#!/usr/bin/env python3
"""
migrate_to_importasimples.py — Migrate ArbitLens products to ImportaSimples bronze_products.

Source: arbtbr (localhost:5432)
Destination: importasimples_products (34.170.210.220:5432)
Source value: 'arbtlly'
source_id format: {platform}:{platform_id}

Usage:
    python3 scripts/migrate_to_importasimples.py              # Full sync
    python3 scripts/migrate_to_importasimples.py --dry-run    # Preview without writing
    python3 scripts/migrate_to_importasimples.py --limit 10   # Migrate only first 10
    python3 scripts/migrate_to_importasimples.py --verify     # Verify counts after migration
"""

import argparse
import json
import os
import sys
import time
import psycopg2
from decimal import Decimal

# ── Config ────────────────────────────────────────────────────
SOURCE_VALUE = 'arbtlly'
SCRIPT_NAME = 'migrate_to_importasimples.py'
BATCH_SIZE = 100

DEST_CONFIG = {
    'host': '34.170.210.220',
    'port': 5432,
    'dbname': 'importasimples_products',
    'user': 'importasimples',
    'password': 'R{[{f<VajbC{<kvU',
    'sslmode': 'require',
}

# Platform → marketplace mapping
PLATFORM_MAP = {
    'amazon_br': 'amazon_br',
    'amazon_us': 'amazon_usa',
    'ml': 'mercadolivre',
}

# ── UPSERT SQL ────────────────────────────────────────────────
UPSERT_SQL = """
INSERT INTO bronze_products (
    source, source_id, marketplace, title,
    image_url, image_urls, image_count,
    price, currency, price_brl,
    url, product_url,
    category_raw, category_level, category_l1, category_l2, category_l3,
    sales_30d, review_count, review_avg,
    raw_data, script_name
) VALUES (
    %s, %s, %s, %s,
    %s, %s, %s,
    %s, %s, %s,
    %s, %s,
    %s, %s, %s, %s, %s,
    %s, %s, %s,
    %s, %s
)
ON CONFLICT (source, source_id) DO UPDATE SET
    title = EXCLUDED.title,
    image_url = EXCLUDED.image_url,
    image_urls = EXCLUDED.image_urls,
    image_count = EXCLUDED.image_count,
    price = EXCLUDED.price,
    currency = EXCLUDED.currency,
    price_brl = EXCLUDED.price_brl,
    category_raw = EXCLUDED.category_raw,
    category_level = EXCLUDED.category_level,
    category_l1 = EXCLUDED.category_l1,
    category_l2 = EXCLUDED.category_l2,
    category_l3 = EXCLUDED.category_l3,
    sales_30d = EXCLUDED.sales_30d,
    review_count = EXCLUDED.review_count,
    review_avg = EXCLUDED.review_avg,
    raw_data = EXCLUDED.raw_data,
    scraped_at = NOW()
RETURNING (xmax = 0) AS is_new;
"""


def get_source_products(source_cursor, limit=None):
    """Fetch all active products from ArbitLens."""
    query = """
        SELECT id, platform, platform_id, title, price, currency, url,
               image_urls, sales_30d, review_count, review_avg,
               category_l1, category_l2, category_l3,
               image_hash, embedding
        FROM products
        WHERE is_active = TRUE
        ORDER BY platform, category_l1, title
    """
    if limit:
        query += f" LIMIT {int(limit)}"
    source_cursor.execute(query)
    return source_cursor.fetchall()


def build_row(product):
    """Transform an ArbitLens product row into bronze_products values."""
    (pid, platform, platform_id, title, price, currency, url,
     image_urls, sales_30d, review_count, review_avg,
     category_l1, category_l2, category_l3,
     image_hash, embedding) = product

    # Source identity
    source_id = f"{platform}:{platform_id}"
    marketplace = PLATFORM_MAP.get(platform, platform)

    # Images
    imgs = image_urls if image_urls else []
    image_url = imgs[0] if imgs else None
    image_count = len(imgs)

    # Categories
    levels = sum(1 for x in [category_l1, category_l2, category_l3] if x)
    cat_parts = [x for x in [category_l1, category_l2, category_l3] if x]
    category_raw = ' > '.join(cat_parts) if cat_parts else None

    # Price — amazon_us stays in USD, price_brl NULL
    price_brl = None
    if platform != 'amazon_us':
        price_brl = price

    # raw_data — reconstruct with available fields + embedding
    raw_data = {
        'title': title,
        'price': float(price) if price else None,
        'currency': currency,
        'url': url,
        'image_urls': imgs,
        'image_hash': image_hash,
        'category_l1': category_l1,
        'category_l2': category_l2,
        'category_l3': category_l3,
        'sales_30d': sales_30d,
        'review_count': review_count,
        'review_avg': float(review_avg) if review_avg else None,
        'platform': platform,
        'platform_id': platform_id,
        'arbtly_id': pid,
    }

    # Store embedding in raw_data as instructed by ImportaSimples
    if embedding:
        try:
            # embedding is a string like "[-0.015, 0.021, ...]" or a vector
            if isinstance(embedding, str):
                emb_list = json.loads(embedding)
            else:
                emb_list = list(embedding)
            raw_data['image_embedding'] = emb_list
        except (json.JSONDecodeError, TypeError):
            pass  # Skip if embedding can't be parsed

    return (
        SOURCE_VALUE,           # source
        source_id,              # source_id
        marketplace,            # marketplace
        title,                  # title
        image_url,              # image_url
        imgs,                   # image_urls
        image_count,            # image_count
        price,                  # price
        currency,               # currency
        price_brl,              # price_brl
        url,                    # url
        url,                    # product_url
        category_raw,           # category_raw
        levels,                 # category_level
        category_l1,            # category_l1
        category_l2,            # category_l2
        category_l3,            # category_l3
        sales_30d or 0,         # sales_30d
        review_count or 0,      # review_count
        review_avg,             # review_avg
        json.dumps(raw_data),   # raw_data
        SCRIPT_NAME,            # script_name
    )


