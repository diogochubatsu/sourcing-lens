#!/usr/bin/env python3
"""Data Quality Gate — validates all products against acceptance criteria.

Usage:
    python3 scripts/data_quality_gate.py                    # full audit
    python3 scripts/data_quality_gate.py --category microfone  # single category
    python3 scripts/data_quality_gate.py --fix               # deactivate failing products
"""
import argparse
import sys
sys.path.insert(0, '.')
from scripts.db import query, execute

CRITERIA = {
    'image': 'image_urls[1] LIKE \'http%\' OR image_urls[1] LIKE \'/images%\'',
    'hash': 'image_hash IS NOT NULL AND image_hash != \'\'',
    'sales': 'sales_30d IS NOT NULL AND sales_30d > 0',
}

def audit(category=None):
    where = "WHERE is_active=true"
    if category:
        where += f" AND category='{category}'"
    
    total = query(f"SELECT COUNT(*) as c FROM products {where}")[0]['c']
    if total == 0:
        print(f'No active products found')
        return
    
    print(f'Total active products: {total}')
    print(f'\n{"Criteria":20s} {"Pass":>6s} {"Fail":>6s} {"%":>6s}')
    print('-' * 40)
    
    passes = {}
    for name, criterion in CRITERIA.items():
        passed = query(f"SELECT COUNT(*) as c FROM products {where} AND ({criterion})")[0]['c']
        failed = total - passed
        pct = passed / total * 100
        passes[name] = passed
        print(f'{name:20s} {passed:6d} {failed:6d} {pct:5.0f}%')
    
    # All three
    all_ok = query(f"""
        SELECT COUNT(*) as c FROM products {where}
        AND ({CRITERIA['image']})
        AND ({CRITERIA['hash']})
        AND ({CRITERIA['sales']})
    """)[0]['c']
    print(f'\nPassing ALL criteria: {all_ok}/{total} ({all_ok/total*100:.0f}%)')
    
    # By category
    print(f'\n{"Category":25s} {"Total":>6s} {"OK":>6s} {"%":>6s}')
    print('-' * 45)
    cats = query(f"""
        SELECT category, COUNT(*) as total,
               SUM(CASE WHEN ({CRITERIA['image']}) AND ({CRITERIA['hash']}) AND ({CRITERIA['sales']}) THEN 1 ELSE 0 END) as ok
        FROM products {where}
        GROUP BY category ORDER BY category
    """)
    for c in cats:
        pct = c['ok'] / c['total'] * 100 if c['total'] > 0 else 0
        print(f'{c["category"]:25s} {c["total"]:6d} {c["ok"]:6d} {pct:5.0f}%')
    
    return passes, total

def fix():
    """Deactivate products failing all criteria."""
    failed = query(f"""
        SELECT id, platform, category, platform_id FROM products WHERE is_active=true
        AND NOT ({CRITERIA['image']})
        AND NOT ({CRITERIA['hash']})
        AND NOT ({CRITERIA['sales']})
    """)
    print(f'\nProducts failing ALL criteria (will deactivate): {len(failed)}')
    for f in failed:
        print(f'  Deactivating ID={f["id"]} {f["platform"]} {f["category"]} {f["platform_id"]}')
        execute("UPDATE products SET is_active=false WHERE id=%s", (f['id'],))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--category', help='Single category to audit')
    parser.add_argument('--fix', action='store_true', help='Deactivate failing products')
    args = parser.parse_args()
    
    audit(args.category)
    if args.fix:
        fix()
