"""Final verification of fix."""
import sys
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query

print('=== CASA MATCHES (FIXED) ===')
r = query("""
    SELECT m.confidence, a.title as br, b.title as ml, a.category_l3
    FROM matches m
    JOIN products a ON m.product_a_id = a.id
    JOIN products b ON m.product_b_id = b.id
    WHERE a.category_l1 = 'Casa'
    ORDER BY a.category_l3, m.confidence DESC
""")
for row in r:
    conf = float(row['confidence'] or 0) * 100
    br = (str(row['br'] or '')[:45])
    ml = (str(row['ml'] or '')[:45])
    print(f'  [{row["category_l3"]:20s}] {conf:.0f}%')
    print(f'    BR: {br}')
    print(f'    ML: {ml}')
    print()

# Final DB state
r2 = query("SELECT category_l1, platform, COUNT(*) as cnt FROM products WHERE is_active=true GROUP BY category_l1, platform ORDER BY category_l1, platform")
print('=== FINAL DB ===')
cats = {}
for row in r2:
    cats.setdefault(row['category_l1'], {})
    cats[row['category_l1']][row['platform']] = row['cnt']
for cl1, platforms in sorted(cats.items()):
    total = sum(platforms.values())
    parts = ' | '.join(f'{p}={c}' for p, c in sorted(platforms.items()))
    print(f'  {cl1:25s} {total:4d} ({parts})')

r3 = query("SELECT COUNT(*) as cnt FROM products WHERE is_active=true")
r4 = query("SELECT COUNT(*) as cnt FROM products WHERE is_active=true AND sales_30d IS NOT NULL")
r5 = query("SELECT COUNT(*) as cnt FROM matches")
print(f'\nTotal ativos: {r3[0]["cnt"]}')
print(f'Com sales_30d: {r4[0]["cnt"]} ({r4[0]["cnt"]*100//r3[0]["cnt"]}%)')
print(f'Matches: {r5[0]["cnt"]}')
