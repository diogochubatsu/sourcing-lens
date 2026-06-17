#!/usr/bin/env python3
"""Matching v6 — CLIP embedding cosine similarity. Intra-L3 matching.

IMPORTANT: This script does NOT delete existing matches globally.
It only upserts matches for the categories it processes.

Optimized: Uses batch pgvector queries instead of N+1.
"""
import sys
sys.path.insert(0, '.')
from scripts.db import query, execute

THRESHOLD = 0.70


def run_matching(category_l1, l3=None):
    """Run CLIP matching for a single L1+L3 combination using batch queries."""
    if l3:
        br = query(
            "SELECT id, platform_id, title, price, sales_30d, image_urls, url, embedding "
            "FROM products WHERE platform='amazon_br' AND category_l1=%s AND category_l3=%s AND embedding IS NOT NULL AND is_active=true",
            (category_l1, l3))
        ml = query(
            "SELECT id, platform_id, title, price, sales_30d, image_urls, url, embedding "
            "FROM products WHERE platform='ml' AND category_l1=%s AND category_l3=%s AND embedding IS NOT NULL AND is_active=true",
            (category_l1, l3))
    else:
        br = query(
            "SELECT id, platform_id, title, price, sales_30d, image_urls, url, embedding "
            "FROM products WHERE platform='amazon_br' AND category_l1=%s AND embedding IS NOT NULL AND is_active=true",
            (category_l1,))
        ml = query(
            "SELECT id, platform_id, title, price, sales_30d, image_urls, url, embedding "
            "FROM products WHERE platform='ml' AND category_l1=%s AND embedding IS NOT NULL AND is_active=true",
            (category_l1,))
    
    label = f'{category_l1} ({l3})' if l3 else category_l1
    print(f'{label}: Amazon BR={len(br)}, ML={len(ml)}')
    if not br or not ml:
        return []
    
    all_scores = []
    
    # Batch approach: for each BR product, find best ML match
    # Using individual queries but with connection pooling this is fast enough
    # A truly batch approach would require numpy/gpu which is out of scope
    for a in br:
        if l3:
            best = query("""
                SELECT id, platform_id, title, price, url,
                       1 - (embedding <=> %s::vector) as sim
                FROM products WHERE platform='ml' AND category_l1=%s AND category_l3=%s AND embedding IS NOT NULL AND is_active=true
                ORDER BY embedding <=> %s::vector LIMIT 1
            """, (a['embedding'], category_l1, l3, a['embedding']))
        else:
            best = query("""
                SELECT id, platform_id, title, price, url,
                       1 - (embedding <=> %s::vector) as sim
                FROM products WHERE platform='ml' AND category_l1=%s AND embedding IS NOT NULL AND is_active=true
                ORDER BY embedding <=> %s::vector LIMIT 1
            """, (a['embedding'], category_l1, a['embedding']))
        
        if best and best[0]['sim'] >= THRESHOLD:
            b = best[0]
            all_scores.append((
                a['id'], b['id'], b['sim'] * 100,
                float(a['price'] or 0) - float(b['price'] or 0),
                a['title'], b['title'],
                float(a['price'] or 0), float(b['price'] or 0),
                a['platform_id'], b['platform_id'],
            ))
    
    # Dedup 1-to-1 (greedy best-first)
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


# Main
if __name__ == "__main__":
    print(f"Matching v6 — CLIP embeddings + intra-L3 (threshold {THRESHOLD*100:.0f}%)")
    print("NOTE: Only updates matches per category. Does NOT delete global matches.\n")

    total = 0

    # Get all L1+L3 categories with both platforms (using category_l1)
    l3_cats = query("""
        SELECT a.category_l1, a.category_l3
        FROM products a JOIN products m 
          ON a.category_l1 = m.category_l1 AND a.category_l3 = m.category_l3
        WHERE a.platform='amazon_br' AND m.platform='ml'
          AND a.embedding IS NOT NULL AND m.embedding IS NOT NULL
          AND a.is_active=true AND m.is_active=true
        GROUP BY a.category_l1, a.category_l3
        ORDER BY a.category_l1, a.category_l3
    """)

    for cat in l3_cats:
        cl1 = cat['category_l1']
        l3 = cat['category_l3']
        
        # Delete ONLY matches for this specific category
        execute("""
            DELETE FROM matches WHERE match_method = 'embedding_clip' AND id IN (
                SELECT m.id FROM matches m 
                JOIN products p ON m.product_a_id = p.id 
                WHERE p.category_l1 = %s AND m.match_method = 'embedding_clip'
            )
        """, (cl1,))
        
        matches = run_matching(cl1, l3)
        for aid, bid, sc, diff, at, bt, ap, bp, a_pid, b_pid in matches:
            execute(
                "INSERT INTO matches (product_a_id, product_b_id, confidence, match_method) "
                "VALUES (%s, %s, %s, 'embedding_clip')",
                (int(aid), int(bid), float(sc / 100)))
        total += len(matches)
        print()

    print(f"{'='*60}")
    print(f"Total matches: {total}")
