"""Fix duplicate match and check zero-price products."""
import sys
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query, execute

# Fix duplicate match
r = query("SELECT m1.id as mid, m1.product_a_id, m1.product_b_id FROM matches m1 JOIN matches m2 ON m1.product_a_id=m2.product_a_id AND m1.product_b_id=m2.product_b_id AND m1.id < m2.id")
print(f'Duplicate matches: {len(r)}')
for row in r:
    execute('DELETE FROM matches WHERE id = %s', (row['mid'],))
    print(f'  Deleted match id={row["mid"]}')

# Check zero-price products
r2 = query("SELECT platform, platform_id, title, price FROM products WHERE is_active=true AND (price IS NULL OR price <= 0) LIMIT 25")
print(f'\nZero-price products: {len(r2)}')
for row in r2:
    t = (row['title'] or '')[:50]
    print(f'  {row["platform"]:12s} {row["platform_id"]:20s} R${row["price"]} | {t}')

# Deactivate them
if r2:
    execute("UPDATE products SET is_active=false WHERE is_active=true AND (price IS NULL OR price <= 0)")
    print(f'Deactivated {len(r2)} zero-price products')

# Final check
r3 = query("SELECT COUNT(*) as cnt FROM products WHERE is_active=true")
r4 = query("SELECT COUNT(*) as cnt FROM products WHERE is_active=true AND (price IS NULL OR price <= 0)")
r5 = query("SELECT COUNT(*) as cnt FROM matches")
print(f'\nActive products: {r3[0]["cnt"]}')
print(f'Zero-price remaining: {r4[0]["cnt"]}')
print(f'Matches: {r5[0]["cnt"]}')
