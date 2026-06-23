#!/usr/bin/env python3
"""
SQLite-based persistent cache for search results.
Survives process restarts, 1-hour TTL by default.
"""
import json
import os
import sqlite3
import time

_CACHE_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', 'search_cache.db')
_DEFAULT_TTL = 3600  # 1 hour


def _get_conn():
    os.makedirs(os.path.dirname(_CACHE_DB), exist_ok=True)
    conn = sqlite3.connect(_CACHE_DB, timeout=5)
    conn.execute('''CREATE TABLE IF NOT EXISTS search_cache (
        query TEXT PRIMARY KEY,
        result TEXT NOT NULL,
        created_at REAL NOT NULL
    )''')
    conn.commit()
    return conn


def cache_get(query: str, ttl: int = _DEFAULT_TTL) -> dict | None:
    """Return cached result if fresh enough, else None."""
    try:
        conn = _get_conn()
        row = conn.execute(
            'SELECT result, created_at FROM search_cache WHERE query = ?',
            (query,),
        ).fetchone()
        conn.close()
        if row and (time.time() - row[1]) < ttl:
            return json.loads(row[0])
    except Exception:
        pass
    return None


def cache_set(query: str, result: dict):
    """Store result in cache."""
    try:
        conn = _get_conn()
        conn.execute(
            'INSERT OR REPLACE INTO search_cache (query, result, created_at) VALUES (?, ?, ?)',
            (query, json.dumps(result, ensure_ascii=False), time.time()),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def cache_clear():
    """Clear all cached entries."""
    try:
        conn = _get_conn()
        conn.execute('DELETE FROM search_cache')
        conn.commit()
        conn.close()
    except Exception:
        pass
