"""Clean DB: deactivate broken products, delete legacy matches."""
import sys
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query, execute

# 1. Deactivate 14 products with broken images
r = query("SELECT id, platform_id, category_l1 FROM products WHERE is_active=true AND embedding IS NULL")
print(f'Deactivating {len(r)} products with broken images:')
for p in r:
    execute("UPDATE products SET is_active=false WHERE id=%s", (p['id'],))
    print(f'  {p["platform_id"]:20s} {p["category_l1"]}')

# 2. Delete legacy matches (2 amazon_br_vs_us + 1 image_title_brand)
del1 = execute("DELETE FROM matches WHERE match_method IN ('amazon_br_vs_us', 'image_title_brand')")
print(f'\nDeleted {del1} legacy matches')

# 3. Verify final state
active = query("SELECT COUNT(*) as c FROM products WHERE is_active=true")[0]['c']
missing_emb = query("SELECT COUNT(*) as c FROM products WHERE is_active=true AND embedding IS NULL")[0]['c']
matches = query("SELECT COUNT(*) as c FROM matches")[0]['c']

print(f'\n=== FINAL ===')
print(f'Active products: {active}')
print(f'Still missing embeddings: {missing_emb}')
print(f'Matches: {matches}')
print(f'Match methods:')
for r in query("SELECT match_method, COUNT(*) as c FROM matches GROUP BY match_method ORDER BY match_method"):
    print(f'  {r["match_method"]:20s} {r["c"]}')
