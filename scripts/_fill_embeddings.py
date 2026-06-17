#!/usr/bin/env python3
"""Generate CLIP embeddings for products missing them.

Features:
  - Batch encoding (32 images at once for ~10x speedup)
  - HTTP retry with exponential backoff
  - Embedding validation (dimension, non-zero)
  - Supports both HTTP URLs and local /images/ paths
"""
import sys, os, time, requests
from io import BytesIO
from PIL import Image
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query, execute
from sentence_transformers import SentenceTransformer

BATCH_SIZE = 32
MAX_RETRIES = 3
RETRY_DELAY = 2.0


def fetch_image(url, retries=MAX_RETRIES):
    """Fetch image from URL with retry and backoff."""
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                return Image.open(BytesIO(r.content)).convert('RGB')
            if r.status_code == 404:
                return None
            time.sleep(RETRY_DELAY * (attempt + 1))
        except (requests.RequestException, Exception):
            time.sleep(RETRY_DELAY * (attempt + 1))
    return None


def load_image(url_or_path):
    """Load image from HTTP URL or local path."""
    if not url_or_path or not isinstance(url_or_path, str):
        return None
    if url_or_path.startswith('http'):
        return fetch_image(url_or_path)
    elif url_or_path.startswith('/images/'):
        local_path = '/mnt/ssd/arbitlens/data' + url_or_path
        if os.path.exists(local_path):
            try:
                return Image.open(local_path).convert('RGB')
            except Exception:
                return None
    return None


def validate_embedding(emb):
    """Check that embedding is valid (non-zero, correct dimension)."""
    import numpy as np
    arr = np.array(emb)
    if arr.shape != (512,):
        return False
    if np.all(arr == 0):
        return False
    return True


def main():
    model = SentenceTransformer('clip-ViT-B-32')

    products = query(
        "SELECT id, platform_id, image_urls FROM products "
        "WHERE is_active=true AND embedding IS NULL"
    )
    print(f'Missing embeddings: {len(products)}')

    # Load images in batches
    batch_ids = []
    batch_images = []
    done = 0
    failed = 0

    for p in products:
        urls = p['image_urls'] or []
        url = urls[0] if urls else ''

        img = load_image(url)
        if img is None:
            failed += 1
            continue

        batch_ids.append(p['id'])
        batch_images.append(img)

        if len(batch_images) >= BATCH_SIZE:
            embeddings = model.encode(batch_images)
            for pid, emb in zip(batch_ids, embeddings):
                if validate_embedding(emb):
                    execute("UPDATE products SET embedding = %s::vector WHERE id = %s",
                            (emb.tolist(), pid))
                    done += 1
                else:
                    failed += 1
                    print(f'  WARN: Invalid embedding for product {pid}')
            batch_ids.clear()
            batch_images.clear()
            print(f'  {done} embeddings generated...')

    # Process remaining
    if batch_images:
        embeddings = model.encode(batch_images)
        for pid, emb in zip(batch_ids, embeddings):
            if validate_embedding(emb):
                execute("UPDATE products SET embedding = %s::vector WHERE id = %s",
                        (emb.tolist(), pid))
                done += 1
            else:
                failed += 1
                print(f'  WARN: Invalid embedding for product {pid}')

    print(f'\nGenerated: {done}, Failed: {failed}')

    remaining = query(
        "SELECT COUNT(*) as c FROM products WHERE is_active=true AND embedding IS NULL"
    )
    print(f'Remaining without embeddings: {remaining[0]["c"]}')


if __name__ == '__main__':
    main()
