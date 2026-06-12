#!/usr/bin/env python3
"""Matching v6 — CLIP embedding cosine similarity. Intra-L3 matching."""
import sys
sys.path.insert(0, '.')
from scripts.db import query, execute

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
    
    print(f'  Pairs: {len(all_scores)}, deduped: {len(final)}')
    for i, (aid, bid, sc, diff, at, bt, ap, bp, a_pid, b_pid) in enumerate(final):
        print(f'  {i+1}. sim:{sc:.0f}% | R${ap:.0f} vs R${bp:.0f} (diff R${diff:.0f}) | {a_pid} vs {b_pid}')
    return final

# Main: run per L3 subcategory
print(f"Matching v6 — CLIP embeddings + intra-L3 (threshold {THRESHOLD*100:.0f}%)\n")

execute("DELETE FROM matches WHERE match_method LIKE 'embedding_%'")
total = 0

# Get all L3 categories with both platforms
l3_cats = query("""
    SELECT a.category, a.category_l3
    FROM products a JOIN products m ON a.category = m.category AND a.category_l3 = m.category_l3
    WHERE a.platform='amazon_br' AND m.platform='ml'
      AND a.embedding IS NOT NULL AND m.embedding IS NOT NULL
    GROUP BY a.category, a.category_l3
    ORDER BY a.category, a.category_l3
""")

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
print(f"Total matches: {total}")
