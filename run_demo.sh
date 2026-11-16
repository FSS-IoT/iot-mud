#!/bin/bash

# Ensure virtualenv is active
if [ ! -d .venv ]; then
    echo "No .venv found. Run 'uv sync --all-extras' first." >&2
    exit 1
fi
source .venv/bin/activate

echo "Starting MUD Server in background..."
python -m src.mud.net.server &
SERVER_PID=$!

# Stop the server on any exit path, including Ctrl-C on the client.
# Without this the server outlives the demo and the port stays bound.
cleanup() {
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Allow server to bind
sleep 1

echo "Launching Interactive Client..."
echo "-----------------------------"
python scripts/client.py
echo "-----------------------------"

echo -e "\nDemo exited safely."
