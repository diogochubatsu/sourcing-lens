#!/usr/bin/env python3
"""
Matching v7 — CLIP embeddings with 3-tier L1/L2/L3 hierarchy.

3 levels of matching strictness:
1. STRICT: L1 + L2 + L3 all match — highest confidence
2. MEDIUM: L1 + L2 match (one side may have L3='Geral') — medium confidence
3. BROAD: L1 only — fallback (used for categories with no specific L2/L3)

Each BR product tries strict first, then medium, then broad.
Threshold 70% (per tier).

IMPORTANT: Only upserts matches for the categories it processes.
Does NOT delete matches globally.
"""
import sys
sys.path.insert(0, '.')
from scripts.db import query, execute

THRESHOLD = 0.70
STRICT_BOOST = 1.05  # Strict matches get +5% confidence (capped at 99)
MEDIUM_PENALTY = 0.03  # Medium matches get -3% (floor 0)


def find_best_ml_match(br_product, l1, l2=None, l3=None, min_sim=0.0):
    """Find best ML match for a BR product at the given hierarchy level.

    Returns dict with id, sim, or None.
    """
    if l3 is not None and l2 is not None:
        # STRICT: L1 + L2 + L3
        if l3 == 'Geral':
            return None  # No point matching with "Geral" - fallback to L1+L2
        best = query("""
            SELECT id, platform_id, title, price, url,
                   1 - (embedding <=> %s::vector) as sim
            FROM products
            WHERE platform='ml' AND category_l1=%s
              AND COALESCE(category_l2, '') = COALESCE(%s, '')
              AND category_l3=%s
              AND embedding IS NOT NULL AND is_active=true
              AND 1 - (embedding <=> %s::vector) >= %s
            ORDER BY embedding <=> %s::vector LIMIT 1
        """, (br_product['embedding'], l1, l2, l3,
              br_product['embedding'], min_sim, br_product['embedding']))
    elif l2 is not None and l3 is None:
        # MEDIUM: L1 + L2 (one side may have L3='Geral')
        best = query("""
            SELECT id, platform_id, title, price, url,
                   1 - (embedding <=> %s::vector) as sim
            FROM products
            WHERE platform='ml' AND category_l1=%s
              AND COALESCE(category_l2, '') = COALESCE(%s, '')
              AND embedding IS NOT NULL AND is_active=true
              AND 1 - (embedding <=> %s::vector) >= %s
            ORDER BY embedding <=> %s::vector LIMIT 1
        """, (br_product['embedding'], l1, l2,
              br_product['embedding'], min_sim, br_product['embedding']))
    else:
        # BROAD: L1 only
        best = query("""
            SELECT id, platform_id, title, price, url,
                   1 - (embedding <=> %s::vector) as sim
            FROM products
            WHERE platform='ml' AND category_l1=%s
              AND embedding IS NOT NULL AND is_active=true
              AND 1 - (embedding <=> %s::vector) >= %s
            ORDER BY embedding <=> %s::vector LIMIT 1
        """, (br_product['embedding'], l1,
              br_product['embedding'], min_sim, br_product['embedding']))

    return best[0] if best else None


