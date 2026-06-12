"""Check match quality after fix."""
import sys
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query

# Check Casa matches
print('=== CASA MATCHES (>=70%) ===')
r = query("""
    SELECT m.confidence, a.title as br, a.platform_id as br_id,
           b.title as ml, b.platform_id as ml_id
    FROM matches m
    JOIN products a ON m.product_a_id = a.id
    JOIN products b ON m.product_b_id = b.id
    WHERE a.category_l1 = 'Casa'
    ORDER BY m.confidence DESC
""")
for row in r:
    conf = float(row['confidence'] or 0) * 100
    br = (str(row['br'] or '')[:50])
    ml = (str(row['ml'] or '')[:50])
    print(f'  {conf:.0f}% | {row["br_id"]} vs {row["ml_id"]}')
    print(f'    BR: {br}')
    print(f'    ML: {ml}')
    print()

# Check Audio matches - top 5
print('=== TOP AUDIO MATCHES ===')
r2 = query("""
    SELECT m.confidence, a.title as br, a.platform_id as br_id,
           b.title as ml, b.platform_id as ml_id
    FROM matches m
    JOIN products a ON m.product_a_id = a.id
    JOIN products b ON m.product_b_id = b.id
    WHERE a.category = 'microfone' OR a.category = 'headphone'
    ORDER BY m.confidence DESC
    LIMIT 8
""")
for row in r2:
    conf = float(row['confidence'] or 0) * 100
    br = (str(row['br'] or '')[:50])
    ml = (str(row['ml'] or '')[:50])
    print(f'  {conf:.0f}% | {row["br_id"]} vs {row["ml_id"]}')
    print(f'    BR: {br}')
    print(f'    ML: {ml}')
    print()

# Total
r3 = query("SELECT COUNT(*) as cnt FROM matches")
r4 = query("SELECT COUNT(*) as cnt FROM matches WHERE confidence >= 0.80")
print(f'Total matches: {r3[0]["cnt"]}, ALTA (>=80%): {r4[0]["cnt"]}')
