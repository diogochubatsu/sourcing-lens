#!/usr/bin/env python3
"""Basic tests for the search cache module."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cache import cache_get, cache_set, cache_clear

def test_cache_set_and_get():
    cache_clear()
    cache_set("test query", {"products": [{"name": "test"}], "total": 1})
    result = cache_get("test query")
    assert result is not None, "Cache should return stored result"
    assert result["total"] == 1, "Cache should return correct data"
    print("✓ cache_set/get works")

def test_cache_miss():
    cache_clear()
    result = cache_get("nonexistent query xyz")
    assert result is None, "Cache miss should return None"
    print("✓ cache miss works")

def test_cache_expiry():
    cache_clear()
    cache_set("expire test", {"data": 1})
    # TTL of 0 should always miss
    result = cache_get("expire test", ttl=0)
    assert result is None, "Expired cache should return None"
    print("✓ cache expiry works")

def test_cache_clear():
    cache_set("clear test", {"data": 1})
    cache_clear()
    result = cache_get("clear test")
    assert result is None, "Cleared cache should return None"
    print("✓ cache clear works")

if __name__ == "__main__":
    test_cache_set_and_get()
    test_cache_miss()
    test_cache_expiry()
    test_cache_clear()
    print("\nAll tests passed!")