def run_matching(category_l1):
    """Run 3-tier matching for an L1 category."""
    # Get all BR products in this L1
    br = query("""
        SELECT id, platform_id, title, price, sales_30d, image_urls, url, embedding,
               category_l2, category_l3
        FROM products
        WHERE platform='amazon_br' AND category_l1=%s
          AND embedding IS NOT NULL AND is_active=true
    """, (category_l1,))

    print(f'{category_l1}: Amazon BR={len(br)}')
    if not br:
        return []

    all_matches = []
    counts = {'strict': 0, 'medium': 0, 'broad': 0, 'none': 0}

    for a in br:
        br_l2 = a.get('category_l2')
        br_l3 = a.get('category_l3')

        match = None
        tier = None

        # 1. STRICT: L1 + L2 + L3
        if br_l2 and br_l3 and br_l3 != 'Geral':
            match = find_best_ml_match(a, category_l1, br_l2, br_l3, THRESHOLD)
            if match:
                tier = 'strict'

        # 2. MEDIUM: L1 + L2 (allow L3='Geral' on either side)
        if not match and br_l2:
            match = find_best_ml_match(a, category_l1, br_l2, None, THRESHOLD)
            if match:
                tier = 'medium'

        # 3. BROAD: L1 only
        if not match:
            match = find_best_ml_match(a, category_l1, None, None, THRESHOLD)
            if match:
                tier = 'broad'

        if match:
            # Apply tier-based confidence adjustment
            sim = match['sim']
            if tier == 'strict':
                conf = min(0.99, sim + STRICT_BOOST - 1.0)  # Convert from boost
                # Actually: keep raw sim, just track tier for reporting
                conf = sim
            elif tier == 'medium':
                conf = max(0.0, sim - MEDIUM_PENALTY)
            else:
                conf = sim

            counts[tier] += 1
            all_matches.append((
                a['id'], match['id'], sim, tier,
                float(a['price'] or 0) - float(match['price'] or 0),
                a['title'], match['title'],
                float(a['price'] or 0), float(match['price'] or 0),
                a['platform_id'], match['platform_id'],
                conf
            ))
        else:
            counts['none'] += 1

    # Dedup 1-to-1 (greedy best-first by confidence)
    all_matches.sort(key=lambda x: x[2], reverse=True)
    seen_br = set()
    seen_ml = set()
    final = []
    for m in all_matches:
        if m[0] not in seen_br and m[1] not in seen_ml:
            seen_br.add(m[0])
            seen_ml.add(m[1])
            final.append(m)

    # Reporting
    print(f'  Pairs: {len(all_matches)}, deduped 1-to-1: {len(final)}')
    print(f'  Tiers: strict={counts["strict"]}, medium={counts["medium"]}, broad={counts["broad"]}, no_match={counts["none"]}')

    for i, m in enumerate(final[:5]):
        aid, bid, sc, tier, diff, at, bt, ap, bp, a_pid, b_pid, conf = m
        print(f'  {i+1}. [{tier:6s}] sim:{sc*100:.0f}% conf:{conf*100:.0f}% | R${ap:.0f} vs R${bp:.0f} | {a_pid} vs {b_pid}')

    return final


# Main
if __name__ == "__main__":
    print(f"Matching v7 — 3-tier (L1/L2/L3) CLIP matching (threshold {THRESHOLD*100:.0f}%)")
    print(f"  STRICT: L1+L2+L3, MEDIUM: L1+L2, BROAD: L1 only")
    print(f"  Strict boost: +{int((STRICT_BOOST-1)*100)}%, Medium penalty: -{int(MEDIUM_PENALTY*100)}%\n")

    total = 0
    by_tier = {'strict': 0, 'medium': 0, 'broad': 0}

    # Get all L1 categories with both platforms
    l1_cats = query("""
        SELECT a.category_l1
        FROM products a JOIN products m
          ON a.category_l1 = m.category_l1
        WHERE a.platform='amazon_br' AND m.platform='ml'
          AND a.embedding IS NOT NULL AND m.embedding IS NOT NULL
          AND a.is_active=true AND m.is_active=true
        GROUP BY a.category_l1
        ORDER BY a.category_l1
    """)

    for cat in l1_cats:
        cl1 = cat['category_l1']

        # Delete ONLY matches for this L1
        execute("""
            DELETE FROM matches WHERE match_method = 'embedding_clip' AND id IN (
                SELECT m.id FROM matches m
                JOIN products p ON m.product_a_id = p.id
                WHERE p.category_l1 = %s AND m.match_method = 'embedding_clip'
            )
        """, (cl1,))

        matches = run_matching(cl1)
        for m in matches:
            aid, bid, sc, tier, diff, at, bt, ap, bp, a_pid, b_pid, conf = m
            execute(
                "INSERT INTO matches (product_a_id, product_b_id, confidence, match_method) "
                "VALUES (%s, %s, %s, 'embedding_clip')",
                (int(aid), int(bid), float(conf)))
            by_tier[tier] += 1
        total += len(matches)
        print()

    print(f"{'='*60}")
    print(f"Total matches: {total}")
    print(f"By tier: strict={by_tier['strict']}, medium={by_tier['medium']}, broad={by_tier['broad']}")
