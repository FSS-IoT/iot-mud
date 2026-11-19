import asyncio
import json
import logging
import websockets
from typing import Any, Callable, Dict, List
from src.mud.engine.core import Engine

# Setup logging
logging.basicConfig(level=logging.ERROR) # Set to ERROR to ensure NO INFO cluttering stdout
logger = logging.getLogger(__name__)

class MudServer:
    def __init__(self, engine: Engine, host: str = "localhost", port: int = 8765):
        """Initializes the MUD server."""
        self.engine = engine
        self.host = host
        self.port = port
        self._stop_event = asyncio.Event()
        self._server = None

    async def handler(self, websocket) -> None:
        """Handles the connection lifecycle and command routing."""
        try:
            # 1. The Handshake (Task-002 Requirement)
            handshake = {
                "v": 1,
                "type": "hello",
                "event_id": f"init-{int(asyncio.get_event_loop().time())}",
                "seq": 1,
                "ts": "2026-11-14T00:00:00Z",
                "data": {
                    "server": "iot-mud-dev",
                    "protocol": [1],
                    "auth_required": False,
                    "motd": "Welcome to the IoT MUD!"
                }
            }
            await websocket.send(json.dumps(handshake))

            # 2. Communication Loop
            while not self._stop_event.is_set():
                try:
                    raw_message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(raw_message)

                    if data.get("type") == "input":
                        result_text = await self.engine.process_command(data["data"]["text"])
                        
                        response = {
                            "v": 1,
                            "type": "command_reply",
                            "event_id": f"resp-{int(asyncio.get_event_loop().time()*1000)}",
                            "seq": data.get("id", 0) if isinstance(data.get("id"), int) else 0,
                            "data": {"text": result_text}
                        }
                        await websocket.send(json.dumps(response))
                
                except asyncio.TimeoutError:
                    continue
                except websockets.exceptions.ConnectionClosed:
                    break
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    break
        except websockets.exceptions.ConnectionClosedOK:
            pass
        except Exception as e:
            logger.error(f"Error in handler loop: {e}")
        finally:
            await websocket.close()

    async def run(self) -> None:
        """Starts the WebSocket server."""
        self._server = await websockets.serve(self.handler, self.host, self.port)
        await self._stop_event.wait()
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    def stop(self) -> None:
        """Triggers an orderly shutdown."""
        self._stop_event.set()

if __name__ == "__main__":
    import sys
    try:
        from src.mud.engine.core import Engine
        from src.mud.world.loader import load_demo_village
        
        engine_instance = Engine()
        async def main():
            await load_demo_village(engine_instance)
            server_instance = MudServer(engine_instance)
            await server_instance.run()
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down.")
    except Exception as e:
        print(f"Failed to start server: {e}")
