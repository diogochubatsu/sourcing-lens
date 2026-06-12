"""Split Casa into proper L3 subcategories to fix matching."""
import sys, re
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query, execute

# Classify products into L3 subcategories
def classify_l3(title, platform_id):
    t = (title or '').lower()
    pid = (platform_id or '').lower()
    
    # Thermal cups / water bottles
    if any(w in t for w in ['copo termico', 'copo quencher', 'stanley', 'garrafa termica', 
                             'termolar', 'tumbler', 'aerolight', 'stay chill',
                             'garrafa de agua', 'garrafa térmica', 'copo de cerveja',
                             'quencher', 'protour']):
        return 'Copos Térmicos'
    
    # Food storage
    if any(w in t for w in ['pote hermetico', 'pote de vidro', 'tupperware', 'recipiente',
                             'kit pote', 'potes hermetic']):
        return 'Cozinha'
    
    # Organization
    if any(w in t for w in ['organizador', 'caixa organizadora', 'cesto', 'bambu',
                             'cabide', 'varal', 'lixeira', 'saco a vacuo',
                             'cesto de bambu', 'roupa suja']):
        return 'Organização'
    
    # Kitchen items
    if any(w in t for w in ['descanso para talher', 'pano de prato', 'toalha']):
        return 'Cozinha'
    
    # Default
    return 'Casa'

# Update all Casa products
products = query(
    "SELECT id, platform_id, title, category_l3 FROM products WHERE category_l1='Casa' AND is_active=true"
)
print(f'Classifying {len(products)} Casa products...')

updates = {'Copos Térmicos': 0, 'Cozinha': 0, 'Organização': 0, 'Casa': 0}
for p in products:
    new_l3 = classify_l3(p['title'], p['platform_id'])
    if new_l3 != p['category_l3']:
        execute("UPDATE products SET category_l3 = %s WHERE id = %s", (new_l3, p['id']))
        updates[new_l3] += 1

for k, v in updates.items():
    print(f'  {k}: {v}')

# Now re-run matching per L3
print('\n=== Re-running matching per L3 ===')

THRESHOLD = 0.70
def run_matching_l3(category, l3):
    br = query(
        "SELECT id, embedding FROM products WHERE platform='amazon_br' AND category_l1=%s AND category_l3=%s AND embedding IS NOT NULL",
        (category, l3))
    ml = query(
        "SELECT id, embedding FROM products WHERE platform='ml' AND category_l1=%s AND category_l3=%s AND embedding IS NOT NULL",
        (category, l3))
    if not br or not ml:
        return []
    
    all_scores = []
    for a in br:
        best = query("""
            SELECT id, 1 - (embedding <=> %s::vector) as sim
            FROM products WHERE platform='ml' AND category_l1=%s AND category_l3=%s AND embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector LIMIT 1
        """, (a['embedding'], category, l3, a['embedding']))
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

# Delete old Casa CLIP matches
execute("""
    DELETE FROM matches WHERE id IN (
        SELECT m.id FROM matches m JOIN products a ON m.product_a_id = a.id
        WHERE a.category_l1 = 'Casa' AND m.match_method = 'embedding_clip'
    )
""")

# Run matching for each L3
total = 0
for l3 in ['Copos Térmicos', 'Cozinha', 'Organização']:
    matches = run_matching_l3('Casa', l3)
    for aid, bid, sc in matches:
        execute(
            "INSERT INTO matches (product_a_id, product_b_id, confidence, match_method) VALUES (%s, %s, %s, 'embedding_clip')",
            (int(aid), int(bid), float(sc)))
    print(f'  {l3}: {len(matches)} matches')
    total += len(matches)

print(f'Total new Casa matches: {total}')
