import asyncio
from typing import Any, Callable, Dict, List, Optional
from src.mud.content import Entity, Room

class Engine:
    def __init__(self):
        """The authoritative brain of the MUD."""
        self._rooms: Dict[str, Room] = {}
        self._player_location: Optional[Room] = None
        self.player: Optional[Entity] = None
        self._subscribers: Dict[str, List[Callable]] = {}

    @property
    def rooms(self) -> Dict[str, Room]:
        """Public access to the world map."""
        return self._rooms

    @property
    def current_location(self) -> Optional[Room]:
        """Public access to the player's current room."""
        return self._player_location

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

    async def process_command(self, command_text: str) -> str:
        """Translates player input into state mutation or narrative."""
        text = command_text.strip().lower()
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
            if self._player_location:
                response = self._player_location.description
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

        # INTERACTION (Items)
        elif resolved_verb == "take" and resolved_arg:
            if not self.player:
                response = "You do not exist!"
            elif not self._player_location:
                response = "There is nowhere here to take anything from."
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
            else:
                target_item = next((i for i in self.player.contents if i.name.lower() == arg.lower()), None)
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
            response = f'"{resolved_arg}" you proclaim.'
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
