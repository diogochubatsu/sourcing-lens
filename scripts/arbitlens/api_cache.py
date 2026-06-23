#!/usr/bin/env python3
"""
API Cache — In-memory cache for search results and taxonomy.

Usage:
  from api_cache import cache_get, cache_set, cache_clear
"""
import time
import json
import os

_cache = {}
_CACHE_TTL = 3600  # 1 hour

def cache_get(key):
    """Get value from cache if not expired."""
    if key in _cache:
        entry = _cache[key]
        if time.time() - entry['ts'] < _CACHE_TTL:
            return entry['data']
        del _cache[key]
    return None

def cache_set(key, data):
    """Set value in cache."""
    _cache[key] = {'data': data, 'ts': time.time()}

def cache_clear():
    """Clear all cache."""
    _cache.clear()

def cache_stats():
    """Return cache statistics."""
    return {
        'size': len(_cache),
        'entries': list(_cache.keys())[:10],
    }
