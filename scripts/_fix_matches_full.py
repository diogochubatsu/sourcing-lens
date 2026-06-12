"""Fix: delete bad matches, generate embeddings, run matching for ALL categories."""
import sys, os, time, requests
from io import BytesIO
from PIL import Image
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query, execute

# Step 1: Delete bad matches
print('=== Step 1: Delete bad matches ===')
del_img = execute("DELETE FROM matches WHERE match_method IN ('image_title_brand', 'amazon_br_vs_us') AND confidence < 0.70")
print(f'Deleted {del_img} low-quality matches')

# Also delete the old embedding matches (they're stale)
del_emb = execute("DELETE FROM matches WHERE match_method = 'embedding_clip'")
print(f'Deleted {del_emb} old CLIP matches (will regenerate)')

# Step 2: Generate embeddings for ALL products without them
print('\n=== Step 2: Generate missing embeddings ===')
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("clip-ViT-B-32")
print('Model loaded')

products = query(
    "SELECT id, platform_id, image_urls, category_l1 FROM products "
    "WHERE is_active = true AND embedding IS NULL"
)
print(f'Products without embeddings: {len(products)}')

done = 0
errors = 0
for p in products:
    img_urls = p['image_urls'] or []
    img_url = img_urls[0] if img_urls else ''
    if not img_url or not isinstance(img_url, str) or not img_url.startswith('http'):
        errors += 1
        continue
    try:
        resp = requests.get(img_url, timeout=15)
        if resp.status_code != 200:
            errors += 1
            continue
        img = Image.open(BytesIO(resp.content)).convert('RGB')
        emb = model.encode(img)
        emb_list = emb.tolist()
        execute("UPDATE products SET embedding = %s::vector WHERE id = %s", (emb_list, p['id']))
        done += 1
        if done % 20 == 0:
            print(f'  {done}/{len(products)}...')
    except Exception as e:
        errors += 1

print(f'Embeddings: {done} done, {errors} errors')

# Step 3: Run matching for ALL categories
print('\n=== Step 3: Run matching_v6 for ALL categories ===')

THRESHOLD = 0.70

def run_matching(category, l3=None):
    if l3:
        br = query(
            "SELECT id, platform_id, title, price, url, embedding "
            "FROM products WHERE platform='amazon_br' AND category=%s AND category_l3=%s AND embedding IS NOT NULL",
            (category, l3))
        ml = query(
            "SELECT id, platform_id, title, price, url, embedding "
            "FROM products WHERE platform='ml' AND category=%s AND category_l3=%s AND embedding IS NOT NULL",
            (category, l3))
    else:
        br = query(
            "SELECT id, platform_id, title, price, url, embedding "
            "FROM products WHERE platform='amazon_br' AND category=%s AND embedding IS NOT NULL",
            (category,))
        ml = query(
            "SELECT id, platform_id, title, price, url, embedding "
            "FROM products WHERE platform='ml' AND category=%s AND embedding IS NOT NULL",
            (category,))
    
    label = f'{category} ({l3})' if l3 else category
    if not br or not ml:
        return []
    
    all_scores = []
    for a in br:
        if l3:
            best = query("""
                SELECT id, 1 - (embedding <=> %s::vector) as sim
                FROM products WHERE platform='ml' AND category=%s AND category_l3=%s AND embedding IS NOT NULL
                ORDER BY embedding <=> %s::vector LIMIT 1
            """, (a['embedding'], category, l3, a['embedding']))
        else:
            best = query("""
                SELECT id, 1 - (embedding <=> %s::vector) as sim
                FROM products WHERE platform='ml' AND category=%s AND embedding IS NOT NULL
                ORDER BY embedding <=> %s::vector LIMIT 1
            """, (a['embedding'], category, a['embedding']))
        
        if best and best[0]['sim'] >= THRESHOLD:
            b = best[0]
            all_scores.append((a['id'], b['id'], b['sim']))
    
    all_scores.sort(key=lambda x: x[2], reverse=True)
    seen_br = set()
    seen_ml = set()
    final = []
    for m in all_scores:
        if m[0] not in seen_br and m[1] not in seen_ml:
            seen_br.add(m[0])
            seen_ml.add(m[1])
            final.append(m)
    
    print(f'  {label:30s} BR={len(br)}, ML={len(ml)} -> {len(final)} matches (deduped)')
    return final

# Get all L3 categories with both platforms
l3_cats = query("""
    SELECT a.category, a.category_l3
    FROM products a JOIN products m ON a.category = m.category AND a.category_l3 = m.category_l3
    WHERE a.platform='amazon_br' AND m.platform='ml'
      AND a.embedding IS NOT NULL AND m.embedding IS NOT NULL
    GROUP BY a.category, a.category_l3
    ORDER BY a.category, a.category_l3
""")

total = 0
for cat in l3_cats:
    matches = run_matching(cat['category'], cat['category_l3'])
    for aid, bid, sc in matches:
        execute(
            "INSERT INTO matches (product_a_id, product_b_id, confidence, match_method) "
            "VALUES (%s, %s, %s, 'embedding_clip')",
            (int(aid), int(bid), float(sc)))
    total += len(matches)

# Also try per-L1 without L3 filter (for cats that have no L3 differentiation)
cats_l1 = query("""
    SELECT DISTINCT a.category
    FROM products a JOIN products m ON a.category = m.category
    WHERE a.platform='amazon_br' AND m.platform='ml'
      AND a.embedding IS NOT NULL AND m.embedding IS NOT NULL
    ORDER BY a.category
""")

for cat in cats_l1:
    c = cat['category']
    # Skip if already processed via L3
    already = any(c == lc['category'] for lc in l3_cats)
    if already:
        continue
    matches = run_matching(c)
    for aid, bid, sc in matches:
        execute(
            "INSERT INTO matches (product_a_id, product_b_id, confidence, match_method) "
            "VALUES (%s, %s, %s, 'embedding_clip')",
            (int(aid), int(bid), float(sc)))
    total += len(matches)

print(f'\nTotal new CLIP matches: {total}')

# Final summary
r = query("SELECT COUNT(*) as cnt FROM matches")
r2 = query("SELECT category_l1, COUNT(*) as cnt FROM matches m JOIN products a ON m.product_a_id=a.id GROUP BY category_l1 ORDER BY cnt DESC")
print(f'\n=== MATCHES BY CATEGORY (total: {r[0]["cnt"]}) ===')
for row in r2:
    print(f'  {row["category_l1"]:25s} {row["cnt"]}')
