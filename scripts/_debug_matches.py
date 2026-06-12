"""Debug match quality issue."""
import sys
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query

# Match methods
r = query("SELECT DISTINCT match_method, COUNT(*) as cnt FROM matches GROUP BY match_method ORDER BY cnt DESC")
print('=== MATCH METHODS ===')
for row in r:
    print(f'  {row["match_method"]:20s} {row["cnt"]}')

# Casa ML products
r2 = query("SELECT platform_id, title, price, sales_30d FROM products WHERE category_l1='Casa' AND platform='ml' AND is_active=true ORDER BY sales_30d DESC NULLS LAST LIMIT 20")
print('\n=== CASA ML TOP 20 ===')
for row in r2:
    t = (row['title'] or '')[:60]
    p = float(row['price'] or 0)
    s = str(row['sales_30d'] or 'None')
    print(f'  {row["platform_id"]:>15s} | R${p:>8.2f} | vend={s:>8s} | {t}')

# Casa BR products
r3 = query("SELECT platform_id, title, price FROM products WHERE category_l1='Casa' AND platform='amazon_br' AND is_active=true LIMIT 20")
print('\n=== CASA BR TOP 20 ===')
for row in r3:
    t = (row['title'] or '')[:60]
    p = float(row['price'] or 0)
    print(f'  {row["platform_id"]:>15s} | R${p:>8.2f} | {t}')

# Check what categories the old good matches were in
r4 = query("SELECT category_l1, COUNT(*) FROM products WHERE is_active=true GROUP BY category_l1 ORDER BY category_l1")
print('\n=== ALL CATEGORIES ===')
for row in r4:
    print(f'  {row["category_l1"]:25s} {row["count"]}')
