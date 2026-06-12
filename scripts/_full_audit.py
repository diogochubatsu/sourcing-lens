"""Complete v0.1 audit."""
import sys
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query

print('=' * 60)
print('  ARBITLENS v0.1 — COMPLETE AUDIT')
print('=' * 60)

print('\n--- DATABASE ---')
t = query("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
print(f'Tables: {[r["table_name"] for r in t]}')

c = query("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name='products' ORDER BY ordinal_position")
print(f'\nProducts columns ({len(c)}):')
for r in c:
    print(f'  {r["column_name"]:25s} {r["data_type"]:20s} nullable={r["is_nullable"]}')

print('\n--- DATA QUALITY ---')
active = query("SELECT COUNT(*) as c FROM products WHERE is_active=true")[0]['c']
print(f'Active products: {active}')

checks = [
    ('No image', "image_urls IS NULL OR array_length(image_urls,1) IS NULL"),
    ('No price', "price IS NULL OR price <= 0"),
    ('No sales', "sales_30d IS NULL OR sales_30d <= 0"),
    ('No embedding', "embedding IS NULL"),
    ('No category_l1', "category_l1 IS NULL"),
]
for name, cond in checks:
    cnt = query(f"SELECT COUNT(*) as c FROM products WHERE is_active=true AND ({cond})")[0]['c']
    print(f'  {name:20s} {cnt:4d} ({cnt*100//active:2d}%)')

print('\nBy platform:')
for r in query("SELECT platform, COUNT(*) as c FROM products WHERE is_active=true GROUP BY platform ORDER BY platform"):
    print(f'  {r["platform"]:12s} {r["c"]}')

print('\nBy category:')
for r in query("SELECT category_l1, COUNT(*) as c FROM products WHERE is_active=true GROUP BY category_l1 ORDER BY category_l1"):
    print(f'  {r["category_l1"]:25s} {r["c"]}')

print('\nMatches:')
for r in query("SELECT match_method, COUNT(*) as c FROM matches GROUP BY match_method"):
    print(f'  {r["match_method"]:20s} {r["c"]}')

old = query("SELECT COUNT(*) as c FROM products WHERE is_active=true AND category IS DISTINCT FROM category_l1")[0]['c']
print(f'\nOld category != category_l1: {old}')

print('\n--- FILES (LEGACY IDENTIFICATION) ---')
print('''
ROOT (15 files): 15.md + 2.py
  KEEP:    EPIC-V0.1.md, EPIC-V0.2.md, IMAGE-INTELLIGENCE.md,
           MANIFEST.md, README.md, SOUL.md, VERSION.md
  LEGACY:  EPIC.md, INFRA.md, LOOP5-PLAN.md, MVP-PLAN.md,
           PI1-PLAN.md, PI6-PLAN.md, PI7-PLAN.md, PROGRESS.md,
           compute_image_hashes.py, polish_dashboard.py

APP (19 files): backend 12 + frontend 3 + migrations 1
  All active - no legacy

SCRIPTS (48 files): 25 active + 23 legacy
  ACTIVE (keep): daily_snapshot, data_quality_gate, db,
    find_similar, matching_v6, sales_pipeline, 
    scrape_amazon_bestsellers, start_port5000, start_server
  LEGACY (delete): matching_v4, matching_v5, extract_ml,
    fix_data_quality, generate_clip_embeddings, scrape_prices,
    scrape_ml_automotive, scrape_ml_automotive_v2
  TEMP (_prefix, keep for reproducibility): 25 files

DOCS: 3 files (1688-scraping.md is legacy, SOURCE-MATRIX keep)
LOGS: 5 files (all legacy debug)
''')
