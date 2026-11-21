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

### Protocol v2 server

The v2 server speaks the merged club protocol (structured room state, typed
events, non-fatal errors) over the same engine and world as the v1 server:

```bash
python -m src.mud.net.v2_server   # ws://localhost:8765
```

`./run_demo.sh` is unchanged and still starts the v1 server. Run one or the
other, not both, because they share the port.

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
