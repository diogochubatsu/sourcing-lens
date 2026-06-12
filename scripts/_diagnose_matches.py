"""Diagnose and fix match quality issues."""
import sys
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query, execute

# 1. Check Casa matches that are clearly wrong
print('=== CASA MATCHES BY TYPE ===')
r = query("""
    SELECT m.match_method, m.confidence, a.title as br_title, b.title as ml_title
    FROM matches m
    JOIN products a ON m.product_a_id = a.id
    JOIN products b ON m.product_b_id = b.id
    WHERE a.category_l1 = 'Casa'
    ORDER BY m.match_method, m.confidence DESC
""")
for row in r:
    conf = float(row['confidence'] or 0) * 100
    br = (row['br_title'] or '')[:45]
    ml = (row['ml_title'] or '')[:45]
    tag = 'GOOD' if conf >= 70 else 'BAD'
    print(f'  [{row["match_method"]:20s}] {tag} {conf:.0f}% | {br} | {ml}')

# 2. Check what the amazon_br_vs_us matches look like
print('\n=== AMAZON BR VS US MATCHES ===')
r2 = query("""
    SELECT m.confidence, a.title as br_title, a.platform_id as br_id,
           b.title as us_title, b.platform_id as us_id
    FROM matches m
    JOIN products a ON m.product_a_id = a.id
    JOIN products b ON m.product_b_id = b.id
    WHERE m.match_method = 'amazon_br_vs_us' AND a.category_l1 = 'Casa'
    LIMIT 10
""")
for row in r2:
    conf = float(row['confidence'] or 0)
    print(f'  {conf*100:.0f}% | {row["br_id"]} vs {row["us_id"]}')
    print(f'    BR: {str(row["br_title"])[:50]}')
    print(f'    US: {str(row["us_title"])[:50]}')
    print()

# 3. Check if ML products have embeddings
print('\n=== EMBEDDING COVERAGE ===')
r3 = query("""
    SELECT category_l1, platform,
           COUNT(*) as total,
           SUM(CASE WHEN embedding IS NOT NULL THEN 1 ELSE 0 END) as has_emb
    FROM products WHERE is_active=true
    GROUP BY category_l1, platform
    ORDER BY category_l1, platform
""")
for row in r3:
    total = row['total']
    has = row['has_emb']
    if total > 0:
        print(f'  {row["category_l1"]:25s} {row["platform"]:12s} {total:4d} total, {has:4d} com emb ({has*100//total}%)')
