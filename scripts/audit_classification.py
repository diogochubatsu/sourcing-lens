#!/usr/bin/env python3
"""
audit_classification.py — Audit classification accuracy by sampling products.

Usage:
  python3 audit_classification.py --sample 200
  python3 audit_classification.py --check-product <product_id>
"""
import os
import sys
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def get_pg_conn():
    import psycopg2
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL not set")
    return psycopg2.connect(database_url)

def audit_sample(sample_size=200):
    """Sample products and show their classification for manual review."""
    conn = get_pg_conn()
    cursor = conn.cursor()
    
    # Get random sample
    cursor.execute("""
        SELECT id, platform, title, category, category_n2, category_n3, category_n4
        FROM arbitlens_products
        WHERE is_active = true
        ORDER BY RANDOM()
        LIMIT %s
    """, (sample_size,))
    
    products = cursor.fetchall()
    
    print(f"\n=== Classification Audit (sample: {len(products)}) ===\n")
    
    # Count classification coverage
    n1_count = sum(1 for p in products if p[3])
    n2_count = sum(1 for p in products if p[4])
    n3_count = sum(1 for p in products if p[5])
    n4_count = sum(1 for p in products if p[6])
    
    print(f"Coverage in sample:")
    print(f"  N1: {n1_count}/{len(products)} ({n1_count/len(products)*100:.1f}%)")
    print(f"  N2: {n2_count}/{len(products)} ({n2_count/len(products)*100:.1f}%)")
    print(f"  N3: {n3_count}/{len(products)} ({n3_count/len(products)*100:.1f}%)")
    print(f"  N4: {n4_count}/{len(products)} ({n4_count/len(products)*100:.1f}%)")
    
    # Show products missing N2 classification (potential keyword gaps)
    missing_n2 = [p for p in products if p[3] and not p[4]]
    if missing_n2:
        print(f"\n=== Products with N1 but missing N2 ({len(missing_n2)}) ===")
        print("These need better N2 keyword rules:\n")
        for p in missing_n2[:20]:
            print(f"  [{p[1]}] {p[2][:60]}")
            print(f"    N1: {p[3]} | N2: {p[4]} | N3: {p[5]}")
            print()
    
    # Show products missing N3 classification
    missing_n3 = [p for p in products if p[4] and not p[5]]
    if missing_n3:
        print(f"\n=== Products with N2 but missing N3 ({len(missing_n3)}) ===")
        print("These need better N3 keyword rules:\n")
        for p in missing_n3[:20]:
            print(f"  [{p[1]}] {p[2][:60]}")
            print(f"    N1: {p[3]} | N2: {p[4]} | N3: {p[5]}")
            print()
    
    # Show top N1 categories
    cursor.execute("""
        SELECT category, COUNT(*) as cnt
        FROM arbitlens_products
        WHERE is_active = true AND category IS NOT NULL
        GROUP BY category ORDER BY cnt DESC LIMIT 10
    """)
    print("\n=== Top N1 Categories ===")
    for cat, cnt in cursor.fetchall():
        print(f"  {cat:20s} {cnt:5d}")
    
    # Show top N2 categories
    cursor.execute("""
        SELECT category_n2, COUNT(*) as cnt
        FROM arbitlens_products
        WHERE is_active = true AND category_n2 IS NOT NULL
        GROUP BY category_n2 ORDER BY cnt DESC LIMIT 15
    """)
    print("\n=== Top N2 Categories ===")
    for cat, cnt in cursor.fetchall():
        print(f"  {cat:30s} {cnt:5d}")
    
    conn.close()

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Audit classification')
    parser.add_argument('--sample', type=int, default=200)
    args = parser.parse_args()
    
    audit_sample(args.sample)

if __name__ == '__main__':
    main()
