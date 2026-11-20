from __future__ import annotations
from typing import Dict, Optional, List

class Entity:
    """Base class for everything in the world: Players, Items, Rooms."""
    def __init__(self, name: str, description: str, weight: float = 0.0,
                 readable: bool = False):
        self.name = name
        self.description = description
        self.weight = weight
        # `readable` marks objects a player can `read` (signs, books, scrolls).
        # Plain items are not; `read <item>` is refused for them.
        self.readable = readable
        self.contents: List[Entity] = []

    def add_content(self, item: Entity) -> bool:
        self.contents.append(item)
        return True

    def remove_content(self, item: Entity) -> bool:
        if item in self.contents:
            self.contents.remove(item)
            return True
        return False

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"

    def __str__(self) -> str:
        return self.name

class Player(Entity):
    """A named player in the world. Owns its current location."""

    def __init__(self, name: str, description: str = "A player."):
        super().__init__(name=name, description=description)
        self.location: Optional[Room] = None


class Room(Entity):
    """A location where entities can reside."""
    def __init__(self, name: str, description: str, exits: Optional[Dict[str, Room]] = None):
        super().__init__(name, description)
        self.exits = exits or {}
