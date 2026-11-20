"""Red-green: demo-friction polish found while playtesting after bug 6.

These tests encode behaviors that do not exist yet in the engine, so they fail
now (RED). They are intentionally small and focused on the interactive feel of
the one-player/registered-player demo path:

  * `inventory` / `i` / `inv` list what the player is carrying.
  * `help` / `h` summarize the available verbs.
  * a bare `take` / `drop` (no argument) is greeted with a hint, not "[FALLBACK]".
  * `exam <item>` and other common shorthands resolve to their full verb.
  * an unrecognized command still matches but reads as helpful prose, never the
    raw "[FALLBACK]" sentinel that leaks implementation details to the player.

The engine is exercised directly (no server) so these stay fast and deterministic.
"""

import pytest

from src.mud.content import Entity, Room
from src.mud.engine.core import Engine


def _setup():
    """A room with a coin on the floor and Ada standing in it holding nothing."""
    engine = Engine()
    room = Room("Marketplace", "Lively vendors cry out their wares.")
    coin = Entity("Gold Coin", "A shiny, minted copper coin.", weight=0.01)
    room.add_content(coin)
    engine._rooms["Marketplace"] = room
    engine._player_location = room
    engine.register_player("Ada")
    return engine


# ---------------------------------------------------------------------------
# inventory: i / inv / inventory list what the player carries
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_inventory_empty_reports_nothing():
    """`inventory` with an empty pack reports that plainly."""
    engine = _setup()
    response = await engine.process_command("inventory", "Ada")
    assert "not carrying" in response.lower()


@pytest.mark.asyncio
async def test_inventory_lists_carried_items():
    """`i` lists every item the player is currently holding."""
    engine = _setup()
    player = engine.get_player("Ada")
    torch = Entity("Torch", "A flickering wooden torch.", weight=0.5)
    player.add_content(torch)

    for cmd in ("i", "inv", "inventory"):
        response = await engine.process_command(cmd, "Ada")
        assert "torch" in response.lower()


@pytest.mark.asyncio
async def test_inventory_multiple_items():
    """`inv` lists more than one carried item."""
    engine = _setup()
    player = engine.get_player("Ada")
    player.add_content(Entity("Torch", "A flickering wooden torch.", weight=0.5))
    player.add_content(Entity("Loaf of Bread", "A stale but edible loaf.", weight=0.3))

    response = await engine.process_command("inv", "Ada")
    lowered = response.lower()
    assert "torch" in lowered and "bread" in lowered


# ---------------------------------------------------------------------------
# help: h / help summarize the verbs
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_help_lists_core_verbs():
    """`help` mentions the main verbs a player can try."""
    engine = _setup()
    response = await engine.process_command("help", "Ada")
    lowered = response.lower()
    for verb in ("look", "go", "take", "drop", "examine", "inventory"):
        assert verb in lowered, f"help did not mention {verb!r}"


@pytest.mark.asyncio
async def test_help_short_alias():
    """`h` behaves like `help`."""
    engine = _setup()
    response = await engine.process_command("h", "Ada")
    assert "look" in response.lower()


# ---------------------------------------------------------------------------
# bare take / drop: greet with a hint, not a fallback sentinel
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_bare_take_gets_hint_not_fallback():
    """`take` with no argument is greeted, and never leaks [FALLBACK]."""
    engine = _setup()
    response = await engine.process_command("take", "Ada")
    assert "[FALLBACK]" not in response
    # It must NOT silently succeed (there is nothing to take) nor move state.
    assert coin_exists_in_room(engine)


@pytest.mark.asyncio
async def test_bare_drop_gets_hint_not_fallback():
    """`drop` with no argument is greeted, and never leaks [FALLBACK]."""
    engine = _setup()
    response = await engine.process_command("drop", "Ada")
    assert "[FALLBACK]" not in response


def coin_exists_in_room(engine: Engine) -> bool:
    room = engine._player_location
    return any(c.name == "Gold Coin" for c in (room.contents if room else []))


# ---------------------------------------------------------------------------
# exam shorthand resolves to examine
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_exam_shorthand_resolves():
    """`exam gold coin` (when held) describes the item like `examine` would."""
    engine = _setup()
    player = engine.get_player("Ada")
    coin = next(c for c in engine._player_location.contents if c.name == "Gold Coin")
    player.add_content(coin)

    response = await engine.process_command("exam gold coin", "Ada")
    assert "shiny" in response.lower()  # from the coin description


@pytest.mark.asyncio
async def test_examine_room_item_not_held():
    """`examine gold coin` when it is on the floor (not held) still describes it,
    not 'You see no ... here'."""
    engine = _setup()
    response = await engine.process_command("examine gold coin", "Ada")
    assert "shiny" in response.lower()


# ---------------------------------------------------------------------------
# fallback reads as helpful prose, never the raw sentinel
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_unknown_command_is_helpful_not_sentinel():
    """An unrecognized command matches (no crash) and never prints [FALLBACK]."""
    engine = _setup()
    response = await engine.process_command("kill dragon", "Ada")
    assert "[FALLBACK]" not in response


@pytest.mark.asyncio
async def test_unknown_command_still_matches():
    """The fallback path is treated as matched so nothing double-replies."""
    engine = _setup()
    # Should return without raising; the point is graceful handling.
    response = await engine.process_command("flibbertigibbet", "Ada")
    assert isinstance(response, str) and response


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
