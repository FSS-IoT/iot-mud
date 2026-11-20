import asyncio
import json
import sys
import websockets
import argparse

# ANSI Colors
CLEAR = "\033[0m"
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"


async def client_handler(uri: str, name: str):
    print(f"{BLUE}{BOLD}Connecting to MUD at {uri}...{CLEAR}")

    # Incoming messages (replies and broadcasts) are drained here so a
    # player_joined/player_left event never blocks or misaligns with a reply.
    incoming = asyncio.Queue()

    async with websockets.connect(uri) as websocket:
        # 1. Handshake
        handshake = json.loads(await websocket.recv())
        if handshake.get("type") != "hello":
            print(f"{RED}Unexpected handshake: {handshake}{CLEAR}")
            return

        motd = handshake.get("data", {}).get("motd", "Welcome to the MUD!")
        print(f"\n{CYAN}{BOLD}--- {motd} ---{CLEAR}\n")
        print(f"{YELLOW}Logged in as: {name}{CLEAR}\n")

        # 2. Announce ourselves so the server registers us as a player. Without
        #    this, look won't show occupants and no broadcasts reach this socket.
        await websocket.send(json.dumps({
            "v": 1, "type": "join", "id": 1, "data": {"name": name},
        }))

        # Continuously read from the socket into the queue.
        async def reader():
            while True:
                raw = await websocket.recv()
                incoming.put_nowait(json.loads(raw))

        reader_task = asyncio.create_task(reader())

        # 3. Command loop. Read user input without blocking the socket reader,
        #    then drain the queue until we get this command's matching reply.
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
                    "v": 1, "type": "input", "id": sequence,
                    "data": {"text": user_input},
                }
                await websocket.send(json.dumps(payload))
                sequence += 1

                while True:
                    msg = await incoming.get()
                    if (msg.get("type") == "command_reply"
                            and msg.get("seq") == payload["id"]):
                        text = msg.get("data", {}).get("text", "")
                        print(f"{GREEN}{text}{CLEAR}\n")
                        break
                    kind = msg.get("type", "")
                    other = msg.get("data", {}).get("name", "")
                    if kind == "player_joined":
                        print(f"{CYAN}{other} joined.{CLEAR}\n")
                    elif kind == "player_left":
                        print(f"{CYAN}{other} left.{CLEAR}\n")
                    else:
                        print(f"{YELLOW}[SERVER] {msg}{CLEAR}\n")
        finally:
            reader_task.cancel()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interactive IoT MUD Client")
    parser.add_argument("--uri", default="ws://localhost:8765", help="WebSocket URI (default: ws://localhost:8765)")
    args = parser.parse_args()

    username = input("Enter your character name: ").strip()
    if not username:
        username = "Traveler"

    asyncio.run(client_handler(args.uri, username))
