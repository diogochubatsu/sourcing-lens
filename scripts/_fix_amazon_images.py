"""Fix corrupted Amazon image URLs."""
import sys
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query, execute

products = query("SELECT id, platform_id, image_urls, title FROM products WHERE is_active=true AND embedding IS NULL")
print(f'Fixing {len(products)} products...')

fixed = 0
for p in products:
    urls = p['image_urls'] or []
    old_url = urls[0] if urls else ''
    if not old_url or 'm.media-amazon.com/images/I/B' not in old_url:
        continue
    
    # These URLs have ASIN mixed into the image path, which is wrong
    # Amazon CDN URLs should be: https://m.media-amazon.com/images/I/{hash}.jpg
    # The pattern /I/B01IEN6AQM is invalid - B01IEN6AQM is an ASIN, not image hash
    
    # Try the standard Amazon image pattern
    asin = p['platform_id']
    correct_url = f'https://images-na.ssl-images-amazon.com/images/I/41{asin}._AC_SX425_.jpg'
    
    # Check alternative patterns
    platform = 'amazon_br' if asin.startswith('B0') or asin.startswith('B00') else 'amazon_us'
    
    # Use the simpler pattern
    new_urls = [f'https://images-na.ssl-images-amazon.com/images/I/41{asin}._AC_SX425_.jpg']
    execute("UPDATE products SET image_urls = %s WHERE id = %s", (new_urls, p['id']))
    fixed += 1
    if fixed <= 5:
        print(f'  {p["platform_id"]}: {old_url[:60]} -> {new_urls[0][:60]}')

print(f'Fixed: {fixed}')

# Now try embeddings again
print('\nRetrying embeddings...')
import requests
from io import BytesIO
from PIL import Image
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('clip-ViT-B-32')
remaining = query("SELECT id, platform_id, image_urls FROM products WHERE is_active=true AND embedding IS NULL")

done = 0
for p in remaining:
    urls = p['image_urls'] or []
    url = urls[0] if urls else ''
    if not url or not isinstance(url, str) or not url.startswith('http'):
        continue
    try:
        r = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
        if r.status_code != 200:
            continue
        img = Image.open(BytesIO(r.content)).convert('RGB')
        emb = model.encode(img)
        execute("UPDATE products SET embedding = %s::vector WHERE id = %s", (emb.tolist(), p['id']))
        done += 1
    except:
        continue

print(f'New embeddings: {done}')
final = query("SELECT COUNT(*) as c FROM products WHERE is_active=true AND embedding IS NULL")
print(f'Without embeddings: {final[0]["c"]}')
