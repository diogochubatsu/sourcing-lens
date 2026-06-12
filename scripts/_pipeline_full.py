"""Generate embeddings + run matching for ALL new products."""
import sys, os, time, requests
from io import BytesIO
from PIL import Image
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query, execute
from sentence_transformers import SentenceTransformer

# Step 1: Generate embeddings for all products without them
print('=== Generating embeddings ===')
model = SentenceTransformer("clip-ViT-B-32")

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
        if done % 30 == 0:
            print(f'  {done}/{len(products)}...')
    except Exception as e:
        errors += 1

print(f'Embeddings: {done} done, {errors} errors')

# Step 2: Run matching for ALL categories
print('\n=== Running matching_v6 for ALL ===')

THRESHOLD = 0.70

def run_matching(category_l1, l3=None):
    if l3:
        br = query(
            "SELECT id, embedding FROM products WHERE platform='amazon_br' AND category_l1=%s AND category_l3=%s AND embedding IS NOT NULL AND is_active=true",
            (category_l1, l3))
        ml = query(
            "SELECT id, embedding FROM products WHERE platform='ml' AND category_l1=%s AND category_l3=%s AND embedding IS NOT NULL AND is_active=true",
            (category_l1, l3))
    else:
        br = query(
            "SELECT id, embedding FROM products WHERE platform='amazon_br' AND category_l1=%s AND embedding IS NOT NULL AND is_active=true",
            (category_l1,))
        ml = query(
            "SELECT id, embedding FROM products WHERE platform='ml' AND category_l1=%s AND embedding IS NOT NULL AND is_active=true",
            (category_l1,))
    
    if not br or not ml:
        return []
    
    all_scores = []
    for a in br:
        if l3:
            best = query("""
                SELECT id, 1 - (embedding <=> %s::vector) as sim
                FROM products WHERE platform='ml' AND category_l1=%s AND category_l3=%s AND embedding IS NOT NULL AND is_active=true
                ORDER BY embedding <=> %s::vector LIMIT 1
            """, (a['embedding'], category_l1, l3, a['embedding']))
        else:
            best = query("""
                SELECT id, 1 - (embedding <=> %s::vector) as sim
                FROM products WHERE platform='ml' AND category_l1=%s AND embedding IS NOT NULL AND is_active=true
                ORDER BY embedding <=> %s::vector LIMIT 1
            """, (a['embedding'], category_l1, a['embedding']))
        
        if best and best[0]['sim'] >= THRESHOLD:
            all_scores.append((a['id'], best[0]['id'], best[0]['sim']))
    
    all_scores.sort(key=lambda x: x[2], reverse=True)
    seen_br, seen_ml = set(), set()
    final = []
    for m in all_scores:
        if m[0] not in seen_br and m[1] not in seen_ml:
            seen_br.add(m[0])
            seen_ml.add(m[1])
            final.append(m)
    return final

# Delete old matches for categories we're about to process
execute("""
    DELETE FROM matches WHERE match_method = 'embedding_clip' AND id IN (
        SELECT m.id FROM matches m JOIN products p ON m.product_a_id = p.id
        WHERE p.category_l1 IN ('Bolsas','Mochilas','Moda','Meias','Moda Intima')
    )
""")

total = 0
new_cats = ['Bolsas', 'Mochilas', 'Moda', 'Meias', 'Moda Intima']
for cat in new_cats:
    matches = run_matching(cat)
    if not matches:
        print(f'  {cat:20s} 0 matches (no cross-platform data)')
        continue
    for aid, bid, sc in matches:
        execute(
            "INSERT INTO matches (product_a_id, product_b_id, confidence, match_method) VALUES (%s, %s, %s, 'embedding_clip')",
            (int(aid), int(bid), float(sc)))
    print(f'  {cat:20s} {len(matches)} matches')
    total += len(matches)

# Also run for all other categories
all_cats = query("""
    SELECT DISTINCT a.category_l1 FROM products a JOIN products m 
    ON a.category_l1 = m.category_l1
    WHERE a.platform='amazon_br' AND m.platform='ml'
      AND a.embedding IS NOT NULL AND m.embedding IS NOT NULL
      AND a.is_active=true AND m.is_active=true
      AND a.category_l1 NOT IN ('Bolsas','Mochilas','Moda','Meias','Moda Intima')
    ORDER BY a.category_l1
""")

for cat in all_cats:
    cl1 = cat['category_l1']
    # Delete old matches for this category
    execute("""
        DELETE FROM matches WHERE match_method = 'embedding_clip' AND id IN (
            SELECT m.id FROM matches m JOIN products p ON m.product_a_id = p.id
            WHERE p.category_l1 = %s AND m.match_method = 'embedding_clip'
        )
    """, (cl1,))
    
    matches = run_matching(cl1)
    for aid, bid, sc in matches:
        execute(
            "INSERT INTO matches (product_a_id, product_b_id, confidence, match_method) VALUES (%s, %s, %s, 'embedding_clip')",
            (int(aid), int(bid), float(sc)))
    if matches:
        print(f'  {cl1:20s} {len(matches)} matches')
    total += len(matches)

print(f'\nTotal new matches: {total}')

# Final summary
r = query("SELECT COUNT(*) as cnt FROM matches")
r2 = query("SELECT COUNT(*) as cnt FROM products WHERE is_active=true")
r3 = query("SELECT COUNT(*) as cnt FROM products WHERE is_active=true AND sales_30d IS NOT NULL")
print(f'\nFINAL: {r2[0]["cnt"]} produtos | {r3[0]["cnt"]} sales ({r3[0]["cnt"]*100//r2[0]["cnt"]}%) | {r[0]["cnt"]} matches')
