#!/usr/bin/env python3
"""
upload_images_to_gcp.py — Upload ArbitLens product images to ImportaSimples GCP bucket.

Path structure: gs://importasimples-intel-images/{source}/{marketplace}/{source_id}/img-0.jpg
Public URL: https://storage.googleapis.com/importasimples-intel-images/{source}/{marketplace}/{source_id}/img-0.jpg

Usage:
    python3 scripts/upload_images_to_gcp.py              # Upload all images
    python3 scripts/upload_images_to_gcp.py --dry-run    # Preview without uploading
    python3 scripts/upload_images_to_gcp.py --limit 10   # Upload only first 10
    python3 scripts/upload_images_to_gcp.py --update-db  # Also update bronze_products image_url/image_urls
"""

import argparse
import json
import os
import subprocess
import sys
import time
import psycopg2

# ── Config ────────────────────────────────────────────────────
SOURCE_VALUE = 'arbt.ly'
BUCKET = 'importasimples-intel-images'
GCP_BASE_URL = f'https://storage.googleapis.com/{BUCKET}'
KEY_FILE = os.path.join(os.path.dirname(__file__), '..', 'config', 'gcp-intel-images-writer.json')

# Platform → marketplace mapping
PLATFORM_MAP = {
    'amazon_br': 'amazon_br',
    'amazon_us': 'amazon_usa',
    'ml': 'mercadolivre',
}

# Destination DB config
DEST_CONFIG = {
    'host': '34.170.210.220',
    'port': 5432,
    'dbname': 'importasimples_products',
    'user': 'importasimples',
    'password': 'R{[{f<VajbC{<kvU',
    'sslmode': 'require',
}


def activate_service_account():
    """Activate the GCP service account for uploads."""
    result = subprocess.run(
        ['gcloud', 'auth', 'activate-service-account', '--key-file=' + KEY_FILE],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"❌ Failed to activate service account: {result.stderr}")
        return False
    print(f"✅ Service account activated")
    return True


def get_products_with_images(dest_cur):
    """Get all arbt.ly products with images from bronze_products."""
    dest_cur.execute("""
        SELECT id, source_id, marketplace, image_url, image_urls, image_count
        FROM bronze_products
        WHERE source = %s
        AND image_url IS NOT NULL
        ORDER BY source_id
    """, (SOURCE_VALUE,))
    return dest_cur.fetchall()


def upload_image(local_path, gcs_path):
    """Upload a single file to GCS."""
    result = subprocess.run(
        ['gcloud', 'storage', 'cp', local_path, f'gs://{BUCKET}/{gcs_path}'],
        capture_output=True, text=True
    )
    return result.returncode == 0


IMAGES_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'images')

def download_image(url, local_path):
    """Download an image from URL. Handles both URLs and local relative paths."""
    # If it's a relative path, resolve to local images directory
    if not url.startswith('http'):
        # Strip /images/ prefix if present (DB stores /images/amazon_br/X.jpg)
        # But local files are at data/images/amazon_br/X.jpg
        rel = url
        if rel.startswith('/images/'):
            rel = rel[len('/images/'):]  # amazon_br/X.jpg
        elif rel.startswith('/'):
            rel = rel[1:]  # strip leading /
        local_src = os.path.join(IMAGES_DIR, rel)
        if os.path.exists(local_src):
            import shutil
            shutil.copy2(local_src, local_path)
            return True
        return False
    
    result = subprocess.run(
        ['curl', '-s', '-L', '-o', local_path, '--max-time', '10', url],
        capture_output=True, text=True
    )
    return result.returncode == 0 and os.path.exists(local_path)


def process_images(products, dry_run=False, update_db=False, limit=None):
    """Main processing logic."""
    if not activate_service_account():
        return

    # Connect to destination DB for updates
    if update_db:
        dest_conn = psycopg2.connect(**DEST_CONFIG)
        dest_cur = dest_conn.cursor()

    uploaded = 0
    skipped = 0
    errors = 0
    start_time = time.time()

    total = len(products)
    if limit:
        products = products[:limit]
        total = len(products)

    for i, product in enumerate(products):
        prod_id, source_id, marketplace, image_url, image_urls, image_count = product

        # Build GCS path
        gcs_dir = f'{SOURCE_VALUE}/{marketplace}/{source_id}'
        gcs_path = f'{gcs_dir}/img-0.jpg'
        public_url = f'{GCP_BASE_URL}/{gcs_path}'

        # Check if already uploaded (by checking public URL)
        if not dry_run:
            check = subprocess.run(
                ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', public_url],
                capture_output=True, text=True
            )
            if check.stdout.strip() == '200':
                skipped += 1
                if (i + 1) % 100 == 0:
                    print(f"  [{i+1}/{total}] skipped={skipped} uploaded={uploaded} errors={errors}")
                continue

        if dry_run:
            print(f"  [DRY] {source_id}: {image_url} → gs://{BUCKET}/{gcs_path}")
            uploaded += 1
            continue

        # Download image
        local_path = f'/tmp/_upload_{source_id.replace(":", "_")}.jpg'
        if not download_image(image_url, local_path):
            errors += 1
            print(f"  ❌ Download failed: {source_id}")
            continue

        # Upload to GCS
        if upload_image(local_path, gcs_path):
            uploaded += 1
            # Clean up local file
            os.remove(local_path)

            # Update DB if requested
            if update_db:
                try:
                    dest_cur.execute("""
                        UPDATE bronze_products
                        SET image_url = %s, image_urls = ARRAY[%s]::text[]
                        WHERE id = %s
                    """, (public_url, public_url, prod_id))
                    dest_conn.commit()
                except Exception as e:
                    dest_conn.rollback()
                    print(f"  ⚠️ DB update failed for {source_id}: {e}")
        else:
            errors += 1
            print(f"  ❌ Upload failed: {source_id}")

        # Progress
        if (i + 1) % 50 == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            print(f"  [{i+1}/{total}] uploaded={uploaded} skipped={skipped} errors={errors} ({rate:.1f}/s)")

    # Final summary
    elapsed = time.time() - start_time
    print(f"\n{'='*50}")
    print(f"Upload complete in {elapsed:.1f}s")
    print(f"  Total products: {total}")
    print(f"  Uploaded: {uploaded}")
    print(f"  Skipped (already exists): {skipped}")
    print(f"  Errors: {errors}")

    if update_db:
        dest_conn.close()


def main():
    parser = argparse.ArgumentParser(description='Upload ArbitLens images to GCP bucket')
    parser.add_argument('--dry-run', action='store_true', help='Preview without uploading')
    parser.add_argument('--limit', type=int, default=None, help='Upload only N images')
    parser.add_argument('--update-db', action='store_true', help='Update bronze_products with public URLs')
    args = parser.parse_args()

    # Connect to destination to get products
    print("Connecting to destination DB...")
    dest_conn = psycopg2.connect(**DEST_CONFIG)
    dest_cur = dest_conn.cursor()

    products = get_products_with_images(dest_cur)
    dest_conn.close()

    print(f"Found {len(products)} products with images")
    process_images(products, dry_run=args.dry_run, update_db=args.update_db, limit=args.limit)


if __name__ == '__main__':
    main()
