#!/bin/bash

cd "$(dirname "$0")/.."

if [ -f .pid ]; then
    PID=$(cat .pid)
    if kill -0 "$PID" 2>/dev/null; then
        echo "Stopping URL Screenshot service (PID $PID)..."
        kill "$PID"
        rm -f .pid
        echo "Stopped."
    else
        echo "Process $PID not running. Cleaning up PID file."
        rm -f .pid
    fi
else
    echo "No PID file found. Service may not be running."
fi
