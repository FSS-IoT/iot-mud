import asyncio
import websockets
import json
import sys
import argparse

# ANSI Colors for MUD feel
COLOR_SYSTEM = "\033[94m"    # Blue
COLOR_MUD = "\033[1;32m"      # Bold Green
COLOR_SERVER = "\033[1;35m"   # Bold Magenta
COLOR_ERROR = "\033[1;31m"    # Bold Red
COLOR_RESET = "\033[0m"

class MudClient:
    def __init__(self, uri="ws://localhost:8765"):
        self.uri = uri
        self.websocket = None

    async def listen(self):
        """Background task to print incoming messages from the server."""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                msg_type = data.get("type", "unknown")
                content = data.get("data", {}).get("text", "")

                if msg_type == "hello":
                    print(f"\n{COLOR_SERVER}[SERVER] --- {data['data'].get('motd', 'Welcome to the MUD')} ---{COLOR_RESET}")
                    print(f"{COLOR_SYSTEM}Protocol version: {data.get('v')}{COLOR_RESET}\n")
                elif msg_type == "command_reply":
                    print(f"\n{COLOR_MUD}[MUD] {content}{COLOR_RESET}")
                else:
                    # Handle other message types or debug info
                    if content:
                        print(f"\n[{msg_type.upper()}] {content}")
                
                print("> ", end="", flush=True)
        except websockets.exceptions.ConnectionClosed:
            print(f"\n{COLOR_ERROR}[SYSTEM] Connection lost.{COLOR_RESET}")
        except Exception as e:
            print(f"\n{COLOR_ERROR}[ERROR] Listener error: {e}{COLOR_RESET}")

    async def run(self):
        """Connects to the server, handles handshake, and enters input loop."""
        try:
            print(f"{COLOR_SYSTEM}Connecting to {self.uri}...{COLOR_RESET}")
            async with websockets.connect(self.uri) as websocket:
                self.websocket = websocket
                print(f"{COLOR_SYSTEM}Connected.{COLOR_RESET}\n")

                # 1. Handle Handshake
                handshake_raw = await self.websocket.recv()
                handshake = json.loads(handshake_raw)
                if handshake.get("type") == "hello":
                    print(f"{COLOR_SERVER}Connection Verified.{COLOR_RESET}\n")

                # 2. Start the background listener for server responses
                listener_task = asyncio.create_task(self.listen())

                # 3. Main Input Loop
                print("Commands: 'look', 'say <msg>', 'hello', 'quit/exit' to leave.")
                while True:
                    # Using to_thread so input() doesn't block the event loop (listener task)
                    user_input = await asyncio.to_thread(input, "> ")
                    
                    cmd = user_input.strip().lower()
                    if cmd in ["quit", "exit"]:
                        print(f"{COLOR_SYSTEM}Disconnecting...{COLOR_RESET}")
                        break
                    
                    if not cmd:
                        continue

                    # Wrap command in the expected JSON structure
                    payload = {
                        "v": 1,
                        "type": "input",
                        "id": f"cli-{int(asyncio.get_event_loop().time())}",
                        "data": {"text": user_input}
                    }
                    await self.websocket.send(json.dumps(payload))

                # Cleanup
                listener_task.cancel()
        except Exception as e:
            print(f"\n{COLOR_ERROR}[ERROR] Connection failed: {e}{COLOR_RESET}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IoT MUD Test Client")
    parser.add_argument("--uri", type=str, default="ws://localhost:8765", help="Server URI (default: ws://localhost:8765)")
    args = parser.parse_args()

    client = MudClient(uri=args.uri)
    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        pass