"""Simple in-memory TTL cache for FastAPI endpoints."""
import time
import json
import hashlib
from functools import wraps
from typing import Any, Callable

_cache: dict = {}


def cached(ttl_seconds: int = 60):
    """Decorator: cache function result for N seconds.

    Cache key is built from function name + args (hashable).
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key
            try:
                key_data = (func.__name__, args, sorted(kwargs.items()))
                key = hashlib.md5(str(key_data).encode()).hexdigest()
            except Exception:
                # If can't hash, just call
                return func(*args, **kwargs)

            now = time.time()
            if key in _cache:
                value, expires_at = _cache[key]
                if now < expires_at:
                    return value
                # Expired
                del _cache[key]

            value = func(*args, **kwargs)
            _cache[key] = (value, now + ttl_seconds)
            return value
        return wrapper
    return decorator


def clear_cache():
    """Clear all cache entries."""
    _cache.clear()


def cache_stats() -> dict:
    """Return cache statistics."""
    now = time.time()
    alive = sum(1 for _, (_, exp) in _cache.items() if now < exp)
    return {
        "total_entries": len(_cache),
        "alive_entries": alive,
        "expired_entries": len(_cache) - alive,
    }
