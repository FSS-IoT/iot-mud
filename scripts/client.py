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
    
    try:
        async with websockets.connect(uri) as websocket:
            # 1. Handle Handshake
            handshake_raw = await websocket.recv()
            handshake = json.loads(handshake_raw)
            
            if handshake.get("type") != "hello":
                print(f"{RED}Unexpected handshake: {handshake}{CLEAR}")
                return

            motd = handshake.get("data", {}).get("motd", "Welcome to the MUD!")
            print(f"\n{CYAN}{BOLD}--- {motd} ---{CLEAR}\n")
            print(f"{YELLOW}Logged in as: {name}{CLEAR}\n")

            sequence = 1

            while True:
                user_input = input(f"{BOLD}{name}{CLEAR} > ").strip()
                
                if user_input.lower() in ["exit", "quit"]:
                    print("Goodbye!")
                    break
                
                if not user_input:
                    continue

                # Create payload
                payload = {
                    "v": 1,
                    "type": "input",
                    "id": sequence,
                    "data": {"text": user_input}
                }
                
                await websocket.send(json.dumps(payload))
                sequence += 1

                # Wait for reply
                resp_raw = await websocket.recv()
                resp = json.loads(resp_raw)

                if resp.get("type") == "command_reply":
                    text = resp.get("data", {}).get("text", "")
                    print(f"{GREEN}{text}{CLEAR}\n")
                else:
                    print(f"{RED}[SERVER MESSAGE] {resp}{CLEAR}\n")

    except ConnectionRefusedError:
        print(f"{RED}Connection refused. Is the server running?{CLEAR}")
    except Exception as e:
        print(f"{RED}An error occurred: {e}{CLEAR}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interactive IoT MUD Client")
    parser.add_argument("--uri", default="ws://localhost:8765", help="WebSocket URI (default: ws://localhost:8765)")
    args = parser.parse_args()

    username = input("Enter your character name: ").strip()
    if not username:
        username = "Traveler"

    asyncio.run(client_handler(args.uri, username))
