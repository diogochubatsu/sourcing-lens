#!/usr/bin/env python3
"""
update_sales_from_json.py — Update sales_30d in ImportaSimples from scraped JSON data.

Reads a JSON file with best sellers data (platform_id → sales) and updates bronze_products.

Usage:
  python3 scripts/update_sales_from_json.py --input data/bestsellers_ml_audio.json
  python3 scripts/update_sales_from_json.py --input data/bestsellers_ml_audio.json --update-db
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

IS_DB = {
    'host': '34.170.210.220',
    'port': 5432,
    'dbname': 'importasimples_products',
    'user': 'importasimples',
    'password': 'R{[{f<VajbC{<kvU',
    'sslmode': 'require'
}


def main():
    parser = argparse.ArgumentParser(description='Update sales from JSON')
    parser.add_argument('--input', required=True, help='JSON file with {platform_id: sales} mapping')
    parser.add_argument('--marketplace', required=True, choices=['amazon_br', 'amazon_usa', 'mercadolivre'])
    parser.add_argument('--update-db', action='store_true')
    args = parser.parse_args()

    # Load scraped data
    with open(args.input) as f:
        data = json.load(f)

    print(f'Loaded {len(data)} products from {args.input}')

    import psycopg2
    conn = psycopg2.connect(**IS_DB)
    cur = conn.cursor()

    updated = 0
    not_found = 0

    for platform_id, sales in data.items():
        if not sales or sales <= 0:
            continue

        # Try with and without prefix
        source_id_1 = f'{args.marketplace}:{platform_id}'
        source_id_2 = platform_id

        cur.execute('''
            UPDATE bronze_products
            SET sales_30d = %s
            WHERE source = 'arbt.ly'
            AND marketplace = %s
            AND (source_id = %s OR source_id = %s)
            AND (sales_30d = 0 OR sales_30d IS NULL OR sales_30d < %s)
        ''', (sales, args.marketplace, source_id_1, source_id_2, sales))

        if cur.rowcount > 0:
            updated += cur.rowcount
        else:
            not_found += 1

    if args.update_db:
        conn.commit()
        print(f'\n✅ Updated {updated} products in ImportaSimples')
        print(f'   Not found: {not_found}')

        # Verify
        cur.execute('''
            SELECT marketplace,
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE sales_30d > 0) as has_sales
            FROM bronze_products WHERE source = 'arbt.ly'
            GROUP BY marketplace ORDER BY marketplace
        ''')
        print(f'\nAfter update:')
        for r in cur.fetchall():
            gap = r[1] - r[2]
            print(f'  {r[0]:<18} {r[2]:>4}/{r[1]:<4} have sales  (gap: {gap})')
    else:
        print(f'\nWould update: {updated}, Not found: {not_found}')
        print('Run with --update-db to apply')

    conn.close()


if __name__ == '__main__':
    main()
