#!/usr/bin/env python3
"""Generate CLIP embeddings for automotive_tool products using sentence-transformers."""
import sys
import time
import numpy as np

sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query, execute

# Use sentence-transformers with a multilingual CLIP model
from sentence_transformers import SentenceTransformer

def main():
    print("Loading CLIP model (multilingual)...", flush=True)
    model = SentenceTransformer('sentence-transformers/clip-ViT-B-32-multilingual-v1')
    print("Model loaded.", flush=True)
    
    # Get all automotive_tool products missing embeddings
    rows = query("""
        SELECT id, title, image_urls, platform, platform_id
        FROM products
        WHERE category = 'automotive_tool'
          AND embedding IS NULL
          AND image_urls IS NOT NULL
          AND array_length(image_urls, 1) > 0
        ORDER BY id
    """)
    
    print(f"Found {len(rows)} products without embeddings", flush=True)
    
    success = 0
    errors = 0
    
    for i, row in enumerate(rows):
        prod_id = row['id']
        title = row['title'] or ''
        image_url = row['image_urls'][0]
        pid = row['platform_id']
        plat = row['platform']
        
        print(f'  [{i+1}/{len(rows)}] {plat}/{pid}: {title[:50]}...', flush=True)
        
        try:
            # Download image
            import requests
            from io import BytesIO
            from PIL import Image
            
            resp = requests.get(image_url, timeout=30)
            resp.raise_for_status()
            img = Image.open(BytesIO(resp.content)).convert('RGB')
            
            # Generate embedding from title + image
            embedding = model.encode([title, img], show_progress_bar=False)
            # Average the two embeddings
            emb = np.mean(embedding, axis=0).astype(np.float32)
            
            # Store in DB
            execute(
                "UPDATE products SET embedding = %s::vector WHERE id = %s",
                (emb.tolist(), prod_id)
            )
            
            success += 1
            if (i + 1) % 10 == 0 or (i + 1) == len(rows):
                print(f'  Progress: {i+1}/{len(rows)} ({success} success, {errors} errors)', flush=True)
            
            time.sleep(1)  # Rate limit
        
        except Exception as e:
            print(f'  [ERROR] {plat}/{pid}: {e}', flush=True)
            errors += 1
    
    print(f'\n{"="*60}', flush=True)
    print(f'CLIP embedding generation complete: {success} success, {errors} errors', flush=True)


if __name__ == '__main__':
    main()
