#!/usr/bin/env python3
"""Validate Mappings — Check category mapping quality.

Usage:
    python3 scripts/validate_mappings.py                    # Validate all
    python3 scripts/validate_mappings.py --category Audio   # Validate specific L1
"""
import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from scripts.db import query


def validate_mappings(category=None):
    """Validate category mappings by checking product match rates."""
    conditions = ["1=1"]
    params = []
    
    if category:
        conditions.append("cm.our_l1 = %s")
        params.append(category)
    
    where = " AND ".join(conditions)
    
    # Get all internal categories with their platform mappings
    categories = query(f"""
        SELECT cm.our_l1, cm.our_l2, cm.our_l3,
               ARRAY_AGG(DISTINCT cm.platform) as platforms,
               COUNT(DISTINCT cm.platform) as platform_count
        FROM category_mappings cm
        WHERE {where}
        GROUP BY cm.our_l1, cm.our_l2, cm.our_l3
        ORDER BY cm.our_l1, cm.our_l2, cm.our_l3
    """, tuple(params))
    
    print(f"\n{'='*80}")
    print(f"Category Mapping Validation")
    print(f"{'='*80}\n")
    
    issues = []
    good = []
    
    for cat in categories:
        l1, l2, l3 = cat['our_l1'], cat['our_l2'], cat['our_l3']
        platforms = cat['platforms']
        platform_count = cat['platform_count']
        
        # Check if we have products in this category
        product_stats = query("""
            SELECT platform, COUNT(*) as cnt
            FROM products
            WHERE category_l1 = %s AND category_l2 = %s AND category_l3 = %s
            GROUP BY platform
        """, (l1, l2, l3))
        
        product_counts = {s['platform']: s['cnt'] for s in product_stats}
        total_products = sum(product_counts.values())
        
        # Check if we have products from multiple platforms
        platforms_with_products = [p for p, c in product_counts.items() if c > 0]
        
        # Calculate match potential
        has_amazon = any(p in platforms_with_products for p in ['amazon_br', 'amazon_us'])
        has_ml = 'ml' in platforms_with_products
        
        status = "OK"
        notes = []
        
        if total_products == 0:
            status = "NO_DATA"
            notes.append("No products scraped yet")
        elif not has_amazon and not has_ml:
            status = "NO_DATA"
            notes.append("No products from any platform")
        elif has_amazon and not has_ml:
            status = "AMAZON_ONLY"
            notes.append("Missing ML products")
        elif not has_amazon and has_ml:
            status = "ML_ONLY"
            notes.append("Missing Amazon products")
        elif platform_count < 3:
            status = "INCOMPLETE"
            notes.append(f"Only {platform_count}/3 platforms mapped")
        
        # Check match rate if we have products from multiple platforms
        if has_amazon and has_ml:
            amazon_count = sum(c for p, c in product_counts.items() if p.startswith('amazon'))
            ml_count = product_counts.get('ml', 0)
            
            # Check how many matches exist
            match_count = query("""
                SELECT COUNT(*) as cnt
                FROM matches m
                JOIN products p1 ON m.product_a_id = p1.id
                JOIN products p2 ON m.product_b_id = p2.id
                WHERE p1.category_l1 = %s AND p1.category_l2 = %s AND p1.category_l3 = %s
            """, (l1, l2, l3))[0]['cnt']
            
            match_rate = match_count / min(amazon_count, ml_count) * 100 if min(amazon_count, ml_count) > 0 else 0
            
            if match_rate < 20:
                status = "LOW_MATCHES"
                notes.append(f"Match rate: {match_rate:.0f}% ({match_count} matches)")
            elif match_rate >= 50:
                status = "GOOD"
                notes.append(f"Match rate: {match_rate:.0f}% ({match_count} matches)")
            else:
                notes.append(f"Match rate: {match_rate:.0f}% ({match_count} matches)")
        
        # Print result
        if status in ["OK", "GOOD"]:
            good.append((l1, l2, l3, status, notes))
        else:
            issues.append((l1, l2, l3, status, notes, product_counts))
    
    # Print good categories
    print(f"✅ Categories with data ({len(good)}):")
    for l1, l2, l3, status, notes in good:
        print(f"  {l1}/{l2}/{l3} — {', '.join(notes)}")
    
    # Print issues
    if issues:
        print(f"\n⚠️  Categories with issues ({len(issues)}):")
        for l1, l2, l3, status, notes, counts in issues:
            counts_str = ', '.join(f"{p}: {c}" for p, c in counts.items())
            print(f"  {l1}/{l2}/{l3} — {status}")
            print(f"    Products: {counts_str or 'none'}")
            for note in notes:
                print(f"    {note}")
    
    # Summary
    print(f"\n{'='*80}")
    print(f"Summary: {len(good)} OK, {len(issues)} issues")
    print(f"{'='*80}\n")
    
    return issues


def main():
    parser = argparse.ArgumentParser(description='Validate Category Mappings')
    parser.add_argument('--category', type=str, help='Validate specific L1 category')
    args = parser.parse_args()
    
    validate_mappings(category=args.category)


if __name__ == '__main__':
    main()
