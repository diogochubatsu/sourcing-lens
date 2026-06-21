"""Run BR↔US matching for categories that lack ML data.

This complements matching_v6.py (BR↔ML) by matching BR↔US for new categories
like Beleza, Brinquedos, Bebê that have both Amazon BR and US but no ML data.
"""
import sys
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query, execute

THRESHOLD = 0.70  # Same as matching_v6.py


def run_br_us_matching(category_l1, l3=None):
    """Match Amazon BR products with Amazon US products in the same category."""
    if l3:
        br = query(
            "SELECT id, platform_id, title, price, sales_30d, image_urls, url, embedding "
            "FROM products WHERE platform='amazon_br' AND category_l1=%s AND category_l3=%s "
            "AND embedding IS NOT NULL AND is_active=true",
            (category_l1, l3))
        us = query(
            "SELECT id, platform_id, title, price, sales_30d, image_urls, url, embedding "
            "FROM products WHERE platform='amazon_us' AND category_l1=%s AND category_l3=%s "
            "AND embedding IS NOT NULL AND is_active=true",
            (category_l1, l3))
    else:
        br = query(
            "SELECT id, platform_id, title, price, sales_30d, image_urls, url, embedding "
            "FROM products WHERE platform='amazon_br' AND category_l1=%s "
            "AND embedding IS NOT NULL AND is_active=true",
            (category_l1,))
        us = query(
            "SELECT id, platform_id, title, price, sales_30d, image_urls, url, embedding "
            "FROM products WHERE platform='amazon_us' AND category_l1=%s "
            "AND embedding IS NOT NULL AND is_active=true",
            (category_l1,))

    label = f'{category_l1} ({l3})' if l3 else category_l1
    print(f'{label}: Amazon BR={len(br)}, US={len(us)}')
    if not br or not us:
        return []

    all_scores = []

    for a in br:
        if l3:
            best = query("""
                SELECT id, platform_id, title, price, url,
                       1 - (embedding <=> %s::vector) as sim
                FROM products WHERE platform='amazon_us' AND category_l1=%s AND category_l3=%s
                AND embedding IS NOT NULL AND is_active=true
                ORDER BY embedding <=> %s::vector LIMIT 1
            """, (a['embedding'], category_l1, l3, a['embedding']))
        else:
            best = query("""
                SELECT id, platform_id, title, price, url,
                       1 - (embedding <=> %s::vector) as sim
                FROM products WHERE platform='amazon_us' AND category_l1=%s
                AND embedding IS NOT NULL AND is_active=true
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

    # Dedup 1-to-1
    all_scores.sort(key=lambda x: x[2], reverse=True)
    seen_br, seen_us, final = set(), set(), []
    for m in all_scores:
        if m[0] not in seen_br and m[1] not in seen_us:
            seen_br.add(m[0])
            seen_us.add(m[1])
            final.append(m)

    print(f'  Pairs: {len(all_scores)}, deduped 1-to-1: {len(final)}')
    return final


if __name__ == '__main__':
    print(f"BR↔US Matching — CLIP embeddings (threshold {THRESHOLD*100:.0f}%)\n")

    total = 0
    # Categories that have both BR and US but no ML
    new_categories = ['Beleza', 'Brinquedos', 'Bebê']

    for cat_l1 in new_categories:
        matches = run_br_us_matching(cat_l1)
        for aid, bid, sc, diff, at, bt, ap, bp, a_pid, b_pid in matches:
            execute(
                "INSERT INTO matches (product_a_id, product_b_id, confidence, match_method) "
                "VALUES (%s, %s, %s, 'embedding_clip_br_us')",
                (int(aid), int(bid), float(sc / 100))
            )
            total += 1
            print(f"  {sc:.0f}% | {a_pid} (R${ap:.0f}) ↔ {b_pid} (${bp:.0f})")
        print()

    print(f"{'='*60}")
    print(f"Total BR↔US matches: {total}")
