"""Hygiene: DB check."""
import sys
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query

# Duplicate products
r = query("SELECT platform, platform_id, COUNT(*) as cnt FROM products WHERE is_active=true GROUP BY platform, platform_id HAVING COUNT(*) > 1")
if r:
    print('=== DUPLICATE PRODUCTS ===')
    for row in r:
        print(f'  {row["platform"]:12s} {row["platform_id"]:20s} x{row["cnt"]}')
else:
    print('=== NO DUPLICATE PRODUCTS ===')

# Duplicate matches
r2 = query("SELECT COUNT(*) as cnt FROM matches m1 JOIN matches m2 ON m1.product_a_id=m2.product_a_id AND m1.product_b_id=m2.product_b_id AND m1.id < m2.id")
print(f'Duplicate matches: {r2[0]["cnt"]}')

# Zero prices
r3 = query("SELECT COUNT(*) as cnt FROM products WHERE is_active=true AND (price IS NULL OR price <= 0)")
print(f'Zero/null price products: {r3[0]["cnt"]}')

# Missing images
r4 = query("SELECT COUNT(*) as cnt FROM products WHERE is_active=true AND (image_urls IS NULL OR array_length(image_urls,1) IS NULL)")
print(f'Missing images: {r4[0]["cnt"]}')

# Sales by platform
r5 = query("SELECT platform, COUNT(*) as cnt FROM products WHERE is_active=true AND sales_30d IS NOT NULL GROUP BY platform ORDER BY platform")
print()
print('=== SALES BY PLATFORM ===')
for row in r5:
    print(f'  {row["platform"]:12s} {row["cnt"]}')

# Totals
r6 = query("SELECT COUNT(*) as cnt FROM products WHERE is_active=true")
r7 = query("SELECT COUNT(*) as cnt FROM matches")
r8 = query("SELECT COUNT(*) as cnt FROM products WHERE is_active=true AND sales_30d IS NOT NULL")
print(f'\nTotal ativos: {r6[0]["cnt"]}')
print(f'Total matches: {r7[0]["cnt"]}')
print(f'Com sales: {r8[0]["cnt"]} ({r8[0]["cnt"]*100//r6[0]["cnt"]}%)')
