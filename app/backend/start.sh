#!/bin/bash
# ArbitLens Backend — Start script
# Usage: ./start.sh [--reload]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
VENV="$PROJECT_ROOT/.venv"

# Activate venv
if [ -f "$VENV/bin/activate" ]; then
    source "$VENV/bin/activate"
fi

cd "$SCRIPT_DIR"

if [ "$1" = "--reload" ]; then
    exec python -m uvicorn main:app --host 0.0.0.0 --port 5000 --reload
else
    exec python main.py
fi
