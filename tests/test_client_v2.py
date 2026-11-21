"""Contract tests for the protocol v2 client path.

The interactive client auto-negotiates from the `hello` handshake: a server
advertising protocol `[2]` gets the v2 message set, while `[1]` keeps the
legacy path. These tests use a fake socket that speaks v2 and unit-test the v2
renderer, so the client can be verified before the common v2 server exists.
"""

import asyncio
import builtins
import io
import json
import queue as _queue
from contextlib import redirect_stdout

import websockets

from scripts.client import client_handler, render_message_v2
from tests.client_test_helpers import wait_for_output

# ---------------------------------------------------------------------------
# Message builders
# ---------------------------------------------------------------------------

def _msg(type_, data, msg_id=None, event_id="e1", seq=1):
    message = {
        "v": 2,
        "type": type_,
        "event_id": event_id,
        "seq": seq,
        "ts": "2026-11-21T00:00:00Z",
        "data": data,
    }
    if msg_id is not None:
        message["id"] = msg_id
    return message


def _room(room_id="gate", name="Village Gate",
          description="A heavy stone gate stands tall.",
          objects=None, players=None, dark=False):
    return {
        "id": room_id,
        "name": name,
        "description": description,
        "dark": dark,
        "exits": [{"direction": "north", "to": "market", "locked": False}],
        "objects": objects or [],
        "players": players or [],
        "npcs": [],
    }


def _room_state(room, msg_id=None):
    return _msg(
        "room.state",
        {"room": room, "text": f"{room['name']}\n{room['description']}"},
        msg_id,
    )


def _session_ok(name="Ada"):
    return _msg(
        "session.ok",
        {
            "player": {"name": name},
            "world": {"name": "Starting Village", "epoch": "e1"},
            "mode": "guest",
            "text": f"Welcome, {name}.",
        },
        "join",
    )


def _object_event(type_, msg_id=None, text="You take the Gold Coin."):
    return _msg(
        type_,
        {
            "object": {"id": "gold_coin", "kind": "gold_coin",
                       "name": "Gold Coin"},
            "by": "Ada",
            "self": True,
            "text": text,
        },
        msg_id,
    )


def _inventory(msg_id=None, items=None, text="You are carrying: Gold Coin."):
    return _msg("player.inventory", {"items": items or [], "text": text}, msg_id)


def _said(text='You say, "hello".', msg_id=None):
    return _msg("player.said", {"from": "Ada", "text": text, "self": True}, msg_id)


def _error(msg_id=None, message="Hmm, I don't understand that. "
                                "Type `help` for a list of commands."):
    return _msg("error", {"code": "unknown_command", "message": message}, msg_id)


# ---------------------------------------------------------------------------
# Fake v2 server
# ---------------------------------------------------------------------------

class FakeV2Socket:
    """A v2-speaking websocket stand-in with scripted replies."""

    def __init__(self, join_error=None):
        self._outgoing = asyncio.Queue()
        self._join_error = join_error

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def recv(self):
        return await self._outgoing.get()

    async def send(self, payload):
        msg = json.loads(payload)
        for reply in self._route(msg):
            await self._outgoing.put(json.dumps(reply))

    def _route(self, msg):
        handler = getattr(self, f"_on_{msg.get('type')}", None)
        return handler(msg) if handler else []

    def _on_join(self, msg):
        if self._join_error is not None:
            return [_msg("error", {
                "code": "name_taken",
                "message": self._join_error,
            }, "join")]
        name = msg.get("data", {}).get("name", "Ada")
        return [_session_ok(name), _room_state(_room())]

    def _on_input(self, msg):
        text = msg["data"]["text"].strip().lower()
        idx = msg["id"]

        if text in ("look", "l"):
            return [_room_state(_room(), idx)]
        if text == "go north":
            market = _room(
                "market", "Marketplace", "Lively vendors cry out their wares.",
                objects=[{"id": "gold_coin", "kind": "gold_coin",
                          "name": "Gold Coin", "portable": True}],
            )
            return [_room_state(market, idx)]
        if text.startswith("take gold"):
            return [
                _object_event("object.taken", idx),
                _inventory(text="You are carrying: Gold Coin."),
            ]
        if text.startswith("drop gold"):
            return [
                _object_event("object.dropped", idx,
                              text="You dropped the Gold Coin."),
                _inventory(items=[], text="You are not carrying anything."),
            ]
        if text.startswith("say "):
            spoken = text.split(maxsplit=1)[1]
            return [_said(text=f'You say, "{spoken}".', msg_id=idx)]
        if text in ("inventory", "i"):
            return [_inventory(idx, [{"id": "gold_coin", "name": "Gold Coin"}])]
        return [_error(idx)]


