# IoT MUD

An experimental project bridging digital text-based gameplay with physical hardware via IoT.

## Getting Started

This project uses `uv` for dependency management and environment running.

### Prerequisites
- [Python 3.12+](https://www.python.org/downloads/)
- [uv](https://astral.sh/uv/)

### Setup

#### Option A: Using `uv` (Recommended)
```bash
# Install dependencies
uv sync --all-extras
```

#### Option B: Manual Virtual Environment
If you are not using `uv`, please follow these steps:
```bash
# Create and activate venv
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install websockets pydantic pydantic-settings PyYAML ruff pytest pytest-asyncio
```

### Running the Project

#### Example: Run the demo
```bash
./run_demo.sh
```

### Protocol versions

The client negotiates the wire protocol from the server's `hello` handshake.
Protocol `2` is the merged club protocol (typed events, structured room state);
a server advertising `[1]` keeps the legacy path, so the same client works
against both the old server and the common one.

To try the v2 path without the common server:

```bash
# Terminal 1
python scripts/mock_v2_server.py

# Terminal 2
python scripts/client.py --uri ws://localhost:8770
```

### Testing

#### Run all tests
```bash
# Using uv
uv run pytest

# Manual venv
pytest
```

---
*Maintained by OpenCode Agents*
