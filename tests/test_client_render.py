"""Contract tests for the client's message renderer (issue #28).

Bug 4 surfaced a related problem in the interactive client: when the server sends
a `room_state` event on join, the client printed the raw JSON as `[SERVER] {...}`
debug output instead of rendering the room. That happened because the rendering
was inline in the async command loop and could not be exercised without a live
socket.

This ticket pulls that logic into a pure `render_message(message, name)` helper
that returns the text to display for any incoming message. It is deliberately
synchronous and side-effect free so it can be tested directly. These tests encode
the desired rendering and fail on the parent commit (no such helper exists yet).
"""

from scripts.client import render_message


def _room_state(name, description, items, occupants):
    """Build a `room_state` message matching what the server sends."""
    return {
        "v": 1,
        "type": "room_state",
        "event_id": "room_state-1",
        "seq": 0,
        "data": {"name": name, "description": description,
                 "items": items, "occupants": occupants},
    }


def test_room_state_renders_name_and_description():
    """A `room_state` renders the room name and its description."""
    msg = _room_state("Village Gate", "A heavy stone gate stands tall.", [], [])
    out = render_message(msg, "Doc")

    assert "Village Gate" in out
    assert "A heavy stone gate stands tall." in out


def test_room_state_renders_items_line():
    """When items are present, a 'Here you see:' line is rendered."""
    msg = _room_state("Marketplace", "Lively vendors cry out their wares.",
                      ["Gold Coin"], [])
    out = render_message(msg, "Doc")

    assert "Here you see: Gold Coin." in out


def test_room_state_renders_occupants_except_self():
    """Occupants are listed excluding the player who received the event."""
    msg = _room_state("Village Gate", "A heavy stone gate stands tall.", [],
                      ["Doc", "Ada"])
    out = render_message(msg, "Doc")

    assert "Others in the room: Ada." in out
    # The receiving player must not be listed as one of the others.
    assert "Others in the room: Doc" not in out


def test_room_state_without_items_or_occupants_has_no_clutter():
    """An empty room renders no 'Here you see' or 'Others' lines."""
    msg = _room_state("Village Gate", "A heavy stone gate stands tall.", [], [])
    out = render_message(msg, "Doc")

    assert "Here you see:" not in out
    assert "Others in the room:" not in out


def test_dark_room_state_renders_darkness_line():
    """A `room_state` flagged `dark` shows the darkness line and nothing else.

    The engine hides items and occupants in a dark room; the renderer must not
    invent a 'Here you see' line for contents the player cannot perceive.
    """
    msg = _room_state("Mysterious Forest", "Trees loom high above.", [], [])
    msg["data"]["dark"] = True
    out = render_message(msg, "Doc")

    assert "dark" in out.lower()
    assert "Here you see:" not in out
    assert "Others in the room:" not in out


def test_player_joined_renders_named_join():
    """A `player_joined` event renders a friendly join notice."""
    msg = {"v": 1, "type": "player_joined", "event_id": "x", "seq": 0,
           "data": {"name": "Ada"}}
    out = render_message(msg, "Doc")

    assert "Ada" in out
    assert "joined" in out


def test_player_left_renders_named_leave():
    """A `player_left` event renders a friendly leave notice."""
    msg = {"v": 1, "type": "player_left", "event_id": "x", "seq": 0,
           "data": {"name": "Ada"}}
    out = render_message(msg, "Doc")

    assert "Ada" in out
    assert "left" in out


def test_unknown_event_is_ignored():
    """An unrecognized message type renders nothing (no raw JSON leak)."""
    msg = {"v": 1, "type": "mystery", "event_id": "x", "seq": 0, "data": {}}
    out = render_message(msg, "Doc")

    assert out == ""
