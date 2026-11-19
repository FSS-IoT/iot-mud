import asyncio
from typing import Any, Callable, Dict, List, Optional
from src.mud.content import Entity, Room, Player

class Engine:
    def __init__(self):
        """The authoritative brain of the MUD."""
        self._rooms: Dict[str, Room] = {}
        self._player_location: Optional[Room] = None
        self.player: Optional[Entity] = None
        self._subscribers: Dict[str, List[Callable]] = {}
        # Multiplayer registry. Each named player owns its location; the engine
        # is authoritative over who is where. Legacy single-player accessors
        # (self.player / self._player_location) remain for backward compatibility.
        self._players: Dict[str, Player] = {}

    @property
    def rooms(self) -> Dict[str, Room]:
        """Public access to the world map."""
        return self._rooms

    @property
    def current_location(self) -> Optional[Room]:
        """Public access to the player's current room."""
        return self._player_location

    def get_room(self, name: str) -> Optional[Room]:
        """Return the room with this name, or None."""
        return self._rooms.get(name)

    # --- Player registry -----------------------------------------------------

    def register_player(self, name: str) -> Player:
        """Register a new player and spawn them at the loaded start room.

        Raises ValueError if a player of that name already exists.
        """
        if name in self._players:
            raise ValueError(f"Player '{name}' is already registered")
        player = Player(name)
        self._players[name] = player
        player.location = self._player_location
        if player.location is not None:
            player.location.add_content(player)
        return player

    def get_player(self, name: str) -> Optional[Player]:
        """Return the player with this name, or None."""
        return self._players.get(name)

    def remove_player(self, name: str) -> bool:
        """Remove a player from the registry and clear their location.

        Returns True if a player was removed, False if no such player existed.
        """
        player = self._players.pop(name, None)
        if player is None:
            return False
        if player.location is not None:
            player.location.remove_content(player)
        player.location = None
        return True

    def players_in_room(self, room: Room) -> List[Player]:
        """Return the players currently in this room."""
        if room is None:
            return []
        return [p for p in self._players.values() if p.location is room]

    async def subscribe(self, event_type: str, callback: Callable) -> None:
        """Registers a listener for semantic events."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    async def emit(self, event_type: str, data: Any) -> None:
        """Broadcasts internal game changes."""
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event_type, data)
                    else:
                        callback(event_type, data)
                except Exception as e:
                    print(f"Event Error ({event_type}): {e}")

    async def process_command(self, command_text: str, player_name: Optional[str] = None) -> str:
        """Translates player input into state mutation or narrative.

        `player_name` is the registered name whose perspective to render from.
        It is optional so existing single-player callers keep working unchanged;
        only the multiplayer path (which knows each socket's registered name)
        passes one. When given, room descriptions also list other occupants.
        """
        raw_text = command_text.strip()
        text = raw_text.lower()
        if not text:
            return "Silence falls over you."

        parts = text.split(maxsplit=1)
        verb = parts[0]
        arg = parts[1] if len(parts) > 1 else None
        
        # --- 1. SYSTEM COMMANDS (Highest Priority) ---
        if verb == "exit":
            response = "Goodbye!"
            matched = True
            await self.emit("player_quit", {"reason": "user_requested"})
            return response

        # --- 2. ALIAS RESOLUTION & NORMALIZATION ---
        aliases = {
            "get": "take", "pick": "take", "grab": "take",
            "l": "look", 
            "n": "go north", "north": "go north",
            "s": "go south", "south": "go south", 
            "e": "go east",  "east": "go east",
            "w": "go west",  "west": "go west", 
            "u": "go up",    "up": "go up", 
            "d": "go down",  "down": "go down",
            "exits": "show_exits"
        }
        
        input_str = f"{verb} {arg}".strip().lower() if arg else verb.lower()
        resolved_verb = verb
        resolved_arg = arg

        if input_str in aliases:
            alias_target = aliases[input_str]
            if " " in alias_target:
                v_part, a_part = alias_target.split(" ", 1)
                resolved_verb = v_part
                resolved_arg = a_part
            else:
                resolved_verb = alias_target
        elif verb.lower() in aliases:
            resolved_verb = aliases[verb.lower()]

        response = ""
        matched = False

        # --- 3. GAMEPLAY COMMAND LOGIC ---
        
        # VIEWING THE WORLD
        if resolved_verb == "look":
            target_player = self.get_player(player_name) if player_name else None
            room = target_player.location if target_player is not None else self._player_location
            if room:
                response = room.description
                occupants = [p for p in self._players.values()
                             if p.location is room and p.name != player_name]
                if occupants:
                    listed = ", ".join(p.name for p in sorted(occupants))
                    response += f"\n\nOthers in the room: {listed}."
                matched = True
            else:
                response = "You feel lost in a void."
                matched = True

        elif resolved_verb == "show_exits":
            if not self._player_location:
                response = "You have no context for exits here."
                matched = True
            else:
                exits_dict = self._player_location.exits
                if not exits_dict:
                    response = "There are no exits here."
                else:
                    names = [d.capitalize() for d in exits_dict.keys()]
                    response = f"Available exits: {', '.join(names)}."
                matched = True

        # MOVEMENT
        elif resolved_verb == "go" and resolved_arg:
            if not self._player_location:
                response = "You have no presence here to move."
                matched = True
            else:
                destination = self._player_location.exits.get(resolved_arg.strip())
                if isinstance(destination, Room):
                    old_name = self._player_location.name
                    self._player_location = destination
                    
                    # Auto-describe destination + exits list
                    exits_list = [e.capitalize() for e in destination.exits.keys()]
                    exit_str = f"Exits lead {', '.join(exits_list)}."
                    
                    response = (
                        f"You travel towards {destination.name}.\n"
                        f"(Prose: You leave the {old_name}).\n\n"
                        f"{destination.description}\n"
                        f"{exit_str}"
                    )
                    matched = True
                    # Signal World Change
                    await self.emit("room_change", {"from": old_name, "to": destination.name, "desc": destination.description})
                else:
                    response = f"You cannot go {resolved_arg}."
                    matched = True

        # INTERACTION (Items)
        elif resolved_verb == "take" and resolved_arg:
            if not self.player:
                response = "You do not exist!"
                matched = True
            elif not self._player_location:
                response = "There is nowhere here to take anything from."
                matched = True
            else:
                target_item = next((i for i in self._player_location.contents if i.name.lower() == resolved_arg.lower()), None)
                if target_item:
                    self._player_location.remove_content(target_item)
                    self.player.add_content(target_item)
                    response = f"You picked up the {target_item.name}."
                    matched = True
                    # Emit Item Taken Event
                    await self.emit("item_taken", {"item_name": target_item.name.lower(), "owner": "player"})
                else:
                    response = f"There is no {resolved_arg} here."
                    matched = True

        elif resolved_verb == "drop" and resolved_arg:
            if not self.player:
                response = "You do not exist!"
                matched = True
            elif not self._player_location:
                response = "There is nowhere here to drop anything."
                matched = True
            else:
                target_item = next((i for i in self.player.contents if i.name.lower() == resolved_arg.lower()), None)
                if target_item:
                    self.player.remove_content(target_item)
                    self._player_location.add_content(target_item)
                    response = f"You dropped the {target_item.name}."
                    matched = True
                    # Emit Item Dropped Event
                    await self.emit("item_dropped", {"item_name": target_item.name.lower(), "location": self._player_location.name})
                else:
                    response = f"You aren't carrying any {resolved_arg}."
                    matched = True

        # SOCIAL / UTILITY
        elif resolved_verb == "say" and resolved_arg:
            # Echo the player's own words with their original casing.
            spoken = raw_text.split(maxsplit=1)[1]
            response = f'You say, "{spoken}".'
            matched = True
        elif resolved_verb == "hello":
            response = "The world listens..."
            matched = True

        # --- 4. FALLBACK PATH ---
        if not matched:
            response = "[FALLBACK]"

        await self.emit("command_processed", {"raw": command_text, "clean": text, "reply": response})
        return response

    async def run(self) -> None:
        pass

if __name__ == "__main__":
    # Simple bootstrap for inspection
    eng = Engine()
    r1 = Room("Start", "A beginning.")
    r2 = Room("End", "The end.")
    r1.exits["next"] = r2
    eng._player_location = r1
    print(asyncio.run(eng.process_command("go next")))
    print(asyncio.run(eng.process_command("look")))
