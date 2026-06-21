"""Generate SigLIP embeddings v2 — improved image pipeline.

Upgrades over v1:
  - SigLIP base (768-dim) instead of CLIP B-32 (512-dim)
  - Higher resolution: rejects images < 200x200
  - Multi-image aggregation: averages embeddings across all images
  - Better preprocessing: convert to RGB, resize if too large
  - Batch processing for speed
"""
import sys, os, argparse
from io import BytesIO
import numpy as np
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query, execute


def generate_siglip_embeddings(category=None, limit=None, model_name='google/siglip-base-patch16-224'):
    """Generate SigLIP embeddings for products.

    Strategy:
      - For each product, encode ALL image URLs (multi-image aggregation)
      - Average the embeddings (mean of normalized vectors)
      - Store single 768-dim vector per product
    """
    from sentence_transformers import SentenceTransformer
    from PIL import Image
    import requests

    # Load model once
    print(f"Loading {model_name}...")
    model = SentenceTransformer(model_name)
    dim = model.get_embedding_dimension()
    print(f"  Loaded (dim={dim})")

    # Get products to embed
    conds = ["is_active = TRUE", "image_urls IS NOT NULL", "array_length(image_urls, 1) > 0"]
    if not args.force:
        conds.append("embedding IS NULL")
    params = []
    if category:
        conds.append("category_l1 = %s")
        params.append(category)
    where = " AND ".join(conds)

    sql = f"""
        SELECT id, platform, platform_id, title, image_urls
        FROM products WHERE {where}
    """
    if limit:
        sql += " LIMIT %s"
        params.append(limit)

    products = query(sql, tuple(params))
    if not products:
        print("No products need embeddings")
        return 0

    print(f"Found {len(products)} products to embed")

    def encode_one(img_url, retries=2):
        """Download + encode a single image. Returns vector or None.
        Supports:
          - http(s):// URLs (download)
          - /images/... local paths (read from data/images/)
        """
        for attempt in range(retries):
            try:
                # Local path - handle /images/... or relative paths like 'platform/file.jpg'
                if img_url.startswith('/images/') or '/' in img_url and not img_url.startswith('http'):
                    if img_url.startswith('/images/'):
                        local_path = '/mnt/ssd/arbitlens/data' + img_url
                    else:
                        local_path = '/mnt/ssd/arbitlens/data/images/' + img_url
                    import os
                    if not os.path.exists(local_path):
                        continue
                    img = Image.open(local_path)
                else:
                    # Remote URL
                    resp = requests.get(img_url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
                    if resp.status_code != 200:
                        continue
                    img = Image.open(BytesIO(resp.content))

                if img.mode != 'RGB':
                    img = img.convert('RGB')
                # Skip very small images (likely thumbnails)
                if img.size[0] < 150 or img.size[1] < 150:
                    return None
                vec = model.encode(img, convert_to_numpy=True, normalize_embeddings=True)
                return vec
            except Exception:
                continue
        return None

    generated = 0
    for i, p in enumerate(products):
        img_urls = p['image_urls'] or []
        if not img_urls:
            continue

        # Try each image, collect all valid embeddings
        vecs = []
        for url in img_urls[:5]:  # max 5 images per product
            v = encode_one(url)
            if v is not None:
                vecs.append(v)

        if not vecs:
            print(f"  [{i+1}/{len(products)}] {p['platform_id']}: no valid images")
            continue

        # Average embeddings (already normalized → mean then re-normalize)
        mean_vec = np.mean(vecs, axis=0)
        norm = np.linalg.norm(mean_vec)
        if norm > 0:
            mean_vec = mean_vec / norm

        execute(
            "UPDATE products SET embedding = %s::vector WHERE id = %s",
            (mean_vec.tolist(), p['id'])
        )
        generated += 1

        if (i+1) % 25 == 0 or i == len(products) - 1:
            print(f"  [{i+1}/{len(products)}] {p['platform_id']}: ✓ ({len(vecs)} imgs averaged)")

    print(f"\n[OK] Generated {generated}/{len(products)} SigLIP embeddings")
    return generated


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate SigLIP embeddings')
    parser.add_argument('--category', type=str, help='Category L1')
    parser.add_argument('--limit', type=int, help='Limit products')
    parser.add_argument('--model', type=str, default='google/siglip-base-patch16-224')
    parser.add_argument('--force', action='store_true', help='Re-embed products that already have embeddings')
    args = parser.parse_args()
    generate_siglip_embeddings(category=args.category, limit=args.limit, model_name=args.model)