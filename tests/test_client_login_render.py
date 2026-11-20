"""Integration tests for the interactive client's message ordering (bug A).

Bug A: on login the server sends a `room_state` describing the starting room, but the
client buffered every incoming message in one queue and only rendered stream events
while draining for the next command's reply. So the join view sat idle until the first
command -- login showed nothing -- and then stacked on top of that command's own reply,
printing the room description twice at once.

The fix renders stream events (join room_state, player_joined/player_left) live via a
background dispatcher, so the command loop only ever waits for its matching reply. These
tests drive client_handler against a fake websocket whose socket mimics real behaviour:
`recv()` blocks while idle and `send()` enqueues scripted replies in the event loop.
"""

import asyncio
import builtins
import io
import json
import queue as _queue
from contextlib import redirect_stdout

import websockets

# Importing the client module up front ensures it is loaded before we monkeypatch
# websockets.connect below (the client resolves `websockets.connect` at call time).
from scripts.client import client_handler  # noqa: F401  (imported for side effect)


class FakeSocket:
    """A websocket stand-in that mimics real blocking I/O and scripted replies.

    `recv()` awaits an internal queue, so it blocks while the server is idle exactly
    like a real socket (unlike a list-based fake that raises on empty). `send()` runs
    in the event loop and enqueues any scripted replies, preserving ordering.
    """

    def __init__(self):
        self._outgoing = asyncio.Queue()

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

    # --- scripted server behaviour -------------------------------------------

    def _route(self, msg):
        handler = getattr(self, f"_on_{msg.get('type')}", None)
        if not handler:
            return []
        return handler(msg)

    def _on_join(self, msg):
        # On join the server describes the starting room (a stream event).
        return [self._room_state(
            "Village Gate", "A heavy stone gate stands tall.", [], [])]

    def _on_input(self, msg):
        text = msg["data"]["text"].strip()
        if text in ("look", "l"):
            return [{
                "v": 1, "type": "command_reply", "event_id": "r", "seq": msg["id"],
                "data": {"text": "A heavy stone gate stands tall."},
            }]
        return []

    @staticmethod
    def _room_state(name, description, items, occupants):
        return {
            "v": 1, "type": "room_state", "event_id": "rs", "seq": 0,
            "data": {"name": name, "description": description,
                     "items": items, "occupants": occupants},
        }


async def run_client(script):
    """Run client_handler with a fake websocket and scripted stdin lines."""
    ws = FakeSocket()

    # Pre-seed the hello handshake that the first recv() must return.
    await ws._outgoing.put(json.dumps({
        "v": 1, "type": "hello", "event_id": "h", "seq": 0,
        "data": {"server": "fake", "protocol": [1], "auth_required": False,
                 "motd": "Welcome to the IoT MUD!"},
    }))

    # Replace input() with a synchronous queue of scripted responses. The client
    # calls it via asyncio.to_thread, so it must be a plain blocking function.
    lines = _queue.Queue()
    for line in script:
        lines.put(line)
    original_input = builtins.input
    builtins.input = lambda prompt="": lines.get()

    original_connect = websockets.connect
    websockets.connect = lambda uri: ws  # resolves to the fake via `async with`
    out = io.StringIO()
    try:
        with redirect_stdout(out):
            await asyncio.wait_for(client_handler("ws://fake", "Ada"), timeout=5)
    finally:
        websockets.connect = original_connect
        builtins.input = original_input
    return out.getvalue()


def _run(script):
    return asyncio.run(run_client(script))


def test_login_shows_room_immediately():
    """Logging in must render the starting room right away, not only after a command.

    This is the discriminating assertion for bug A: with the buffering bug the join
    view sits idle until the first command, so joining and exiting shows nothing. The
    fix renders it live on join.
    """
    output = _run(["exit"])
    assert output.count("A heavy stone gate stands tall.") == 1


def test_look_does_not_double_render():
    """After a live join render, 'look' must add exactly one more description.

    With the buffering bug the first command rendered the buffered join view AND its
    own reply at once (two descriptions on one prompt). The fix renders the join view
    live and the reply separately, so two prompts yield two total occurrences.
    """
    output = _run(["l", "exit"])
    assert output.count("A heavy stone gate stands tall.") == 2
