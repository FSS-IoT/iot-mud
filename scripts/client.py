import argparse
import asyncio
import json

import websockets

# ANSI Colors
CLEAR = "\033[0m"
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"


def render_message(message: dict, name: str) -> str:
    """Render an incoming protocol-v1 message as text for the user.

    Synchronous and side-effect free so it can be unit-tested directly. Returns
    "" for messages that need no display (command replies are handled by their own
    matching path in the command loop). This is what turns a server event like a
    join, leave, or room_state into something readable on screen.
    """
    kind = message.get("type", "")
    data = message.get("data", {})

    if kind == "room_state":
        out = f"{GREEN}{data.get('name', '')}{CLEAR}"
        description = data.get("description")
        if description:
            out += "\n" + description
        if data.get("dark"):
            return out + f"{CLEAR}\nIt is too dark to see anything.\n"
        items = data.get("items") or []
        if items:
            out += f"\nHere you see: {', '.join(items)}."
        occupants = data.get("occupants") or []
        visible = [o for o in occupants if o != name]
        if visible:
            out += f"\nOthers in the room: {', '.join(visible)}."
        return out + f"{CLEAR}\n"

    if kind == "player_joined":
        return f"{CYAN}{data.get('name', '')} joined.{CLEAR}\n"

    if kind == "player_left":
        return f"{CYAN}{data.get('name', '')} left.{CLEAR}\n"

    return ""


def render_message_v2(message: dict, name: str) -> str:
    """Render an incoming protocol-v2 message as text for the user.

    v2 carries structured state with `data.text` as presentation only. This
    renderer prefers the structured fields where they matter (the room view) and
    falls back to the server's text for events. It is deliberately synchronous
    and side-effect free, like the v1 renderer.
    """
    kind = message.get("type", "")
    data = message.get("data", {})

    if kind == "room.state":
        room = data.get("room") or {}
        out = f"{GREEN}{room.get('name', '')}{CLEAR}"
        description = room.get("description")
        if description:
            out += "\n" + description
        if room.get("dark"):
            return out + f"{CLEAR}\nIt is too dark to see anything.\n"
        objects = [o.get("name", "") for o in (room.get("objects") or [])
                   if o.get("name")]
        if objects:
            out += f"\nHere you see: {', '.join(objects)}."
        players = [p.get("name", "") for p in (room.get("players") or [])
                   if p.get("name") and p.get("name") != name]
        if players:
            out += f"\nOthers in the room: {', '.join(players)}."
        return out + f"{CLEAR}\n"

    if kind == "session.ok":
        # The client already prints "Logged in as: <name>"; the session event
        # adds no line of its own.
        return ""

    if kind == "notice":
        return f"{GREEN}{data.get('text', '')}{CLEAR}\n"

    if kind == "error":
        return f"{RED}{data.get('message', '')}{CLEAR}\n"

    if kind in ("player.said", "player.emoted", "player.told",
                "room.enter", "room.leave"):
        return f"{CYAN}{data.get('text', '')}{CLEAR}\n"

    if kind in ("object.taken", "object.dropped", "object.opened",
                "object.closed", "object.put", "object.got", "object.read",
                "player.inventory", "exit.locked", "exit.unlocked"):
        return f"{GREEN}{data.get('text', '')}{CLEAR}\n"

    if kind == "shutdown":
        text = data.get("text") or data.get("reason", "Server shutting down.")
        return f"{YELLOW}{text}{CLEAR}\n"

    return ""


