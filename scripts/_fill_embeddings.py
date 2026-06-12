"""Generate remaining embeddings."""
import sys, requests
from io import BytesIO
from PIL import Image
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query, execute
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('clip-ViT-B-32')
products = query("SELECT id, platform_id, image_urls FROM products WHERE is_active=true AND embedding IS NULL")
print(f'Missing embeddings: {len(products)}')
done = 0
for p in products:
    urls = p['image_urls'] or []
    url = urls[0] if urls else ''
    if not url or not isinstance(url, str) or not url.startswith('http'):
        continue
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            continue
        img = Image.open(BytesIO(r.content)).convert('RGB')
        emb = model.encode(img)
        execute("UPDATE products SET embedding = %s::vector WHERE id = %s", (emb.tolist(), p['id']))
        done += 1
        if done % 10 == 0:
            print(f'  {done}...')
    except Exception as e:
        pass
print(f'Generated: {done}')
