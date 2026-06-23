#!/usr/bin/env python3
"""Proxy pool manager for Decodo residential proxies.

Rotates through sticky endpoint ports (configurable via env vars).
Each proxy gives a fresh residential IP with session stickiness.
"""

import os
import random
from typing import Optional

# Decodo credentials from environment (no fallback — must be set in .env)
DECODO_USER = os.getenv('DECODO_USER') or os.getenv('DECODO_PROXY_USER')
DECODO_PASS = os.getenv('DECODO_PASS') or os.getenv('DECODO_PROXY_PASS')
DECODO_HOST = os.getenv('DECODO_HOST') or os.getenv('DECODO_PROXY_HOST') or 'gate.decodo.com'
PORT_START = int(os.getenv('DECODO_PORT_START', '10001'))
PORT_END = int(os.getenv('DECODO_PORT_END', '10010'))

# Validate — fail fast with clear message if missing
if not DECODO_USER or not DECODO_PASS:
    raise RuntimeError(
        "Decodo credentials not set. Set DECODO_USER / DECODO_PASS environment variables "
        "(or copy .env.example to .env and fill in your credentials)."
    )
DECODO_PORTS = list(range(PORT_START, PORT_END + 1))

# Round-robin index (shared across process)
_current = 0

def get_proxy_url() -> str:
    """Return next proxy URL in rotation: http://user:pass@host:port."""
    global _current
    port = DECODO_PORTS[_current]
    _current = (_current + 1) % len(DECODO_PORTS)
    return f"http://{DECODO_USER}:{DECODO_PASS}@{DECODO_HOST}:{port}"

def random_proxy_url() -> str:
    """Return a random proxy URL from the pool."""
    port = random.choice(DECODO_PORTS)
    return f"http://{DECODO_USER}:{DECODO_PASS}@{DECODO_HOST}:{port}"

def add_proxy_arg(options, proxy_url: Optional[str] = None):
    """Inject --proxy-server arg into ChromeOptions."""
    if proxy_url is None:
        proxy_url = get_proxy_url()
    options.add_argument(f'--proxy-server={proxy_url}')
    return proxy_url
