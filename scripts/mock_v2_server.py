"""A tiny protocol-v2 mock server for trying the interactive client.

This is **not** the real server. It exists so the v2 client path can be run
end-to-end before the common `iot-mud-server` is ready:

    python scripts/mock_v2_server.py
    python scripts/client.py --uri ws://localhost:8770

It speaks the v2 handshake, join, room state, object/inventory events, chat,
errors, and the small command set the client knows. State is per connection and
deliberately minimal; the real server remains authoritative.
"""

import argparse
import asyncio
import json
from datetime import UTC, datetime

import websockets

PORT = 8770


def _ts() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


class Session:
    """Per-connection scripted world state."""

    def __init__(self, name: str = "Traveler"):
        self.name = name
        self.room = "gate"
        self.inventory: list[dict] = []
        self.seq = 0

    def envelope(self, type_: str, data: dict, msg_id=None) -> dict:
        self.seq += 1
        message = {
            "v": 2,
            "type": type_,
            "event_id": f"{type_}-{self.seq}",
            "seq": self.seq,
            "ts": _ts(),
            "data": data,
        }
        if msg_id is not None:
            message["id"] = msg_id
        return message

    def room_payload(self) -> dict:
        if self.room == "market":
            return {
                "id": "market",
                "name": "Marketplace",
                "description": "Lively vendors cry out their wares. "
                               "Exits lead South, West, and North.",
                "dark": False,
                "exits": [
                    {"direction": "south", "to": "gate", "locked": False},
                    {"direction": "west", "to": "shop", "locked": False},
                    {"direction": "north", "to": "forest", "locked": False},
                ],
                "objects": [
                    {"id": "gold_coin", "kind": "gold_coin",
                     "name": "Gold Coin", "portable": True},
                ],
                "players": [],
                "npcs": [],
            }
        return {
            "id": "gate",
            "name": "Village Gate",
            "description": "A heavy stone gate stands tall. "
                           "To the north is the Marketplace.",
            "dark": False,
            "exits": [{"direction": "north", "to": "market", "locked": False}],
            "objects": [
                {"id": "sign", "kind": "sign", "name": "Village Sign",
                 "portable": True, "readable": True},
            ],
            "players": [],
            "npcs": [],
        }

    def room_state(self, msg_id=None) -> dict:
        room = self.room_payload()
        return self.envelope("room.state", {
            "room": room,
            "text": f"{room['name']}\n{room['description']}",
        }, msg_id)

    def inventory_event(self, msg_id=None) -> dict:
        if self.inventory:
            text = "You are carrying: " + ", ".join(
                item["name"] for item in self.inventory) + "."
        else:
            text = "You are not carrying anything."
        return self.envelope("player.inventory", {
            "items": self.inventory,
            "text": text,
        }, msg_id)

    def error(self, msg_id, message: str) -> dict:
        return self.envelope("error", {
            "code": "unknown_command",
            "message": message,
        }, msg_id)


