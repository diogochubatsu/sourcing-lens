#!/usr/bin/env python3
"""
Ingest ArbitlensProduct data into PostgreSQL.

Loads scraped data from JSON files into arbitlens_products table
for visual matching and comparison.

Usage:
  python3 ingest_to_pg.py --all           # Ingest all JSON files
  python3 ingest_to_pg.py --file output/rakumart_br_1688.json
"""
import json
import os
import sys
import glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def get_pg_conn():
    import psycopg2
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL not set")
    return psycopg2.connect(database_url)

def ingest_products(products, category=None):
    """Ingest products into PostgreSQL."""
    conn = get_pg_conn()
    cursor = conn.cursor()
    
    inserted = 0
    for p in products:
        try:
            raw = p.get('raw_data', {}) or {}
            title_cn = raw.get('title_cn', '') or p.get('title_cn', '')
            trade_score = raw.get('trade_score') or p.get('trade_score')
            shop_address = raw.get('shop_address', '') or p.get('shop_address', '')
            seller_identities = raw.get('seller_identities', []) or p.get('seller_identities', [])
            create_date = raw.get('create_date') or p.get('create_date')
            modify_date = raw.get('modify_date') or p.get('modify_date')
            
            platform = p.get('platform', '')
            platform_id = p.get('product_url', '').split('/')[-1].split('?')[0] or p.get('product_name', '')[:50]
            
            cursor.execute("""
                INSERT INTO arbitlens_products (
                    platform, platform_id, title, price, currency, url,
                    image_urls, supplier_name, moq, sales_30d, review_count,
                    review_avg, category, is_active,
                    title_cn, trade_score, shop_address, seller_identities,
                    product_create_date, product_modify_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, true,
                          %s, %s, %s, %s, %s, %s)
                ON CONFLICT (platform, platform_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    price = EXCLUDED.price,
                    image_urls = EXCLUDED.image_urls,
                    supplier_name = EXCLUDED.supplier_name,
                    sales_30d = EXCLUDED.sales_30d,
                    category = EXCLUDED.category,
                    title_cn = EXCLUDED.title_cn,
                    trade_score = EXCLUDED.trade_score,
                    shop_address = EXCLUDED.shop_address,
                    seller_identities = EXCLUDED.seller_identities,
                    last_updated = NOW()
            """, (
                platform, platform_id,
                (p.get('product_name', '') or '')[:500],
                p.get('price_brl'),
                'BRL',
                p.get('product_url', ''),
                [p.get('image_url', '')] if p.get('image_url') else [],
                p.get('seller_name', ''),
                p.get('moq'),
                p.get('monthly_sales'),
                p.get('review_count'),
                p.get('rating'),
                category,
                title_cn,
                trade_score,
                shop_address,
                seller_identities,
                create_date,
                modify_date,
            ))
            inserted += 1
        except Exception as e:
            pass
    
    conn.commit()
    conn.close()
    return inserted

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Ingest products to PostgreSQL')
    parser.add_argument('--all', action='store_true', help='Ingest all JSON files')
    parser.add_argument('--file', help='Specific JSON file to ingest')
    args = parser.parse_args()
    
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    
    if args.file:
        files = [args.file]
    elif args.all:
        files = glob.glob(os.path.join(output_dir, '*.json'))
    else:
        print("Usage: python3 ingest_to_pg.py --all | --file <path>")
        return
    
    total = 0
    for f in files:
        with open(f) as fh:
            products = json.load(fh)
        count = ingest_products(products)
        total += count
        print(f"  {os.path.basename(f)}: {count} products")
    
    print(f"\nTotal ingested: {total}")

if __name__ == '__main__':
    main()
