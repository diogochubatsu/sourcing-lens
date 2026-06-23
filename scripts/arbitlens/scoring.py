#!/usr/bin/env python3
"""
Search scoring module — Combines text, visual, price, and sales into ranked results.

Scoring weights:
- Text relevance: 30%
- Visual similarity: 40%
- Price competitiveness: 20%
- Sales velocity: 10%
"""
import os
import sys

def get_pg_conn():
    import psycopg2
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL not set")
    return psycopg2.connect(database_url)


def text_score(query, title, title_cn=''):
    """Calculate text relevance score (0-100)."""
    query_lower = query.lower()
    title_lower = (title or '').lower()
    title_cn_lower = (title_cn or '').lower()
    
    # Exact match
    if query_lower in title_lower or query_lower in title_cn_lower:
        return 100
    
    # Partial match (all words present)
    words = query_lower.split()
    matches = sum(1 for w in words if w in title_lower or w in title_cn_lower)
    if matches == len(words):
        return 90
    elif matches > 0:
        return 60 + (matches / len(words)) * 30
    
    # No match
    return 0


def price_score(price_brl, min_price=0, max_price=1000):
    """Calculate price competitiveness score (0-100)."""
    if not price_brl:
        return 50
    
    # Normalize to 0-1 range (lower price = higher score)
    if max_price > min_price:
        normalized = 1 - (price_brl - min_price) / (max_price - min_price)
    else:
        normalized = 0.5
    
    return max(0, min(100, normalized * 100))


def sales_score(monthly_sales):
    """Calculate sales velocity score (0-100)."""
    if not monthly_sales:
        return 0
    
    # Logarithmic scale
    import math
    if monthly_sales <= 0:
        return 0
    return min(100, math.log10(monthly_sales + 1) * 25)


def composite_score(text=0, visual=0, price=0, sales=0):
    """Calculate weighted composite score."""
    return (
        text * 0.30 +
        visual * 0.40 +
        price * 0.20 +
        sales * 0.10
    )


def rank_results(query, results, visual_scores=None):
    """Rank search results by composite score."""
    if visual_scores is None:
        visual_scores = {}
    
    # Calculate price range for normalization
    prices = [r.get('price_brl') for r in results if r.get('price_brl')]
    min_price = min(prices) if prices else 0
    max_price = max(prices) if prices else 1000
    
    ranked = []
    for r in results:
        pid = r.get('product_url', '')
        t_score = text_score(query, r.get('product_name', ''), r.get('title_cn', ''))
        v_score = visual_scores.get(pid, 0)
        p_score = price_score(r.get('price_brl'), min_price, max_price)
        s_score = sales_score(r.get('monthly_sales'))
        
        composite = composite_score(t_score, v_score, p_score, s_score)
        
        r['text_score'] = t_score
        r['visual_score'] = v_score
        r['price_score'] = p_score
        r['sales_score'] = s_score
        r['composite_score'] = composite
        ranked.append(r)
    
    # Sort by composite score
    ranked.sort(key=lambda x: x['composite_score'], reverse=True)
    return ranked
