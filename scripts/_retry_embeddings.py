"""Retry failed Amazon image embeddings."""
import sys, requests
from io import BytesIO
from PIL import Image
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query, execute
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('clip-ViT-B-32')
products = query("SELECT id, platform_id, image_urls FROM products WHERE is_active=true AND embedding IS NULL")
print(f'Retrying {len(products)}...')

done = 0
for p in products:
    urls = p['image_urls'] or []
    url = urls[0] if urls else ''
    if not url or not isinstance(url, str) or not url.startswith('http'):
        continue
    
    try:
        # Amazon images need proper headers
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(url, timeout=30, headers=headers)
        if r.status_code != 200:
            print(f'  HTTP {r.status_code} for {p["platform_id"]}: {url[:60]}')
            continue
        img = Image.open(BytesIO(r.content)).convert('RGB')
        emb = model.encode(img)
        execute("UPDATE products SET embedding = %s::vector WHERE id = %s", (emb.tolist(), p['id']))
        done += 1
        print(f'  OK {p["platform_id"]}')
    except Exception as e:
        print(f'  ERR {p["platform_id"]}: {str(e)[:60]}')

print(f'Generated: {done}')
remaining = query("SELECT COUNT(*) as c FROM products WHERE is_active=true AND embedding IS NULL")
print(f'Remaining: {remaining[0]["c"]}')
