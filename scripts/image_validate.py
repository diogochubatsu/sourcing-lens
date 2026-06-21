"""Image classification — verify product categories using prototype similarity.

For each category, compute the average embedding of all known-good products.
Then check new products against the prototype of their assigned category.

This is more robust than zero-shot because:
- It uses the actual data distribution
- Doesn't depend on text label quality
- Catches products that don't visually match their category
"""
import sys, os
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query
import numpy as np


def main():
    import torch
    print("Loading embeddings from DB...")

    # Get all active products with embeddings, grouped by category_l1
    rows = query("""
        SELECT id, title, category_l1, embedding::text as emb
        FROM products
        WHERE is_active=true AND embedding IS NOT NULL
    """)

    # Parse embeddings and group by category
    from collections import defaultdict
    cat_embs = defaultdict(list)
    for r in rows:
        # pgvector returns '[0.1, 0.2, ...]' format
        emb_str = r['emb']
        if emb_str and emb_str.startswith('['):
            try:
                emb = np.array([float(x) for x in emb_str.strip('[]').split(',')])
                cat_embs[r['category_l1']].append(emb)
            except Exception:
                pass

    print(f"Loaded {len(rows)} products in {len(cat_embs)} categories")

    # Compute prototype (centroid) for each category
    prototypes = {}
    for cat, embs in cat_embs.items():
        if len(embs) >= 3:  # need at least 3 products
            prototypes[cat] = np.mean(embs, axis=0)
            # Normalize
            prototypes[cat] = prototypes[cat] / np.linalg.norm(prototypes[cat])

    print(f"\nPrototypes for {len(prototypes)} categories:")
    for cat in sorted(prototypes.keys()):
        print(f"  {cat:25} {len(cat_embs[cat]):>3} products")

    # Verify each product against its category prototype
    print("\nVerifying products against their category prototype...")
    correct = 0
    total = 0
    mismatches = []
    for r in rows:
        if r['category_l1'] not in prototypes:
            continue
        emb_str = r['emb']
        if not emb_str or not emb_str.startswith('['):
            continue
        try:
            emb = np.array([float(x) for x in emb_str.strip('[]').split(',')])
            emb = emb / np.linalg.norm(emb)
        except Exception:
            continue

        actual_cat = r['category_l1']
        proto = prototypes[actual_cat]
        sim_actual = float(np.dot(emb, proto))

        # Find best matching category
        best_cat = max(prototypes.keys(), key=lambda c: float(np.dot(emb, prototypes[c])))
        best_sim = float(np.dot(emb, prototypes[best_cat]))

        total += 1
        if best_cat == actual_cat:
            correct += 1
        else:
            mismatches.append((r['id'], r['title'][:50], actual_cat, best_cat, sim_actual, best_sim))

        # If the image is VERY far from its category prototype, flag it
        if sim_actual < 0.5:  # low similarity to assigned category
            pass  # could flag this

    acc = 100 * correct / total if total else 0
    print(f"\n[OK] Prototype-based accuracy: {correct}/{total} = {acc:.0f}%")

    if mismatches:
        print(f"\nTop 15 mismatches (predicted ≠ actual):")
        for m in sorted(mismatches, key=lambda x: x[4])[:15]:  # sort by lowest sim to actual
            print(f"  {m[0]}: actual='{m[2]:18}' predicted='{m[3]:18}' sim_actual={m[4]:.3f} sim_pred={m[5]:.3f} {m[1]}")


if __name__ == '__main__':
    main()