def run_migration(dry_run=False, limit=None, verify_only=False):
    """Main migration logic."""
    # Connect to source (ArbitLens)
    print("Connecting to source (arbtbr)...")
    src_env = os.environ.copy()
    src_env['PGPASSFILE'] = '/tmp/.pgpass'
    src_conn = psycopg2.connect(
        dbname='arbtbr', user='hermes1688',
        host='localhost', port=5432
    )
    src_cur = src_conn.cursor()

    # Connect to destination (ImportaSimples)
    print("Connecting to destination (importasimples_products)...")
    dst_conn = psycopg2.connect(**DEST_CONFIG)
    dst_cur = dst_conn.cursor()

    # Verify mode — just check counts
    if verify_only:
        src_cur.execute("SELECT COUNT(*) FROM products WHERE is_active = TRUE")
        src_count = src_cur.fetchone()[0]
        dst_cur.execute("SELECT COUNT(*) FROM bronze_products WHERE source = %s", (SOURCE_VALUE,))
        dst_count = dst_cur.fetchone()[0]
        print(f"\n=== Verification ===")
        print(f"  Source (arbtly products): {src_count}")
        print(f"  Destination (arbtlly in bronze): {dst_count}")
        print(f"  Match: {'✅' if src_count == dst_count else '⚠️ MISMATCH'}")
        src_conn.close()
        dst_conn.close()
        return

    # Fetch products
    print(f"Fetching products from source{' (limit=' + str(limit) + ')' if limit else ''}...")
    products = get_source_products(src_cur, limit)
    total = len(products)
    print(f"  Found {total} products to migrate")

    # Stats
    inserted = 0
    updated = 0
    errors = 0
    start_time = time.time()

    # Process in batches
    for batch_start in range(0, total, BATCH_SIZE):
        batch = products[batch_start:batch_start + BATCH_SIZE]
        batch_num = batch_start // BATCH_SIZE + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE

        if dry_run:
            print(f"  [DRY RUN] Batch {batch_num}/{total_batches}: {len(batch)} products")
            continue

        try:
            for product in batch:
                try:
                    values = build_row(product)
                    dst_cur.execute(UPSERT_SQL, values)
                    result = dst_cur.fetchone()
                    if result and result[0]:  # is_new = True
                        inserted += 1
                    else:
                        updated += 1
                except Exception as e:
                    errors += 1
                    platform = product[1]
                    platform_id = product[2]
                    print(f"  ❌ Error on {platform}:{platform_id}: {e}")
                    dst_conn.rollback()
                    continue

            dst_conn.commit()
            elapsed = time.time() - start_time
            progress = batch_start + len(batch)
            pct = (progress / total * 100) if total else 0
            print(f"  Batch {batch_num}/{total_batches}: {progress}/{total} ({pct:.0f}%) "
                  f"[+{inserted} new, ~{updated} updated, {errors} errors] "
                  f"({elapsed:.1f}s)")

        except Exception as e:
            dst_conn.rollback()
            errors += len(batch)
            print(f"  ❌ Batch {batch_num} failed: {e}")

    # Final summary
    elapsed = time.time() - start_time
    print(f"\n{'='*50}")
    print(f"Migration complete in {elapsed:.1f}s")
    print(f"  Total products: {total}")
    print(f"  Inserted (new): {inserted}")
    print(f"  Updated: {updated}")
    print(f"  Errors: {errors}")

    if not dry_run and inserted + updated > 0:
        # Verify
        dst_cur.execute("SELECT COUNT(*) FROM bronze_products WHERE source = %s", (SOURCE_VALUE,))
        dest_count = dst_cur.fetchone()[0]
        print(f"\n  Destination count: {dest_count}")
        print(f"  ✅ Run --verify to cross-check")

    src_conn.close()
    dst_conn.close()


def main():
    parser = argparse.ArgumentParser(description='Migrate ArbitLens → ImportaSimples bronze_products')
    parser.add_argument('--dry-run', action='store_true', help='Preview without writing')
    parser.add_argument('--limit', type=int, default=None, help='Migrate only N products')
    parser.add_argument('--verify', action='store_true', help='Verify counts after migration')
    args = parser.parse_args()

    run_migration(dry_run=args.dry_run, limit=args.limit, verify_only=args.verify)


if __name__ == '__main__':
    main()
