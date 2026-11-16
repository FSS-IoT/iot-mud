#!/bin/bash

# Ensure virtualenv is active
source .venv/bin/activate

echo "Starting MUD Server in background..."
python -m src.mud.net.server &
SERVER_PID=$!

# Allow server to bind
sleep 1

echo "Launching Interactive Client..."
echo "-----------------------------"
python scripts/client.py
echo "-----------------------------"

# Clean up server on exit
kill $SERVER_PID 2>/dev/null || true
echo -e "\nDemo exited safely."
