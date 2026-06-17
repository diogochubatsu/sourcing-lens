#!/usr/bin/env python3
"""Data Quality Gate — validates all products against acceptance criteria.
Uses CLIP embedding for image quality (not deprecated image_hash).
Uses category_l1 (not deprecated category column).

Usage:
    python3 scripts/data_quality_gate.py                    # full audit
    python3 scripts/data_quality_gate.py --category Audio   # single category by L1
    python3 scripts/data_quality_gate.py --fix              # deactivate failing products
"""
import argparse
import sys
sys.path.insert(0, '.')
from scripts.db import query, execute

CRITERIA = {
    'image': "image_urls[1] LIKE 'http%' OR image_urls[1] LIKE '/images%'",
    'embedding': 'embedding IS NOT NULL',
    'sales': 'sales_30d IS NOT NULL AND sales_30d > 0',
    'price': 'price IS NOT NULL AND price > 0',
}

def audit(category=None):
    where = "WHERE is_active=true"
    params = []
    if category:
        where += " AND category_l1=%s"
        params.append(category)

    total = query(f"SELECT COUNT(*) as c FROM products {where}", tuple(params))[0]['c']
    if total == 0:
        print(f'No active products found')
        return

    print(f'Total active products: {total}')
    print(f'\n{"Criteria":20s} {"Pass":>6s} {"Fail":>6s} {"%":>6s}')
    print('-' * 40)

    passes = {}
    for name, criterion in CRITERIA.items():
        passed = query(f"SELECT COUNT(*) as c FROM products {where} AND ({criterion})", tuple(params))[0]['c']
        failed = total - passed
        pct = passed / total * 100
        passes[name] = passed
        print(f'{name:20s} {passed:6d} {failed:6d} {pct:5.0f}%')

    all_pass = sum(1 for n in passes if passes[n] == total)
    print(f'\nCriteria fully met: {all_pass}/{len(CRITERIA)}')

    if category:
        print(f'\nCategory "{category}" quality score: {min(passes.values()) / total * 100:.0f}%')

def fix_deactivate():
    """Deactivate products that fail any mandatory criterion."""
    count = execute("""
        UPDATE products SET is_active=false WHERE is_active=true AND (
            (image_urls IS NULL OR array_length(image_urls,1) IS NULL OR image_urls[1] NOT LIKE 'http%')
            OR (price IS NULL OR price <= 0)
        )
    """)
    print(f'Deactivated {count} products failing mandatory criteria')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--category', type=str, help='Audit single category (by category_l1)')
    parser.add_argument('--fix', action='store_true', help='Deactivate failing products')
    args = parser.parse_args()

    if args.fix:
        fix_deactivate()
    else:
        audit(args.category)
