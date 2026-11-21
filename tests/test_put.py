"""Red-green: `put <item> in <container>`.

`take <loot>` picks things up; `drop <item>` puts them on the floor;
`put <item> in <container>` stores an item inside a container the player is
standing next to. This is the complement to `open`/`take` for containers.

These expect a `put` verb that does not exist yet, so they fail now (RED).
"""

import pytest

from src.mud.content import Entity, Player, Room
from src.mud.engine.core import Engine


async def _setup():
    engine = Engine()
    _player = Player("Ada", "A brave adventurer.")
    room = Room("Market", "A busy marketplace.")
    engine.player = _player
    engine._player_location = room
    return engine, _player, room


@pytest.mark.asyncio
async def test_put_into_open_chest():
    """`put <item> in <chest>` moves the item into the container."""
    engine, player, room = await _setup()
    lantern = Entity("Brass Lantern", "A brass lantern.", light_source=True)
    chest = Entity("Chest", "A sturdy oak chest.")
    chest.add_content(lantern)
    room.add_content(chest)
    player.add_content(lantern)

    await engine.process_command("put lantern in chest")

    assert lantern in chest.contents
    assert lantern not in player.contents
    assert lantern not in room.contents


@pytest.mark.asyncio
async def test_put_missing_item():
    """`put` refuses when the item is not carried."""
    engine, _player, room = await _setup()
    chest = Entity("Chest", "A sturdy oak chest.")
    room.add_content(chest)

    response = await engine.process_command("put lantern in chest")

    assert "carrying" in response.lower()


@pytest.mark.asyncio
async def test_put_missing_container():
    """`put` refuses when there is no container to put it in."""
    engine, player, _room = await _setup()
    lantern = Entity("Brass Lantern", "A brass lantern.", light_source=True)
    player.add_content(lantern)

    response = await engine.process_command("put lantern in chest")

    assert "chest" in response.lower()


@pytest.mark.asyncio
async def test_put_into_locked_chest():
    """A locked container refuses the item."""
    engine, player, room = await _setup()
    lantern = Entity("Brass Lantern", "A brass lantern.", light_source=True)
    chest = Entity("Chest", "A sturdy oak chest.", locked=True, required_key="key_gold_1")
    room.add_content(chest)
    player.add_content(lantern)

    response = await engine.process_command("put lantern in chest")

    assert "lock" in response.lower()
    assert lantern in player.contents
