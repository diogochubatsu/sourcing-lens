"""
Compute image_hash for all ML products with image_urls but missing image_hash.
Processes products across home_organization, microfone, sports categories.
Waits 2 seconds between downloads to avoid rate limiting.
"""
import sys
import time
import requests
from io import BytesIO
from PIL import Image
import imagehash

sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import query, execute

def process_products():
    # Get products missing image_hash but with image_urls
    rows = query("""
        SELECT id, image_urls, category
        FROM products
        WHERE (image_hash IS NULL OR image_hash = '')
        AND image_urls IS NOT NULL
        AND array_length(image_urls, 1) > 0
        AND category IN ('home_organization', 'microfone', 'sports')
        ORDER BY category, id
    """)
    
    total = len(rows)
    print(f"Found {total} products to process")
    
    success = 0
    skipped = 0
    errors = []
    category_counts = {}
    
    for i, row in enumerate(rows):
        prod_id = row['id']
        category = row['category']
        urls = row['image_urls']
        first_url = urls[0] if urls else None
        
        if not first_url:
            skipped += 1
            continue
        
        try:
            # Download image
            resp = requests.get(first_url, timeout=30)
            resp.raise_for_status()
            
            img_content = resp.content
            
            # Compute perceptual hash
            img = Image.open(BytesIO(img_content)).convert('RGB')
            hash_str = str(imagehash.phash(img))
            
            # Update database
            execute(
                "UPDATE products SET image_hash = %s WHERE id = %s",
                (hash_str, prod_id)
            )
            
            success += 1
            category_counts[category] = category_counts.get(category, 0) + 1
            
            if (i + 1) % 10 == 0 or (i + 1) == total:
                print(f"  Progress: {i+1}/{total} ({success} success, {skipped} skipped, {len(errors)} errors)")
            
            # Wait 2 seconds between requests to avoid rate limiting
            if i < total - 1:
                time.sleep(2)
                
        except requests.exceptions.RequestException as e:
            errors.append((prod_id, str(e)))
            skipped += 1
            print(f"  [SKIP] ID={prod_id} ({category}): Download failed - {e}")
        except Exception as e:
            errors.append((prod_id, str(e)))
            skipped += 1
            print(f"  [SKIP] ID={prod_id} ({category}): Processing failed - {e}")
    
    print(f"\n{'='*60}")
    print(f"COMPLETE: {success} updated, {skipped} skipped ({len(errors)} errors)")
    print(f"Categories processed: {category_counts}")
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for prod_id, err in errors[:10]:
            print(f"  ID={prod_id}: {err}")
        if len(errors) > 10:
            print(f"  ... and {len(errors)-10} more")
    
    return success, skipped, errors, category_counts

if __name__ == "__main__":
    process_products()
