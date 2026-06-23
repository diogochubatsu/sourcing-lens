#!/usr/bin/env python3
"""
classify_products.py — Classify products into 4-level taxonomy.

Uses:
- N1-N2: Keyword matching from taxonomy table
- N3: Keyword matching + CLIP disambiguation
- N4: CLIP zero-shot within N3 candidates (≤8 options)

Usage:
  python3 classify_products.py --all           # Classify all products
  python3 classify_products.py --limit 100     # Classify first 100
  python3 classify_products.py --validate      # Check accuracy
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def get_pg_conn():
    import psycopg2
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL not set")
    return psycopg2.connect(database_url)

def load_taxonomy():
    """Load taxonomy from PostgreSQL into memory."""
    conn = get_pg_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT slug, level, parent_slug, name_pt, keywords FROM taxonomy WHERE is_active = true ORDER BY level, slug")
    rows = cursor.fetchall()
    conn.close()

    taxonomy = {}
    children = {}
    for slug, level, parent, name_pt, keywords in rows:
        taxonomy[slug] = {
            'slug': slug,
            'level': level,
            'parent': parent,
            'name': name_pt,
            'keywords': keywords or [],
        }
        if parent:
            children.setdefault(parent, []).append(slug)

    return taxonomy, children


def keyword_classify(title, candidates, taxonomy):
    """Classify using keyword matching against candidate slugs."""
    name = (title or '').lower()
    scores = {}

    for slug in candidates:
        kw_list = taxonomy.get(slug, {}).get('keywords', [])
        score = sum(1 for kw in kw_list if kw in name)
        if score > 0:
            scores[slug] = score

    if scores:
        best = max(scores, key=scores.get)
        return best, min(1.0, scores[best] / 3)
    return None, 0.0


def classify_n1(title, taxonomy, n1_slugs, embedding=None):
    """Classify N1 using keyword matching + CLIP fallback."""
    # Try keywords first
    result, score = keyword_classify(title, n1_slugs, taxonomy)
    if result:
        return result, score
    
    # CLIP fallback (if embedding available)
    if embedding is not None and len(n1_slugs) <= 20:
        try:
            import numpy as np
            from transformers import CLIPModel, CLIPProcessor
            
            # Parse embedding if it's a string
            if isinstance(embedding, str):
                embedding = np.array([float(x) for x in embedding.strip('[]').split(',')], dtype=np.float32)
            
            model_name = "openai/clip-vit-base-patch32"
            model = CLIPModel.from_pretrained(model_name, use_safetensors=True)
            processor = CLIPProcessor.from_pretrained(model_name)
            
            labels = [taxonomy[c]['name'] for c in n1_slugs]
            text_inputs = processor(text=labels, return_tensors='pt', padding=True, truncation=True)
            text_features = model.get_text_features(**text_inputs)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            emb = embedding / np.linalg.norm(embedding)
            similarities = np.dot(text_features.detach().numpy(), emb)
            
            idx = int(np.argmax(similarities))
            confidence = float(similarities[idx])
            
            if confidence >= 0.20:
                return n1_slugs[idx], confidence
        except Exception:
            pass
    
    return None, 0.0


def classify_n2(title, n1_slug, taxonomy, children, embedding=None):
    """Classify N2 within N1 scope using keywords + CLIP."""
    n2_candidates = children.get(n1_slug, [])
    if not n2_candidates:
        return None, 0.0
    
    # Try keyword matching first
    result, score = keyword_classify(title, n2_candidates, taxonomy)
    if result:
        return result, score
    
    # If no keyword match and embedding available, use CLIP zero-shot
    if embedding is not None and len(n2_candidates) <= 8:
        try:
            import numpy as np
            from transformers import CLIPModel, CLIPProcessor
            
            # Parse embedding if it's a string
            if isinstance(embedding, str):
                embedding = np.array([float(x) for x in embedding.strip('[]').split(',')], dtype=np.float32)
            
            model_name = "openai/clip-vit-base-patch32"
            model = CLIPModel.from_pretrained(model_name, use_safetensors=True)
            processor = CLIPProcessor.from_pretrained(model_name)
            
            labels = [taxonomy[c]['name'] for c in n2_candidates]
            text_inputs = processor(text=labels, return_tensors='pt', padding=True, truncation=True)
            text_features = model.get_text_features(**text_inputs)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            emb = embedding / np.linalg.norm(embedding)
            similarities = np.dot(text_features.detach().numpy(), emb)
            
            idx = int(np.argmax(similarities))
            confidence = float(similarities[idx])
            
            if confidence >= 0.15:
                return n2_candidates[idx], confidence
        except Exception:
            pass
    
    return None, 0.0


def classify_n3(title, n1_slug, n2_slug, taxonomy, children, embedding=None):
    """Classify N3 within N2 scope using keywords + CLIP."""
    n3_candidates = children.get(n2_slug, [])
    if not n3_candidates:
        return None, 0.0
    
    # Try keyword matching first
    result, score = keyword_classify(title, n3_candidates, taxonomy)
    if result:
        return result, score
    
    # If no keyword match and embedding available, use CLIP zero-shot
    if embedding is not None and len(n3_candidates) <= 8:
        try:
            import numpy as np
            from transformers import CLIPModel, CLIPProcessor
            
            # Parse embedding if it's a string
            if isinstance(embedding, str):
                embedding = np.array([float(x) for x in embedding.strip('[]').split(',')], dtype=np.float32)
            
            model_name = "openai/clip-vit-base-patch32"
            model = CLIPModel.from_pretrained(model_name, use_safetensors=True)
            processor = CLIPProcessor.from_pretrained(model_name)
            
            labels = [taxonomy[c]['name'] for c in n3_candidates]
            text_inputs = processor(text=labels, return_tensors='pt', padding=True, truncation=True)
            text_features = model.get_text_features(**text_inputs)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            emb = embedding / np.linalg.norm(embedding)
            similarities = np.dot(text_features.detach().numpy(), emb)
            
            idx = int(np.argmax(similarities))
            confidence = float(similarities[idx])
            
            if confidence >= 0.15:
                return n3_candidates[idx], confidence
        except Exception:
            pass
    
    return None, 0.0


def classify_n4_clip(embedding, n3_slug, taxonomy, children):
    """Classify N4 using CLIP zero-shot within N3 scope."""
    n4_candidates = children.get(n3_slug, [])
    if not n4_candidates or len(n4_candidates) > 8:
        return None, 0.0

    try:
        import numpy as np

        # Load CLIP model
        from transformers import CLIPModel, CLIPProcessor
        model_name = "openai/clip-vit-base-patch32"
        model = CLIPModel.from_pretrained(model_name)
        processor = CLIPProcessor.from_pretrained(model_name)

        labels = [taxonomy[c]['name'] for c in n4_candidates]

        # Encode labels
        text_inputs = processor(text=labels, return_tensors='pt', padding=True, truncation=True)
        text_features = model.get_text_features(**text_inputs)
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)

        # Embedding is already normalized
        emb = embedding / np.linalg.norm(embedding)

        # Cosine similarity
        similarities = np.dot(text_features.detach().numpy(), emb)

        idx = int(np.argmax(similarities))
        confidence = float(similarities[idx])

        if confidence < 0.20:
            return None, confidence

        return n4_candidates[idx], confidence
    except Exception:
        return None, 0.0


def classify_product(title, embedding, taxonomy, children):
    """Full 4-level classification."""
    n1_slugs = [s for s, t in taxonomy.items() if t['level'] == 1]

    # N1
    n1, c1 = classify_n1(title, taxonomy, n1_slugs, embedding)
    if not n1:
        n1 = 'uncategorized'

    # N2 (with CLIP fallback)
    n2, c2 = classify_n2(title, n1, taxonomy, children, embedding)
    if not n2:
        return {'n1': n1, 'n2': None, 'n3': None, 'n4': None}

    # N3 (with CLIP fallback)
    n3, c3 = classify_n3(title, n1, n2, taxonomy, children, embedding)
    if not n3:
        return {'n1': n1, 'n2': n2, 'n3': None, 'n4': None}

    # N4 (CLIP if embedding available)
    n4 = None
    if embedding is not None:
        n4, c4 = classify_n4_clip(embedding, n3, taxonomy, children)

    return {'n1': n1, 'n2': n2, 'n3': n3, 'n4': n4}


def reclassify_products(limit=None):
    """Re-classify all products in PostgreSQL."""
    import numpy as np

    def _blob_to_embedding(blob):
        """Convert binary blob to numpy array."""
        import struct
        if not blob:
            return None
        if isinstance(blob, memoryview):
            blob = bytes(blob)
        count = len(blob) // 4
        return np.array(struct.unpack(f'{count}f', blob[:count * 4]), dtype=np.float32)

    print("Loading taxonomy...")
    taxonomy, children = load_taxonomy()
    n1_slugs = [s for s, t in taxonomy.items() if t['level'] == 1]
    print(f"  Taxonomy: {len(taxonomy)} categories, {len(n1_slugs)} N1")

    conn = get_pg_conn()
    cursor = conn.cursor()

    # Get products to classify
    query = """
        SELECT id, title, image_embedding
        FROM arbitlens_products
        WHERE is_active = true
        ORDER BY id
    """
    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    products = cursor.fetchall()
    print(f"  Products to classify: {len(products)}")

    classified = 0
    updated = 0
    start = time.time()

    for prod_id, title, emb_blob in products:
        # Parse embedding
        embedding = None
        if emb_blob:
            try:
                if isinstance(emb_blob, memoryview):
                    emb_blob = bytes(emb_blob)
                embedding = np.frombuffer(emb_blob, dtype=np.float32)
            except Exception:
                pass

        # Classify
        result = classify_product(title, embedding, taxonomy, children)

        # Build path from taxonomy
        path = result['n4'] or result['n3'] or result['n2'] or result['n1'] or ''

        # Update database
        cursor.execute("""
            UPDATE arbitlens_products
            SET category = %s, category_n2 = %s, category_n3 = %s, category_n4 = %s, category_path = %s
            WHERE id = %s
        """, (result['n1'], result['n2'], result['n3'], result['n4'], path, prod_id))

        classified += 1
        if classified % 100 == 0:
            conn.commit()
            elapsed = time.time() - start
            rate = classified / elapsed if elapsed > 0 else 0
            print(f"  [{classified}/{len(products)}] classified in {elapsed:.0f}s ({rate:.0f}/s)")

    conn.commit()
    conn.close()

    elapsed = time.time() - start
    print(f"\n✅ Classification complete: {classified} products in {elapsed:.0f}s")


def validate_classification():
    """Check classification accuracy by level."""
    conn = get_pg_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(CASE WHEN category IS NOT NULL THEN 1 END) as n1,
            COUNT(CASE WHEN category_n2 IS NOT NULL THEN 1 END) as n2,
            COUNT(CASE WHEN category_n3 IS NOT NULL THEN 1 END) as n3,
            COUNT(CASE WHEN category_n4 IS NOT NULL THEN 1 END) as n4,
            COUNT(*) as total
        FROM arbitlens_products WHERE is_active = true
    """)
    row = cursor.fetchone()
    n1, n2, n3, n4, total = row

    print(f"\n=== Classification Coverage ===")
    print(f"  N1: {n1}/{total} ({n1/total*100:.1f}%)")
    print(f"  N2: {n2}/{total} ({n2/total*100:.1f}%)")
    print(f"  N3: {n3}/{total} ({n3/total*100:.1f}%)")
    print(f"  N4: {n4}/{total} ({n4/total*100:.1f}%)")

    # Top categories
    print(f"\n=== Top N1 Categories ===")
    cursor.execute("""
        SELECT category, COUNT(*) as cnt
        FROM arbitlens_products WHERE is_active = true AND category IS NOT NULL
        GROUP BY category ORDER BY cnt DESC LIMIT 10
    """)
    for cat, cnt in cursor.fetchall():
        print(f"  {cat:20s} {cnt:5d}")

    print(f"\n=== Top N2 Categories ===")
    cursor.execute("""
        SELECT category_n2, COUNT(*) as cnt
        FROM arbitlens_products WHERE is_active = true AND category_n2 IS NOT NULL
        GROUP BY category_n2 ORDER BY cnt DESC LIMIT 10
    """)
    for cat, cnt in cursor.fetchall():
        print(f"  {cat:20s} {cnt:5d}")

    print(f"\n=== Top N3 Categories ===")
    cursor.execute("""
        SELECT category_n3, COUNT(*) as cnt
        FROM arbitlens_products WHERE is_active = true AND category_n3 IS NOT NULL
        GROUP BY category_n3 ORDER BY cnt DESC LIMIT 10
    """)
    for cat, cnt in cursor.fetchall():
        print(f"  {cat:20s} {cnt:5d}")

    conn.close()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Classify products')
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--limit', type=int)
    parser.add_argument('--validate', action='store_true')
    args = parser.parse_args()

    if args.validate:
        validate_classification()
    elif args.all or args.limit:
        reclassify_products(args.limit)
    else:
        print("Usage: python3 classify_products.py --all [--limit N] | --validate")


if __name__ == '__main__':
    main()
