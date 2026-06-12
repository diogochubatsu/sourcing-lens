"""Fix embeddings for all remaining products (local paths + http timeouts)."""
import sys, os, requests
from io import BytesIO
from PIL import Image
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query, execute
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('clip-ViT-B-32')
products = query("SELECT id, platform_id, image_urls FROM products WHERE is_active=true AND embedding IS NULL")
print(f'Products without embeddings: {len(products)}')

done = 0
for p in products:
    urls = p['image_urls'] or []
    url = urls[0] if urls else ''
    if not url or not isinstance(url, str):
        continue
    
    img = None
    try:
        if url.startswith('http'):
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                img = Image.open(BytesIO(r.content)).convert('RGB')
        elif url.startswith('/images/'):
            # Local cached file
            local_path = '/mnt/ssd/arbitlens/data' + url
            if os.path.exists(local_path):
                img = Image.open(local_path).convert('RGB')
    except:
        continue
    
    if img is None:
        continue
    
    try:
        emb = model.encode(img)
        execute("UPDATE products SET embedding = %s::vector WHERE id = %s", (emb.tolist(), p['id']))
        done += 1
        if done % 10 == 0:
            print(f'  {done}...')
    except:
        continue

print(f'Embeddings generated: {done}')

# Final check
remaining = query("SELECT COUNT(*) as c FROM products WHERE is_active=true AND embedding IS NULL")
print(f'Remaining without embeddings: {remaining[0]["c"]}')
