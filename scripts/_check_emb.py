"""Check why embeddings fail and fix."""
import sys
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query

products = query("SELECT id, platform_id, image_urls, category_l1 FROM products WHERE is_active=true AND embedding IS NULL LIMIT 50")
print(f'Products without embeddings: {len(products)}')
for p in products:
    urls = p['image_urls'] or []
    first = urls[0] if urls else '(empty)'
    url_type = 'http' if isinstance(first, str) and first.startswith('http') else 'local' if isinstance(first, str) else 'none'
    first_short = str(first)[:80]
    print(f'  {p["id"]:5d} {p["platform_id"]:20s} [{url_type:6s}] {p["category_l1"]:20s} {first_short}')
