"""Full DB schema audit."""
import sys
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query

print('=== TABLES ===')
tables = query("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
for t in tables:
    print(f'  {t["table_name"]}')

print('\n=== PRODUCTS COLUMNS ===')
cols = query("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name='products' ORDER BY ordinal_position")
for c in cols:
    print(f'  {c["column_name"]:25s} {c["data_type"]:20s} nullable={c["is_nullable"]}')

print('\n=== MATCHES COLUMNS ===')
cols = query("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name='matches' ORDER BY ordinal_position")
for c in cols:
    print(f'  {c["column_name"]:25s} {c["data_type"]:20s} nullable={c["is_nullable"]}')

print('\n=== PRICE HISTORY COLUMNS ===')
cols = query("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name='product_price_history' ORDER BY ordinal_position")
for c in cols:
    print(f'  {c["column_name"]:25s} {c["data_type"]:20s} nullable={c["is_nullable"]}')

print('\n=== INDICES ===')
indices = query("SELECT indexname, indexdef FROM pg_indexes WHERE tablename='products' OR tablename='matches' ORDER BY tablename, indexname")
for i in indices:
    print(f'  {i["indexname"]:30s} {i["indexdef"][:80]}')

print('\n=== DATA QUALITY ===')
# Category name consistency
cats = query("SELECT DISTINCT category_l1 FROM products WHERE is_active=true ORDER BY category_l1")
print(f'Category L1 values ({len(cats)}):')
for c in cats:
    cnt = query("SELECT COUNT(*) as c FROM products WHERE is_active=true AND category_l1=%s", (c['category_l1'],))
    print(f'  {c["category_l1"]:25s} {cnt[0]["c"]} products')

# Platform consistency
platforms = query("SELECT DISTINCT platform FROM products WHERE is_active=true")
print(f'\nPlatform values: {[p["platform"] for p in platforms]}')

# Check for NULL embeddings
no_emb = query("SELECT COUNT(*) as c FROM products WHERE is_active=true AND embedding IS NULL")
print(f'Products without embeddings: {no_emb[0]["c"]}')

# Check for NULL category_l1
null_cat = query("SELECT COUNT(*) as c FROM products WHERE is_active=true AND category_l1 IS NULL")
print(f'Products without category_l1: {null_cat[0]["c"]}')

# Match methods
methods = query("SELECT DISTINCT match_method, COUNT(*) as c FROM matches GROUP BY match_method ORDER BY match_method")
print(f'\nMatch methods:')
for m in methods:
    print(f'  {m["match_method"]:20s} {m["c"]}')
