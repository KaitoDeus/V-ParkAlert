#!/bin/bash
echo "=================================================="
echo "       V-ParkAlert Src Server"
echo "=================================================="

SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SRC_DIR")"

# Set PYTHONPATH so that 'src' module can be imported from anywhere
export PYTHONPATH="$ROOT_DIR"

# 1. Create venv if not exists
if [ ! -f "$SRC_DIR/.venv/Scripts/python.exe" ]; then
    echo "[1/4] Creating virtual environment..."
    python -m venv "$SRC_DIR/.venv"
    echo "      Done."
else
    echo "[1/4] Virtual environment exists. Skipping."
fi

PYTHON="$SRC_DIR/.venv/Scripts/python"
PIP="$SRC_DIR/.venv/Scripts/pip"

# 2. Install dependencies
echo "[2/4] Installing dependencies..."
"$PIP" install -r "$SRC_DIR/requirements.txt" -q
echo "      Done."

# 3. Init database
echo "[3/4] Initializing database..."
"$PYTHON" -m src.init_db

# 4. Start server
echo "[4/4] Starting Src server..."
echo "=================================================="
"$PYTHON" -m src.main
