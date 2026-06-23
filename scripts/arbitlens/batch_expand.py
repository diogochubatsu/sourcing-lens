#!/usr/bin/env python3
"""
batch_expand.py — Expand product catalog by scraping all categories.

Scrapes 19 categories × 5 platforms = 95 potential sources per query.
Stores results in PostgreSQL with CLIP embeddings.

Usage:
  python3 batch_expand.py --category audio --limit 20
  python3 batch_expand.py --all --limit 10
  python3 batch_expand.py --high-priority --limit 15
"""
import json
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from categories_v2 import CATEGORIES
from search import search_all
from cache import cache_get, cache_set

def get_pg_conn():
    import psycopg2
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL not set")
    return psycopg2.connect(database_url)

def store_product(conn, product, category):
    """Store a product in PostgreSQL with enriched Rakumart data."""
    cursor = conn.cursor()
    
    # Extract enriched fields - can be in raw_data or directly in product
    raw = product.get('raw_data', {}) or {}
    
    title_cn = raw.get('title_cn', '') or product.get('title_cn', '')
    top_cat_id = raw.get('top_category_id') or product.get('top_category_id')
    second_cat_id = raw.get('second_category_id') or product.get('second_category_id')
    third_cat_id = raw.get('third_category_id') or product.get('third_category_id')
    trade_score = raw.get('trade_score') or product.get('trade_score')
    seller_identities = raw.get('seller_identities', []) or product.get('seller_identities', [])
    shop_address = raw.get('shop_address', '') or product.get('shop_address', '')
    create_date = raw.get('create_date') or product.get('create_date')
    modify_date = raw.get('modify_date') or product.get('modify_date')
    
    try:
        cursor.execute("""
            INSERT INTO arbitlens_products (
                platform, platform_id, title, price, currency, url,
                image_urls, supplier_name, moq, sales_30d, review_count,
                review_avg, category, is_active,
                title_cn, top_category_id, second_category_id, third_category_id,
                trade_score, seller_identities, shop_address,
                product_create_date, product_modify_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, true,
                      %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (platform, platform_id) DO UPDATE SET
                title = EXCLUDED.title,
                price = EXCLUDED.price,
                image_urls = EXCLUDED.image_urls,
                supplier_name = EXCLUDED.supplier_name,
                moq = EXCLUDED.moq,
                sales_30d = EXCLUDED.sales_30d,
                review_count = EXCLUDED.review_count,
                review_avg = EXCLUDED.review_avg,
                category = EXCLUDED.category,
                title_cn = EXCLUDED.title_cn,
                top_category_id = EXCLUDED.top_category_id,
                second_category_id = EXCLUDED.second_category_id,
                third_category_id = EXCLUDED.third_category_id,
                trade_score = EXCLUDED.trade_score,
                seller_identities = EXCLUDED.seller_identities,
                shop_address = EXCLUDED.shop_address,
                product_create_date = EXCLUDED.product_create_date,
                product_modify_date = EXCLUDED.product_modify_date,
                last_updated = NOW()
        """, (
            product.get('platform', ''),
            product.get('product_url', '').split('/')[-1] or product.get('product_name', '')[:50],
            (product.get('product_name', '') or '')[:500],
            product.get('price_brl'),
            'BRL',
            product.get('product_url', ''),
            [product.get('image_url', '')] if product.get('image_url') else [],
            product.get('seller_name', ''),
            product.get('moq'),
            product.get('monthly_sales'),
            product.get('review_count'),
            product.get('rating'),
            category,
            title_cn,
            top_cat_id,
            second_cat_id,
            third_cat_id,
            trade_score,
            seller_identities,
            shop_address,
            create_date,
            modify_date,
        ))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return False

def scrape_category(cat_slug, limit_per_query=10):
    """Scrape all queries for a category."""
    cat = CATEGORIES[cat_slug]
    all_products = []
    seen_urls = set()

    for lang, queries in cat["queries"].items():
        for query in queries:
            # Check cache first
            cached = cache_get(f"expand:{cat_slug}:{query}")
            if cached:
                products = cached.get('products', [])
            else:
                try:
                    result = search_all(query, max_results_per_platform=limit_per_query)
                    products = result.get('products', [])
                    cache_set(f"expand:{cat_slug}:{query}", {'products': products})
                except Exception as e:
                    print(f"    Error scraping '{query}': {e}", file=sys.stderr)
                    continue

            for p in products:
                url = p.get('product_url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    p['category'] = cat_slug
                    all_products.append(p)

    return all_products

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Expand product catalog')
    parser.add_argument('--category', help='Scrape specific category')
    parser.add_argument('--all', action='store_true', help='Scrape all categories')
    parser.add_argument('--high-priority', action='store_true', help='Scrape high-priority categories only')
    parser.add_argument('--limit', type=int, default=10, help='Results per query')
    parser.add_argument('--dry-run', action='store_true', help='Scrape but don\'t store')
    args = parser.parse_args()

    print(f"ArbitLens Batch Expand — {datetime.utcnow().isoformat()}")

    # Determine categories to scrape
    if args.category:
        if args.category in CATEGORIES:
            cat_slugs = [args.category]
        else:
            print(f"Category '{args.category}' not found")
            sys.exit(1)
    elif args.all:
        cat_slugs = list(CATEGORIES.keys())
    elif args.high_priority:
        cat_slugs = [s for s, c in CATEGORIES.items() if c.get('priority') == 'high']
    else:
        cat_slugs = list(CATEGORIES.keys())

    print(f"\nCategories to scrape: {len(cat_slugs)}")
    for s in cat_slugs:
        print(f"  - {CATEGORIES[s]['name']} ({s})")

    # Connect to database
    conn = get_pg_conn() if not args.dry_run else None

    total_products = 0
    total_stored = 0
    start = time.time()

    for cat_slug in cat_slugs:
        cat = CATEGORIES[cat_slug]
        print(f"\n{'='*60}")
        print(f"  {cat['name']} ({cat_slug})")
        print(f"{'='*60}")

        cat_start = time.time()
        products = scrape_category(cat_slug, args.limit)
        cat_time = time.time() - cat_start

        print(f"\n  Found: {len(products)} unique products in {cat_time:.1f}s")
        total_products += len(products)

        if not args.dry_run and conn:
            stored = 0
            for p in products:
                if store_product(conn, p, cat_slug):
                    stored += 1
            total_stored += stored
            print(f"  Stored: {stored}/{len(products)}")
        else:
            print(f"  Dry run: {len(products)} products not stored")

    elapsed = time.time() - start

    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(f"  Categories scraped: {len(cat_slugs)}")
    print(f"  Total products found: {total_products}")
    print(f"  Total products stored: {total_stored}")
    print(f"  Time: {elapsed:.0f}s")

    if conn:
        conn.close()

    # Verify final state
    if not args.dry_run:
        conn = get_pg_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM arbitlens_products WHERE is_active = true")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT category) FROM arbitlens_products WHERE is_active = true AND category IS NOT NULL")
        cats = cursor.fetchone()[0]
        conn.close()
        print(f"\n  Database: {total} products across {cats} categories")

if __name__ == '__main__':
    main()
