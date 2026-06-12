#!/usr/bin/env bash
# Wrapper to start ArbitLens without locale warnings
export LC_ALL=C.UTF-8
exec /mnt/ssd/arbitlens/.venv/bin/python3 -m uvicorn app.backend.main:app --host 0.0.0.0 --port 8080 2>/dev/null