async def client_handler(uri: str, name: str):
    """Connect, negotiate the protocol from `hello`, and run the command loop.

    The handshake advertises the versions the server speaks. `[2]` selects the
    structured v2 message set; anything else keeps the legacy v1 path so the
    client still works against Doc's original server.
    """
    print(f"{BLUE}{BOLD}Connecting to MUD at {uri}...{CLEAR}")

    # Two independent concerns must not share one queue:
    #   * stream events (room_state on join, presence, broadcasts) are rendered
    #     LIVE as they arrive.
    #   * command replies are matched to their request by id and only awaited
    #     inside the command loop.
    # Keeping them separate is what stops the join view being buffered until the
    # first command (which both left login blank and double-rendered the room on
    # the first `look`).
    stream_events = asyncio.Queue()  # rendered live by a background task
    replies = asyncio.Queue()        # awaited by the command loop

    async with websockets.connect(uri) as websocket:
        # 1. Handshake and protocol negotiation.
        handshake = json.loads(await websocket.recv())
        if handshake.get("type") != "hello":
            print(f"{RED}Unexpected handshake: {handshake}{CLEAR}")
            return

        supported = handshake.get("data", {}).get("protocol", [1])
        protocol = 2 if isinstance(supported, list) and 2 in supported else 1
        render = render_message_v2 if protocol == 2 else render_message

        async def stream_dispatcher():
            """Render stream events as they arrive, without waiting for a reply."""
            while True:
                msg = await stream_events.get()
                rendered = render(msg, name)
                if rendered:
                    print(rendered)

        motd = handshake.get("data", {}).get("motd", "Welcome to the MUD!")
        print(f"\n{CYAN}{BOLD}--- {motd} ---{CLEAR}\n")
        print(f"{YELLOW}Logged in as: {name}{CLEAR}\n")

        # 2. Announce ourselves so the server registers us as a player. Without
        #    this, look won't show occupants and no broadcasts reach this socket.
        if protocol == 2:
            join = {"v": 2, "type": "join", "id": "join",
                    "data": {"name": name}}
        else:
            join = {"v": 1, "type": "join", "id": 1,
                    "data": {"name": name}}
        await websocket.send(json.dumps(join))

        # Continuously read from the socket, splitting events into stream vs reply.
        async def reader():
            while True:
                raw = await websocket.recv()
                msg = json.loads(raw)
                if protocol == 2:
                    # Direct replies carry the client's request id; broadcasts
                    # and follow-up state pushes do not. Anything answering the
                    # join (`session.ok` or a join error) is session setup, not
                    # a command reply, so it stays on the stream path.
                    if msg.get("id") == "join":
                        stream_events.put_nowait(msg)
                    elif "id" in msg:
                        replies.put_nowait(msg)
                    else:
                        stream_events.put_nowait(msg)
                elif msg.get("type") == "command_reply":
                    replies.put_nowait(msg)
                else:
                    stream_events.put_nowait(msg)

        reader_task = asyncio.create_task(reader())
        stream_task = asyncio.create_task(stream_dispatcher())

        # 3. Command loop. Read user input without blocking the socket reader,
        #    then await only this command's matching reply.
        sequence = 1
        try:
            while True:
                raw_input = await asyncio.to_thread(input, f"{BOLD}{name}{CLEAR} > ")
                user_input = raw_input.strip()

                if user_input.lower() in ["exit", "quit"]:
                    print("Goodbye!")
                    break
                if not user_input:
                    continue

                payload = {
                    "v": 2 if protocol == 2 else 1,
                    "type": "input",
                    "id": sequence,
                    "data": {"text": user_input},
                }
                await websocket.send(json.dumps(payload))
                sequence += 1

                msg = await replies.get()
                if protocol == 2:
                    rendered = render_message_v2(msg, name)
                    if rendered:
                        print(rendered)
                    else:
                        text = msg.get("data", {}).get("text", "")
                        if text:
                            print(f"{GREEN}{text}{CLEAR}\n")
                else:
                    text = msg.get("data", {}).get("text", "")
                    print(f"{GREEN}{text}{CLEAR}\n")
        finally:
            reader_task.cancel()
            stream_task.cancel()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interactive IoT MUD Client")
    parser.add_argument("--uri", default="ws://localhost:8765", help="WebSocket URI (default: ws://localhost:8765)")
    args = parser.parse_args()

    username = input("Enter your character name: ").strip()
    if not username:
        username = "Traveler"

    asyncio.run(client_handler(args.uri, username))
