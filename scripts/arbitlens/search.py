#!/usr/bin/env python3
"""
arbitlens Search V2 — scrape all platforms and return flat results.

V2 approach: NO automated matching, NO confidence scores, NO CLIP.
Just scrape + return flat product list sorted by price.
User decides what's the same product.

Usage:
  python3 search.py "microfone lapela"
  python3 search.py "wireless lapel microphone" 10
"""
import json
import os
import sys
import time
import urllib.parse
import concurrent.futures

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrape_rakumart_br import search_rakumart_br
from scrape_dhgate import scrape_dhgate
from scrape_alibaba import scrape_alibaba
from pt_cn_dict import pt_to_cn, build_queries
from phash import phash_int
from cache import cache_get, cache_set
from cn_pt_dict import translate_if_chinese
from price_history import record_search

# Default queries for trending (when no query provided)
DEFAULT_QUERIES = [
    "novidade", "lançamento", "promoção",
    "mais vendido", "bestseller", "top vendas",
    "frete grátis", "atacado", "importado",
]


def scrape_platform(platform, query, max_results=15):
    """Scrape a single platform and return products."""
    try:
        if platform == 'rakumart-1688':
            return search_rakumart_br(query, source='1688')[:max_results]
        elif platform == 'rakumart-taobao':
            return search_rakumart_br(query, source='taobao')[:max_results]
        elif platform == 'rakumart-alibaba':
            return search_rakumart_br(query, source='alibaba')[:max_results]
        elif platform == 'dhgate':
            return scrape_dhgate(query)[:max_results]
        elif platform == 'alibaba':
            return scrape_alibaba(query)[:max_results]
        else:
            return []
    except Exception as e:
        print(f"  Error scraping {platform}: {e}", file=sys.stderr)
        return []


_rate_cache = {}
_FALLBACK = {'BRL': 1.0, 'CNY': 0.78, 'USD': 5.69}


def _fetch_live_rates():
    """Fetch live BRL exchange rates (cached for 1 hour)."""
    import time
    now = time.time()
    if _rate_cache and now - _rate_cache.get('_ts', 0) < 3600:
        return _rate_cache
    try:
        import urllib.request
        req = urllib.request.Request(
            'https://open.er-api.com/v6/latest/BRL',
            headers={'User-Agent': 'arbitlens/1.0'},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        rates = data.get('rates', {})
        inverted = {k: 1.0 / v for k, v in rates.items() if v}
        inverted['_ts'] = now
        _rate_cache.update(inverted)
    except Exception:
        pass
    return _rate_cache


def to_brl(price, curr):
    """Convert price to BRL using live exchange rates."""
    if not price:
        return None
    if curr == 'BRL':
        return round(price, 2)
    rates = _fetch_live_rates()
    rate = rates.get(curr, _FALLBACK.get(curr))
    if rate:
        return round(price * rate, 2)
    return round(price, 2)


def product_to_dict(p):
    """Convert a scraper product to a flat dict for JSON output."""
    name = translate_if_chinese(p.product_name or '')
    
    # Extract enriched fields from raw_data
    raw = p.raw_data or {}
    
    d = {
        'platform': p.source_platform,
        'product_name': name[:120],
        'price_low': p.price_low,
        'price_high': p.price_high,
        'price_currency': p.price_currency,
        'price_brl': to_brl(p.price_low, p.price_currency),
        'image_url': p.image_url,
        'product_url': p.source_url,
        'seller_name': p.seller_name or '',
        'seller_rating': p.seller_rating,
        'monthly_sales': p.monthly_sales,
        'moq': p.moq,
        'review_count': p.review_count,
        'rating': p.rating,
        'image_hash': None,
        # Enriched Rakumart fields
        'title_cn': raw.get('title_cn', ''),
        'trade_score': raw.get('trade_score'),
        'shop_address': raw.get('shop_address', ''),
        'seller_identities': raw.get('seller_identities', []),
        'create_date': raw.get('create_date'),
        'modify_date': raw.get('modify_date'),
        'top_category_id': raw.get('top_category_id'),
        'second_category_id': raw.get('second_category_id'),
        'third_category_id': raw.get('third_category_id'),
    }
    return d


PLATFORM_LABELS = {
    'rakumart-1688': 'Rakumart BR (1688)',
    'rakumart-taobao': 'Rakumart BR (Taobao)',
    'rakumart-alibaba': 'Rakumart BR (Alibaba)',
    'dhgate': 'DHgate',
    'alibaba': 'Alibaba',
}


def search_all(query, max_results_per_platform=50):
    """
    Search all platforms in parallel, return flat results.
    V2: No matching, no confidence, no CLIP.
    Uses persistent SQLite cache (1-hour TTL).
    """
    # Check cache first
    cached = cache_get(query)
    if cached:
        print(f"  Cache hit for: {query}", file=sys.stderr)
        return cached

    platforms = ['rakumart-1688', 'rakumart-taobao', 'rakumart-alibaba', 'dhgate', 'alibaba']

    # Scrape all platforms in parallel
    all_products = []
    platform_counts = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(scrape_platform, p, query, max_results_per_platform): p
            for p in platforms
        }
        for future in concurrent.futures.as_completed(futures):
            platform = futures[future]
            try:
                products = future.result()
                all_products.extend(products)
                platform_counts[platform] = len(products)
                print(f"  {platform}: {len(products)} products", file=sys.stderr)
            except Exception as e:
                print(f"  {platform}: error - {e}", file=sys.stderr)
                platform_counts[platform] = 0

    # Convert to dicts
    flat = [product_to_dict(p) for p in all_products]

    # Sort by BRL price (low to high), None at end
    flat.sort(key=lambda x: (x['price_brl'] is None, x['price_brl'] or 0))

    result = {
        'query': query,
        'products': flat,
        'total_products': len(flat),
        'platforms': {
            PLATFORM_LABELS.get(k, k): v for k, v in platform_counts.items()
        },
        'search_time_ms': 0,
    }

    # Cache the result
    cache_set(query, result)

    # Record for price tracking (async-safe, non-blocking)
    try:
        record_search(query, flat)
    except Exception:
        pass

    return result


if __name__ == '__main__':
    query = sys.argv[1] if len(sys.argv) > 1 else 'wireless lapel microphone'
    max_results = int(sys.argv[2]) if len(sys.argv) > 2 else 50

    start = time.time()
    result = search_all(query, max_results)
    result['search_time_ms'] = int((time.time() - start) * 1000)

    print(json.dumps(result, ensure_ascii=False, indent=2))