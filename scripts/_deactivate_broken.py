"""Deactivate 14 products with broken images."""
import sys
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query, execute

r = query("SELECT id, platform_id, category_l1, title FROM products WHERE is_active=true AND embedding IS NULL")
print(f'Deactivating {len(r)} products with broken images:')
for p in r:
    t = (p['title'] or '')[:50]
    print(f'  {p["platform_id"]:20s} {p["category_l1"]:20s} {t}')
    execute("UPDATE products SET is_active=false WHERE id=%s", (p['id'],))

r2 = query("SELECT COUNT(*) as c FROM products WHERE is_active=true")
r3 = query("SELECT COUNT(*) as c FROM products WHERE embedding IS NULL AND is_active=true")
print(f'\nActive products: {r2[0]["c"]}')
print(f'Still missing embeddings: {r3[0]["c"]}')
