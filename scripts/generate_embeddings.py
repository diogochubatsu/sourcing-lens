#!/usr/bin/env python3
"""Generate CLIP Embeddings — Creates embeddings for products without them.

Usage:
    python3 scripts/generate_embeddings.py                    # All products
    python3 scripts/generate_embeddings.py --category Audio   # Specific L1
    python3 scripts/generate_embeddings.py --limit 10         # Limit batch size
"""
import sys
import os
import argparse
from io import BytesIO

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from scripts.db import query, execute


def generate_embeddings(category=None, limit=100):
    """Generate CLIP embeddings for products without them."""
    try:
        from sentence_transformers import SentenceTransformer
        from PIL import Image
        import requests
    except ImportError as e:
        print(f"Error: Missing dependency: {e}")
        print("Install: pip install sentence-transformers Pillow requests")
        return 0
    
    # Load model
    print("Loading CLIP model...")
    model = SentenceTransformer('clip-ViT-B-32')
    
    # Get products without embeddings
    conditions = ["is_active = TRUE", "embedding IS NULL", "image_urls IS NOT NULL", "array_length(image_urls, 1) > 0"]
    params = []
    
    if category:
        conditions.append("category_l1 = %s")
        params.append(category)
    
    where = " AND ".join(conditions)
    products = query(f"""
        SELECT id, platform, platform_id, title, image_urls
        FROM products
        WHERE {where}
        LIMIT %s
    """, tuple(params) + (limit,))
    
    if not products:
        print("No products need embeddings")
        return 0
    
    print(f"Found {len(products)} products without embeddings")
    
    generated = 0
    for i, p in enumerate(products):
        img_url = p['image_urls'][0] if p['image_urls'] else None
        if not img_url:
            continue
        
        try:
            # Download image
            resp = requests.get(img_url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
            if resp.status_code != 200:
                print(f"  [{i+1}] Failed to download image for {p['platform_id']}")
                continue
            
            # Generate embedding
            img = Image.open(BytesIO(resp.content)).convert('RGB')
            embedding = model.encode(img)
            embedding_list = embedding.tolist()
            
            # Store in database
            execute(
                "UPDATE products SET embedding = %s::vector WHERE id = %s",
                (embedding_list, p['id'])
            )
            
            generated += 1
            print(f"  [{i+1}] {p['platform']}: {p['title'][:40]}... ✓")
            
        except Exception as e:
            print(f"  [{i+1}] Error for {p['platform_id']}: {e}")
    
    print(f"\nGenerated {generated} embeddings")
    return generated


def main():
    parser = argparse.ArgumentParser(description='Generate CLIP Embeddings')
    parser.add_argument('--category', type=str, help='Generate for specific L1 category')
    parser.add_argument('--limit', type=int, default=100, help='Max products to process')
    args = parser.parse_args()
    
    generate_embeddings(category=args.category, limit=args.limit)


if __name__ == '__main__':
    main()
