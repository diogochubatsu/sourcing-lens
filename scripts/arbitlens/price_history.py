#!/usr/bin/env python3
"""
Price history tracker — stores search results over time for trend analysis.
Uses SQLite for persistence.
"""
import json
import os
import sqlite3
import time
from datetime import datetime

_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', 'price_history.db')


def _get_conn():
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(_DB_PATH, timeout=5)
    conn.execute('''CREATE TABLE IF NOT EXISTS price_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT NOT NULL,
        platform TEXT NOT NULL,
        product_id TEXT NOT NULL,
        product_name TEXT,
        price_brl REAL,
        price_original REAL,
        price_currency TEXT,
        monthly_sales INTEGER,
        image_url TEXT,
        product_url TEXT,
        scraped_at TEXT NOT NULL,
        created_at REAL NOT NULL
    )''')
    conn.execute('''CREATE INDEX IF NOT EXISTS idx_snapshots_query ON price_snapshots(query)''')
    conn.execute('''CREATE INDEX IF NOT EXISTS idx_snapshots_product ON price_snapshots(platform, product_id)''')
    conn.execute('''CREATE INDEX IF NOT EXISTS idx_snapshots_time ON price_snapshots(scraped_at)''')
    conn.commit()
    return conn


def record_search(query: str, products: list[dict]):
    """Record search results for price tracking."""
    now = time.time()
    scraped_at = datetime.utcnow().isoformat()
    conn = _get_conn()
    try:
        for p in products:
            conn.execute(
                '''INSERT INTO price_snapshots
                   (query, platform, product_id, product_name, price_brl,
                    price_original, price_currency, monthly_sales,
                    image_url, product_url, scraped_at, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    query,
                    p.get('platform', ''),
                    p.get('product_url', ''),
                    (p.get('product_name', '') or '')[:200],
                    p.get('price_brl'),
                    p.get('price_low'),
                    p.get('price_currency', ''),
                    p.get('monthly_sales'),
                    p.get('image_url', ''),
                    p.get('product_url', ''),
                    scraped_at,
                    now,
                ),
            )
        conn.commit()
    finally:
        conn.close()


def get_price_trends(query: str, days: int = 30) -> list[dict]:
    """Get price trends for a query over time."""
    conn = _get_conn()
    try:
        cutoff = datetime.utcnow().replace(
            hour=0, minute=0, second=0
        ).isoformat()
        rows = conn.execute(
            '''SELECT DATE(scraped_at) as date,
                      platform,
                      AVG(price_brl) as avg_price,
                      MIN(price_brl) as min_price,
                      MAX(price_brl) as max_price,
                      COUNT(*) as product_count
               FROM price_snapshots
               WHERE query = ? AND scraped_at >= datetime('now', ?)
               GROUP BY DATE(scraped_at), platform
               ORDER BY date DESC''',
            (query, f'-{days} days'),
        ).fetchall()
        return [
            {
                'date': r[0],
                'platform': r[1],
                'avg_price': round(r[2], 2) if r[2] else None,
                'min_price': round(r[3], 2) if r[3] else None,
                'max_price': round(r[4], 2) if r[4] else None,
                'product_count': r[5],
            }
            for r in rows
        ]
    finally:
        conn.close()


def get_product_price_history(platform: str, product_id: str) -> list[dict]:
    """Get price history for a specific product."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            '''SELECT DATE(scraped_at) as date,
                      price_brl, price_original, price_currency,
                      monthly_sales
               FROM price_snapshots
               WHERE platform = ? AND product_id = ?
               ORDER BY scraped_at DESC
               LIMIT 90''',
            (platform, product_id),
        ).fetchall()
        return [
            {
                'date': r[0],
                'price_brl': round(r[1], 2) if r[1] else None,
                'price_original': r[2],
                'price_currency': r[3],
                'monthly_sales': r[4],
            }
            for r in rows
        ]
    finally:
        conn.close()


def get_recent_queries(limit: int = 20) -> list[dict]:
    """Get most recently searched queries with stats."""
    conn = _get_conn()
    try:
        rows = conn.execute(
            '''SELECT query,
                      COUNT(DISTINCT platform) as platforms,
                      COUNT(*) as total_snapshots,
                      MAX(scraped_at) as last_searched
               FROM price_snapshots
               GROUP BY query
               ORDER BY last_searched DESC
               LIMIT ?''',
            (limit,),
        ).fetchall()
        return [
            {
                'query': r[0],
                'platforms': r[1],
                'total_snapshots': r[2],
                'last_searched': r[3],
            }
            for r in rows
        ]
    finally:
        conn.close()


if __name__ == '__main__':
    import sys
    import json

    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Usage: price_history.py --trends QUERY [DAYS] | --recent [LIMIT] | --product PLATFORM ID'}))
        sys.exit(1)

    action = sys.argv[1]
    if action == '--trends':
        query = sys.argv[2] if len(sys.argv) > 2 else ''
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 30
        result = {'query': query, 'trends': get_price_trends(query, days)}
    elif action == '--recent':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        result = {'queries': get_recent_queries(limit)}
    elif action == '--product':
        platform = sys.argv[2] if len(sys.argv) > 2 else ''
        product_id = sys.argv[3] if len(sys.argv) > 3 else ''
        result = {'history': get_product_price_history(platform, product_id)}
    else:
        result = {'error': f'Unknown action: {action}'}

    print(json.dumps(result, ensure_ascii=False, indent=2))
