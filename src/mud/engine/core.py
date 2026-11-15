import asyncio
from typing import Callable, Dict, List, Any
import sys

# ANSI Colors
COLOR_SYSTEM = "\033[94m"  # Blue
COLOR_MUD = "\033[1;32m"    # Bold Green
COLOR_SERVER = "\033[1;35m" # Bold Magenta
COLOR_ERROR = "\033[1;31m"  # Bold Red
COLOR_RESET = "\033[0m"

class Engine:
    def __init__(self):
        # World State
        self._rooms = {
            "hall": {"name": "Hall", "desc": "A dim, echoing hall with flagstones underfoot.", "exits": {"north": "kitchen"}},
            "kitchen": {"name": "Kitchen", "desc": "The air smells of stale spices. It is dimly lit.", "exits": {"south": "hall"}}
        }
        self._player_location = "hall"
        
        # Event System
        self._subscribers: Dict[str, List[Callable]] = {}

    async def subscribe(self, event_type: str, callback: Callable):
        """Registers a callback for a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    async def emit(self, event_type: str, data: Any):
        """Emits an event to all registered subscribers."""
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_type, data)
                else:
                    callback(event_type, data)

    async def process_command(self, command_text: str) -> str:
        """Processes a single input string and returns a response."""
        text = command_text.strip().lower()
        if not text:
            return "You stand in silence."

        parts = text.split(maxsplit=1)
        verb = parts[0]
        arg = parts[1] if len(parts) > 1 else None

        # Command aliases (TASK-007)
        aliases = {"get": "take", "pick": "take", "grab": "take"}
        if verb in aliases:
            verb = aliases[verb]

        response_text = ""
        match_found = False

        # Routing Logic
        if verb == "look":
            current_room = self._rooms[self._player_location]
            response_text = current_room["desc"]
            match_found = True
        elif verb == "go" and arg:
            directions = {op: dest for op, dest in self._rooms[self._player_location]["exits"].items()}
            if arg in directions:
                old_room_name = self._rooms[self._player_location]["name"]
                self._player_location = directions[arg]
                new_room_data = self._rooms[self._player_location]
                response_text = f"You walk to the {new_room_data['name']}. (AI Prose: The air grows colder as you depart from the {old_room_name}.)"
                match_found = True
                await self.emit("room_change", {"from": old_room_name, "to": new_room_data['name'], "new_desc": new_room_data["desc"]})
            else:
                response_text = f"You cannot go {arg}."
        elif verb == "say" and arg:
            response_text = f'You say, "{arg}"'
            match_found = True
        elif verb == "hello":
            response_text = "Greetings, traveler!"

        if not match_found:
            response_text = "[FALLBACK]"

        await self.emit("command_processed", {"text": command_text, "result": response_text})
        return response_text

    async def run(self):
        """Main game loop placeholder."""
        pass