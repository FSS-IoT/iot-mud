"""Contract tests for broadcast of player join/leave (issue #23).

Issue #22 gave the engine a registry of named players. Issue #21 gave clients a
handshake + command round-trip. This ticket bridges them: when a client joins as
a named player and later leaves, every *other* player still in that room must be
notified with `player_joined` / `player_left` events.

To register from the network layer a client must announce itself, so this ticket
also introduces the client `join` message. Movement-driven presence is #24 and is
deliberately NOT asserted here — both players spawn at the start room by default,
so they are co-located deterministically without any movement commands.

Red-green: the first two tests encode join/leave broadcast behavior that did not
exist before this ticket, so they failed on the parent commit; the third is a
regression guard ensuring registration does not break the existing command
round-trip.
"""

import asyncio
import json

import pytest
import websockets

from src.mud.engine.core import Engine
from src.mud.net.server import MudServer
from src.mud.world.loader import load_demo_village


@pytest.fixture
async def running_server():
    """Start a server backed by the starting-village world, stop it after."""
    engine = Engine()
    await load_demo_village(engine)  # start room = "Village Gate"
    server = MudServer(engine, port=8767)
    task = asyncio.create_task(server.run())

    await asyncio.sleep(0.3)

    yield server, task

    server.stop()
    try:
        await asyncio.wait_for(task, timeout=2.0)
    except TimeoutError:
        task.cancel()
    finally:
        if not task.done():
            task.cancel()


async def _read(websocket):
    """Read one message with a guard so a missing event fails fast, not by hanging."""
    raw = await asyncio.wait_for(websocket.recv(), timeout=3.0)
    return json.loads(raw)


async def _connect_and_handshake(uri):
    """Open a socket and consume the server's `hello` handshake."""
    websocket = await websockets.connect(uri)
    await _read(websocket)  # discard hello
    return websocket


async def _join(websocket, name):
    """Send a client `join` message announcing this player's name."""
    payload = {"v": 1, "type": "join", "id": 1, "data": {"name": name}}
    await websocket.send(json.dumps(payload))


@pytest.mark.asyncio
async def test_joining_player_is_notified_of_new_occupant(running_server):
    """When Ben joins a room that Ada already occupies, Ada gets `player_joined`."""
    server, _ = running_server
    uri = f"ws://localhost:{server.port}"

    ada = await _connect_and_handshake(uri)
    await _join(ada, "Ada")  # Ada alone at Village Gate -> no broadcast yet

    ben = await _connect_and_handshake(uri)
    await _join(ben, "Ben")  # Ben joins the same room

    event = await _read(ada)  # Ada should receive notification about Ben

    assert event["type"] == "player_joined"
    assert event["data"]["name"] == "Ben"


@pytest.mark.asyncio
async def test_leaving_player_is_notified_of_departure(running_server):
    """When Ben disconnects, Ada still in the room gets `player_left`."""
    server, _ = running_server
    uri = f"ws://localhost:{server.port}"

    ada = await _connect_and_handshake(uri)
    await _join(ada, "Ada")

    ben = await _connect_and_handshake(uri)
    await _join(ben, "Ben")

    # Consume Ada's player_joined for Ben first, then trigger Ben's disconnect.
    joined = await _read(ada)
    assert joined["type"] == "player_joined"
    await ben.close()

    event = await _read(ada)  # Ada should receive notification that Ben left

    assert event["type"] == "player_left"
    assert event["data"]["name"] == "Ben"


@pytest.mark.asyncio
async def test_commands_still_work_after_registration(running_server):
    """Registration must not break the existing command round-trip."""
    server, _ = running_server
    uri = f"ws://localhost:{server.port}"

    ada = await _connect_and_handshake(uri)
    await _join(ada, "Ada")

    payload = {"v": 1, "type": "input", "id": 5, "data": {"text": "look"}}
    await ada.send(json.dumps(payload))
    reply = await _read(ada)

    assert reply["type"] == "command_reply"
    assert reply["seq"] == payload["id"]
    assert isinstance(reply["data"]["text"], str) and reply["data"]["text"]
