#!/usr/bin/env python3
"""Matching v7 — CLIP embedding cosine similarity. Multi-platform intra-L3 matching.

Matches products across platforms using CLIP image embeddings:
  - Amazon BR ↔ ML
  - Amazon US ↔ ML
  - Amazon US ↔ Amazon BR

IMPORTANT: This script does NOT delete existing matches globally.
It only upserts matches for the categories it processes.
"""
import sys
sys.path.insert(0, '.')
from scripts.db import query, execute

THRESHOLD = 0.70

PLATFORM_PAIRS = [
    ('amazon_br', 'ml'),
    ('amazon_us', 'ml'),
    ('amazon_us', 'amazon_br'),
]


def find_best_match(product_embedding, target_platform, category_l1, category_l3=None):
    """Find the best matching product in target_platform by cosine similarity."""
    if category_l3:
        return query("""
            SELECT id, platform_id, title, price, url,
                   1 - (embedding <=> %s::vector) as sim
            FROM products
            WHERE platform=%s AND category_l1=%s AND category_l3=%s
              AND embedding IS NOT NULL AND is_active=true
            ORDER BY embedding <=> %s::vector LIMIT 1
        """, (product_embedding, target_platform, category_l1, category_l3, product_embedding))
    else:
        return query("""
            SELECT id, platform_id, title, price, url,
                   1 - (embedding <=> %s::vector) as sim
            FROM products
            WHERE platform=%s AND category_l1=%s
              AND embedding IS NOT NULL AND is_active=true
            ORDER BY embedding <=> %s::vector LIMIT 1
        """, (product_embedding, target_platform, category_l1, product_embedding))


def run_matching(source_platform, target_platform, category_l1, category_l3=None):
    """Run CLIP matching for a single platform pair + L1+L3 combination."""
    where_source = "platform=%s AND category_l1=%s AND embedding IS NOT NULL AND is_active=true"
    params_source = [source_platform, category_l1]
    if category_l3:
        where_source += " AND category_l3=%s"
        params_source.append(category_l3)

    source_products = query(
        f"SELECT id, platform_id, title, price, sales_30d, image_urls, url, embedding "
        f"FROM products WHERE {where_source}",
        tuple(params_source)
    )

    label = f'{category_l1} ({category_l3})' if category_l3 else category_l1
    print(f'  {source_platform} → {target_platform} | {label}: {len(source_products)} source products')
    if not source_products:
        return []

    all_scores = []
    for p in source_products:
        best = find_best_match(p['embedding'], target_platform, category_l1, category_l3)
        if best and best[0]['sim'] >= THRESHOLD:
            b = best[0]
            all_scores.append((
                p['id'], b['id'], b['sim'] * 100,
                float(p['price'] or 0) - float(b['price'] or 0),
                p['title'], b['title'],
                float(p['price'] or 0), float(b['price'] or 0),
                p['platform_id'], b['platform_id'],
            ))

    # Sort by confidence DESC, then greedy 1-to-1 dedup
    all_scores.sort(key=lambda x: x[2], reverse=True)
    seen_source = set()
    seen_target = set()
    final = []
    for m in all_scores:
        if m[0] not in seen_source and m[1] not in seen_target:
            seen_source.add(m[0])
            seen_target.add(m[1])
            final.append(m)

    print(f'    Pairs: {len(all_scores)}, deduped 1-to-1: {len(final)}')
    for i, (aid, bid, sc, diff, at, bt, ap, bp, a_pid, b_pid) in enumerate(final):
        print(f'    {i+1}. sim:{sc:.0f}% | ${ap:.0f} vs ${bp:.0f} (diff ${diff:.0f}) | {a_pid} vs {b_pid}')
    return final


# Main
print(f"Matching v7 — CLIP embeddings + multi-platform intra-L3 (threshold {THRESHOLD*100:.0f}%)")
print(f"Platform pairs: {', '.join(f'{s}→{t}' for s, t in PLATFORM_PAIRS)}")
print("NOTE: Only updates matches per category. Does NOT delete global matches.\n")

grand_total = 0

for source_platform, target_platform in PLATFORM_PAIRS:
    print(f"\n{'='*60}")
    print(f"  {source_platform} → {target_platform}")
    print(f"{'='*60}")

    # Find L3 categories where both platforms have products with embeddings
    l3_cats = query("""
        SELECT a.category_l1, a.category_l3
        FROM products a JOIN products b
          ON a.category_l1 = b.category_l1 AND a.category_l3 = b.category_l3
        WHERE a.platform=%s AND b.platform=%s
          AND a.embedding IS NOT NULL AND b.embedding IS NOT NULL
          AND a.is_active=true AND b.is_active=true
        GROUP BY a.category_l1, a.category_l3
        ORDER BY a.category_l1, a.category_l3
    """, (source_platform, target_platform))

    pair_total = 0
    for cat in l3_cats:
        cl1 = cat['category_l1']
        l3 = cat['category_l3']

        # Delete ONLY matches for this specific source platform + category
        execute("""
            DELETE FROM matches WHERE match_method = 'embedding_clip' AND id IN (
                SELECT m.id FROM matches m
                JOIN products p ON m.product_a_id = p.id
                WHERE p.category_l1 = %s AND p.platform = %s AND m.match_method = 'embedding_clip'
            )
        """, (cl1, source_platform))

        matches = run_matching(source_platform, target_platform, cl1, l3)
        for aid, bid, sc, diff, at, bt, ap, bp, a_pid, b_pid in matches:
            execute(
                "INSERT INTO matches (product_a_id, product_b_id, confidence, match_method) "
                "VALUES (%s, %s, %s, 'embedding_clip')",
                (int(aid), int(bid), float(sc / 100)))
        pair_total += len(matches)
        print()

    print(f"  Subtotal: {pair_total}")
    grand_total += pair_total

print(f"\n{'='*60}")
print(f"Grand total matches: {grand_total}")
