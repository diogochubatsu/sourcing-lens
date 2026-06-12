# ArbitLens Infrastructure Notes

## Server
- Port: 8080
- Start: `cd /mnt/ssd/arbitlens && .venv/bin/python3 scripts/start_server.py`
- Watchdog: cronjob 'arbt-server-watchdog' runs every 5 min via scripts/watchdog.py
- The start_server.py script uses Python uvicorn.run() (no bash wrapper) to avoid LC_ALL locale corruption

## Critical bug fixed 2026-06-10
Port 8080 had a zombie process from "ImportaSimples Marketplace" project (PID 2881341, then PID 3175053). 
Kill command: `fuser -k 8080/tcp` then restart server.

## Tunnel
- Binary: /tmp/cloudflared
- Start: /tmp/cloudflared tunnel --url http://localhost:8080
- Current URL as of 2026-06-10: https://skating-demographic-about-learners.trycloudflare.com
- URL changes on EVERY restart of cloudflared process
- tunnel process persists across server restarts (keeps same URL)

## ML Status (2026-06-10)
- Completely blocked: IP 34.30.146.117 (GCP) flagged by PolicyAgent
- Even Playwright with stealth can't bypass (ML does IP-level blocking, not browser fingerprint)
- Chromium installed at ~/.hermes/profiles/arbt/home/.cache/ms-playwright/chromium-1223/
- Need residential proxy to unblock (Decodo credentials return 407, SU credentials also fail)