async def run_client_v2(script, join_error=None,
                        first_needle="Village Gate"):
    """Run client_handler against the fake v2 socket and capture stdout."""
    ws = FakeV2Socket(join_error=join_error)
    await ws._outgoing.put(json.dumps(_msg(
        "hello",
        {
            "server": "fake",
            "protocol": [2],
            "world": {"name": "Starting Village", "epoch": "e1"},
            "auth_required": False,
            "motd": "Welcome to the IoT MUD!",
        },
        event_id="h",
        seq=1,
    )))

    lines = _queue.Queue()
    for line in script:
        lines.put(line)

    out = io.StringIO()
    waited = [False]

    def scripted_input(prompt=""):
        if not waited[0]:
            wait_for_output(out, first_needle)
            waited[0] = True
        return lines.get()

    original_input = builtins.input
    original_connect = websockets.connect
    builtins.input = scripted_input
    websockets.connect = lambda uri: ws
    try:
        with redirect_stdout(out):
            await asyncio.wait_for(client_handler("ws://fake", "Ada"),
                                   timeout=5)
    finally:
        websockets.connect = original_connect
        builtins.input = original_input
    return out.getvalue()


def _run(script, **kwargs):
    return asyncio.run(run_client_v2(script, **kwargs))


# ---------------------------------------------------------------------------
# End-to-end client behaviour over v2
# ---------------------------------------------------------------------------

def test_v2_login_shows_room_immediately():
    """Joining a v2 server renders the starting room before the first command."""
    output = _run(["exit"])
    assert output.count("A heavy stone gate stands tall.") == 1


def test_v2_look_renders_room_once():
    """The join view plus one `look` yields exactly two descriptions."""
    output = _run(["look", "exit"])
    assert output.count("A heavy stone gate stands tall.") == 2


def test_v2_join_error_is_rendered():
    """A rejected join is shown before the first prompt, not held as a reply."""
    output = _run(["exit"], join_error="That name is already taken.",
                  first_needle="already taken")
    assert "already taken" in output


def test_v2_say_renders_own_message():
    """The actor's `player.said` copy is rendered, not dropped."""
    output = _run(["say hello", "exit"])
    assert 'You say, "hello".' in output


def test_v2_error_keeps_client_running():
    """A command error is printed and the next command still works."""
    output = _run(["dance", "look", "exit"])
    assert "I don't understand" in output
    assert "A heavy stone gate stands tall." in output


def test_v2_take_renders_event_and_inventory():
    """`take` renders the direct object event and the inventory follow-up."""
    output = _run(["take gold_coin", "exit"])
    assert "You take the Gold Coin." in output
    assert "You are carrying: Gold Coin." in output


# ---------------------------------------------------------------------------
# Renderer units
# ---------------------------------------------------------------------------

def test_render_v2_room_state_structured():
    room = _room(
        objects=[{"id": "sign", "kind": "sign", "name": "Village Sign"}],
        players=[{"name": "Ben"}],
    )
    out = render_message_v2(_room_state(room), "Ada")

    assert "Village Gate" in out
    assert "A heavy stone gate stands tall." in out
    assert "Here you see: Village Sign." in out
    assert "Others in the room: Ben." in out


def test_render_v2_dark_room_hides_contents():
    room = _room(name="Mysterious Forest", description="Trees loom high above.",
                 dark=True)
    out = render_message_v2(_room_state(room), "Ada")

    assert "dark" in out.lower()
    assert "Here you see:" not in out
    assert "Others in the room:" not in out


def test_render_v2_object_unlocked():
    msg = _msg("object.unlocked", {
        "object": {"id": "chest", "kind": "chest", "name": "Chest"},
        "by": "Ada",
        "self": True,
        "text": "You unlock the Chest.",
    }, 1)
    assert "unlock" in render_message_v2(msg, "Ada").lower()


def test_render_v2_player_said():
    out = render_message_v2(_said(), "Ada")
    assert 'You say, "hello".' in out


def test_render_v2_unknown_event_is_ignored():
    assert render_message_v2({"v": 2, "type": "mystery", "data": {}}, "Ada") == ""