async def handler(websocket) -> None:
    session = Session()
    await websocket.send(json.dumps(session.envelope("hello", {
        "server": "iot-mud-mock",
        "protocol": [2],
        "world": {"name": "Starting Village", "epoch": "mock-1"},
        "auth_required": False,
        "motd": "Welcome to the IoT MUD!",
    })))

    try:
        async for raw in websocket:
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send(json.dumps(session.envelope(
                    "error",
                    {"code": "malformed_message",
                     "message": "That message was not valid JSON."},
                )))
                continue

            kind = msg.get("type")
            msg_id = msg.get("id")
            data = msg.get("data") or {}

            if kind == "join":
                session.name = data.get("name") or session.name
                await websocket.send(json.dumps(session.envelope("session.ok", {
                    "player": {"name": session.name},
                    "world": {"name": "Starting Village", "epoch": "mock-1"},
                    "mode": "guest",
                    "text": f"Welcome, {session.name}.",
                }, msg_id)))
                await websocket.send(json.dumps(session.room_state()))
                continue

            if kind == "quit":
                break

            if kind != "input":
                await websocket.send(json.dumps(session.envelope(
                    "error",
                    {"code": "unknown_message",
                     "message": f"Unknown message type: {kind!r}."},
                    msg_id,
                )))
                continue

            text = str(data.get("text", "")).strip()
            command = text.lower()

            if command in ("look", "l"):
                await websocket.send(json.dumps(session.room_state(msg_id)))
            elif command in ("go north", "n"):
                session.room = "market"
                await websocket.send(json.dumps(session.room_state(msg_id)))
            elif command in ("go south", "s"):
                session.room = "gate"
                await websocket.send(json.dumps(session.room_state(msg_id)))
            elif command in ("inventory", "i", "inv"):
                await websocket.send(json.dumps(
                    session.inventory_event(msg_id)))
            elif command.startswith(("take gold", "get gold")):
                coin = {"id": "gold_coin", "kind": "gold_coin",
                        "name": "Gold Coin"}
                session.inventory.append({"id": "gold_coin",
                                          "name": "Gold Coin"})
                await websocket.send(json.dumps(session.envelope(
                    "object.taken",
                    {"object": coin, "by": session.name, "self": True,
                     "text": "You take the Gold Coin."},
                    msg_id,
                )))
                await websocket.send(json.dumps(session.inventory_event()))
            elif command.startswith("drop gold"):
                session.inventory = [
                    item for item in session.inventory
                    if item["id"] != "gold_coin"
                ]
                coin = {"id": "gold_coin", "kind": "gold_coin",
                        "name": "Gold Coin"}
                await websocket.send(json.dumps(session.envelope(
                    "object.dropped",
                    {"object": coin, "by": session.name, "self": True,
                     "text": "You dropped the Gold Coin."},
                    msg_id,
                )))
                await websocket.send(json.dumps(session.inventory_event()))
            elif command.startswith("say "):
                spoken = text.split(maxsplit=1)[1]
                await websocket.send(json.dumps(session.envelope(
                    "player.said",
                    {"from": session.name, "text": f'You say, "{spoken}".',
                     "self": True},
                    msg_id,
                )))
            elif command in ("help", "h"):
                await websocket.send(json.dumps(session.envelope(
                    "notice",
                    {"text": "Commands: look, go <direction>, take <item>, "
                             "drop <item>, inventory, say <text>, exit.",
                     "level": "info"},
                    msg_id,
                )))
            elif command in ("exits",):
                room = session.room_payload()
                directions = ", ".join(
                    exit_["direction"].capitalize()
                    for exit_ in room["exits"])
                await websocket.send(json.dumps(session.envelope(
                    "notice",
                    {"text": f"Available exits: {directions}.",
                     "level": "info"},
                    msg_id,
                )))
            elif command.startswith(("examine ", "look at ")):
                target = text.split(maxsplit=2)[-1]
                await websocket.send(json.dumps(session.envelope(
                    "notice",
                    {"text": f"You see nothing special about {target}.",
                     "level": "info"},
                    msg_id,
                )))
            elif command in ("exit", "quit"):
                break
            else:
                await websocket.send(json.dumps(session.error(
                    msg_id,
                    "Hmm, I don't understand that. Type `help` for a list "
                    "of commands.",
                )))
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        try:
            await websocket.close()
        except websockets.exceptions.ConnectionClosed:
            pass


async def main(port: int = PORT) -> None:
    async with websockets.serve(handler, "localhost", port):
        print(f"Mock protocol-v2 server on ws://localhost:{port}")
        print("Run: python scripts/client.py --uri "
              f"ws://localhost:{port}")
        await asyncio.Future()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Protocol-v2 mock server for the interactive client")
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()
    try:
        asyncio.run(main(args.port))
    except KeyboardInterrupt:
        print("\nShutting down.")
