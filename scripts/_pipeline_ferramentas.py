"""Generate CLIP embeddings for Ferramentas products and run matching."""
import sys, os, time
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query, execute
from sentence_transformers import SentenceTransformer
import requests
from PIL import Image
from io import BytesIO

# 1. Fix category column for matching_v6
print('=== Step 1: Updating category column ===')
execute("UPDATE products SET category = category_l1 WHERE category_l1 IS NOT NULL AND (category IS NULL OR category = '')")
affected = execute("UPDATE products SET category = 'Ferramentas' WHERE category_l1 = 'Ferramentas' AND category IS DISTINCT FROM 'Ferramentas'")
print(f'Fixed category for Ferramentas: {affected}')

# 2. Load CLIP model
print('\n=== Step 2: Loading CLIP model ===')
model = SentenceTransformer("clip-ViT-B-32")
print('Model loaded')

# 3. Generate embeddings for Ferramentas products
products = query(
    "SELECT id, platform_id, image_urls, category_l1 FROM products "
    "WHERE category_l1 = 'Ferramentas' AND is_active = true AND embedding IS NULL"
)
print(f'\n=== Step 3: Generating embeddings for {len(products)} products ===')

done = 0
errors = 0
for p in products:
    img_urls = p['image_urls'] or []
    img_url = img_urls[0] if img_urls else ''
    
    if not img_url:
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
        execute(
            "UPDATE products SET embedding = %s::vector WHERE id = %s",
            (emb_list, p['id'])
        )
        done += 1
        if done % 10 == 0:
            print(f'  {done}/{len(products)} embeddings generated...')
    except Exception as e:
        errors += 1
        if errors <= 5:
            print(f'  Error {p["platform_id"]}: {e}')

print(f'Done: {done} embeddings, {errors} errors')

# 4. Run matching_v6
print('\n=== Step 4: Running matching_v6 ===')
THRESHOLD = 0.70

def run_matching(category, l3=None):
    if l3:
        br = query(
            "SELECT id, platform_id, title, price, sales_30d, image_urls, url, embedding "
            "FROM products WHERE platform='amazon_br' AND category=%s AND category_l3=%s AND embedding IS NOT NULL",
            (category, l3))
        ml = query(
            "SELECT id, platform_id, title, price, sales_30d, image_urls, url, embedding "
            "FROM products WHERE platform='ml' AND category=%s AND category_l3=%s AND embedding IS NOT NULL",
            (category, l3))
    else:
        br = query(
            "SELECT id, platform_id, title, price, sales_30d, image_urls, url, embedding "
            "FROM products WHERE platform='amazon_br' AND category=%s AND embedding IS NOT NULL",
            (category,))
        ml = query(
            "SELECT id, platform_id, title, price, sales_30d, image_urls, url, embedding "
            "FROM products WHERE platform='ml' AND category=%s AND embedding IS NOT NULL",
            (category,))
    
    label = f'{category} ({l3})' if l3 else category
    print(f'{label}: Amazon BR={len(br)}, ML={len(ml)}')
    if not br or not ml:
        return []
    
    all_scores = []
    for a in br:
        if l3:
            best = query("""
                SELECT id, platform_id, title, price, url,
                       1 - (embedding <=> %s::vector) as sim
                FROM products WHERE platform='ml' AND category=%s AND category_l3=%s AND embedding IS NOT NULL
                ORDER BY embedding <=> %s::vector LIMIT 1
            """, (a['embedding'], category, l3, a['embedding']))
        else:
            best = query("""
                SELECT id, platform_id, title, price, url,
                       1 - (embedding <=> %s::vector) as sim
                FROM products WHERE platform='ml' AND category=%s AND embedding IS NOT NULL
                ORDER BY embedding <=> %s::vector LIMIT 1
            """, (a['embedding'], category, a['embedding']))
        
        if best and best[0]['sim'] >= THRESHOLD:
            b = best[0]
            all_scores.append((
                a['id'], b['id'], b['sim'] * 100,
                float(a['price'] or 0) - float(b['price'] or 0),
                a['title'], b['title'],
                float(a['price'] or 0), float(b['price'] or 0),
                a['platform_id'], b['platform_id'],
            ))
    
    all_scores.sort(key=lambda x: x[2], reverse=True)
    seen_br = set()
    seen_ml = set()
    final = []
    for m in all_scores:
        if m[0] not in seen_br and m[1] not in seen_ml:
            seen_br.add(m[0])
            seen_ml.add(m[1])
            final.append(m)
    
    print(f'  Pairs: {len(all_scores)}, deduped 1-to-1: {len(final)}')
    for i, (aid, bid, sc, diff, at, bt, ap, bp, a_pid, b_pid) in enumerate(final):
        print(f'  {i+1}. sim:{sc:.0f}% | R${ap:.0f} vs R${bp:.0f} (diff R${diff:.0f}) | {a_pid} vs {b_pid}')
    return final

# Clear old matches
execute("DELETE FROM matches WHERE match_method LIKE 'embedding_%'")
total = 0

# Get L3 categories with both platforms
l3_cats = query("""
    SELECT a.category, a.category_l3
    FROM products a JOIN products m ON a.category = m.category AND a.category_l3 = m.category_l3
    WHERE a.platform='amazon_br' AND m.platform='ml'
      AND a.embedding IS NOT NULL AND m.embedding IS NOT NULL
      AND a.category = 'Ferramentas'
    GROUP BY a.category, a.category_l3
    ORDER BY a.category, a.category_l3
""")

print(f'\nL3 categories found: {len(l3_cats)}')
for cat in l3_cats:
    matches = run_matching(cat['category'], cat['category_l3'])
    for aid, bid, sc, diff, at, bt, ap, bp, a_pid, b_pid in matches:
        execute(
            "INSERT INTO matches (product_a_id, product_b_id, confidence, match_method) "
            "VALUES (%s, %s, %s, 'embedding_clip')",
            (int(aid), int(bid), float(sc / 100)))
    total += len(matches)
    print()

print(f"{'='*60}")
print(f"Total matches for Ferramentas: {total}")

# Also run without L3 filter in case L3 is too granular
print(f'\n=== Running matching at L1 level (no L3 filter) ===')
matches = run_matching('Ferramentas')
for aid, bid, sc, diff, at, bt, ap, bp, a_pid, b_pid in matches:
    execute(
        "INSERT INTO matches (product_a_id, product_b_id, confidence, match_method) "
        "VALUES (%s, %s, %s, 'embedding_clip')",
        (int(aid), int(bid), float(sc / 100)))
total += len(matches)
print(f'\nGrand total matches: {total}')

# 5. Final summary
r = query("""
    SELECT COUNT(*) FROM matches m
    JOIN products a ON m.product_a_id = a.id
    JOIN products b ON m.product_b_id = b.id
    WHERE a.category_l1 = 'Ferramentas' OR b.category_l1 = 'Ferramentas'
""")
print(f'\nTotal matches in DB for Ferramentas: {r[0]["count"]}')
