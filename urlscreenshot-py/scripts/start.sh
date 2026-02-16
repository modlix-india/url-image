#!/bin/bash
set -e

cd "$(dirname "$0")/.."

# Find a compatible Python (3.11-3.13; greenlet/playwright don't support 3.14 yet)
PYTHON=""
for candidate in python3.11 python3.12 python3.13; do
    if command -v "$candidate" &>/dev/null; then
        PYTHON="$candidate"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "Error: Python 3.11-3.13 required (greenlet doesn't support 3.14 yet)"
    echo "Install with: brew install python@3.13"
    exit 1
fi

echo "Using $PYTHON ($($PYTHON --version))"

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    "$PYTHON" -m venv venv
fi

source venv/bin/activate

echo "Installing dependencies..."
pip install -q -r requirements.txt

echo "Installing Playwright WebKit..."
playwright install webkit

echo "Starting URL Screenshot service on port 6201..."
uvicorn app.main:app --host 0.0.0.0 --port 6201 --workers 1 --log-level info &
echo $! > .pid
echo "Started with PID $(cat .pid)"
