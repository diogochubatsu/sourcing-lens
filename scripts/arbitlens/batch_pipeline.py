#!/usr/bin/env python3
"""
batch_pipeline.py — Nightly batch pipeline for ArbitLens.

Runs:
1. Re-embed new products (products without embeddings)
2. Update matches (find new cross-platform matches)
3. Refresh opportunities (re-score opportunities)
4. Clean stale cache entries

Usage:
  python3 batch_pipeline.py                    # run all steps
  python3 batch_pipeline.py --step embed       # run only embedding
  python3 batch_pipeline.py --step matches     # run only matches
  python3 batch_pipeline.py --step opportunities  # run only opportunities
"""
import json
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def get_pg_conn():
    import psycopg2
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL not set")
    return psycopg2.connect(database_url)

def step_embed_products():
    """Embed products that don't have embeddings yet."""
    print("\n=== Step 1: Embedding new products ===")
    conn = get_pg_conn()
    cursor = conn.cursor()
    
    # Count products without embeddings
    cursor.execute("SELECT COUNT(*) FROM arbitlens_products WHERE image_embedding IS NULL AND image_urls IS NOT NULL AND array_length(image_urls, 1) > 0")
    count = cursor.fetchone()[0]
    print(f"  Products without embeddings: {count}")
    
    if count == 0:
        print("  All products already embedded")
        conn.close()
        return 0
    
    # Get products to embed
    cursor.execute(
        "SELECT id, platform, platform_id, title, image_urls[1] "
        "FROM arbitlens_products WHERE image_embedding IS NULL "
        "AND image_urls IS NOT NULL AND array_length(image_urls, 1) > 0 "
        "LIMIT 50"
    )
    products = cursor.fetchall()
    conn.close()
    
    if not products:
        return 0
    
    # Import embedding function
    try:
        from embed import compute_embedding
    except ImportError:
        print("  Error: embed.py not available")
        return 0
    
    embedded = 0
    for prod_id, platform, platform_id, title, image_url in products:
        if not image_url:
            continue
        
        try:
            embedding = compute_embedding(image_url)
            if embedding is not None:
                # Store in PostgreSQL
                pg_conn = get_pg_conn()
                pg_cursor = pg_conn.cursor()
                emb_str = '[' + ','.join(map(str, embedding.tolist())) + ']'
                pg_cursor.execute(
                    "UPDATE arbitlens_products SET image_embedding = %s::vector, last_updated = NOW() WHERE id = %s",
                    (emb_str, prod_id)
                )
                pg_conn.commit()
                pg_conn.close()
                embedded += 1
                print(f"  Embedded: {platform}_{platform_id[:30]}...")
        except Exception as e:
            print(f"  Error embedding {platform}_{platform_id}: {e}")
    
    print(f"  Embedded {embedded}/{len(products)} products")
    return embedded

def step_update_matches():
    """Update cross-platform matches using pgvector."""
    print("\n=== Step 2: Updating matches ===")
    conn = get_pg_conn()
    cursor = conn.cursor()
    
    # Find products with embeddings that don't have recent matches
    cursor.execute("""
        SELECT p.id, p.platform || '_' || p.platform_id as product_id, p.image_embedding
        FROM arbitlens_products p
        WHERE p.image_embedding IS NOT NULL
            AND p.is_active = true
            AND NOT EXISTS (
                SELECT 1 FROM arbitlens_matches m 
                WHERE m.product_a_id = p.id 
                AND m.created_at > NOW() - INTERVAL '7 days'
            )
        LIMIT 100
    """)
    products = cursor.fetchall()
    print(f"  Products needing match updates: {len(products)}")
    
    matches_created = 0
    for prod_id, product_id, embedding in products:
        if not embedding:
            continue
        
        # Find top 5 similar products
        cursor.execute(f"""
            SELECT 
                p.id,
                1 - (p.image_embedding <=> %s::vector) as similarity
            FROM arbitlens_products p
            WHERE p.id != %s AND p.image_embedding IS NOT NULL AND p.is_active = true
            ORDER BY p.image_embedding <=> %s::vector
            LIMIT 5
        """, (embedding, prod_id, embedding))
        
        similar = cursor.fetchall()
        for match_id, similarity in similar:
            if similarity > 0.7:  # 70% threshold
                try:
                    cursor.execute("""
                        INSERT INTO arbitlens_matches (product_a_id, product_b_id, confidence, match_method)
                        VALUES (%s, %s, %s, 'clip_v1')
                        ON CONFLICT (product_a_id, product_b_id) DO UPDATE SET
                            confidence = EXCLUDED.confidence,
                            created_at = NOW()
                    """, (prod_id, match_id, float(similarity)))
                    matches_created += 1
                except Exception:
                    pass
    
    conn.commit()
    conn.close()
    print(f"  Created/updated {matches_created} matches")
    return matches_created

def step_refresh_opportunities():
    """Refresh opportunity scores."""
    print("\n=== Step 3: Refreshing opportunities ===")
    from opportunity_detect import detect_opportunities
    
    opportunities = detect_opportunities(limit=50)
    print(f"  Found {len(opportunities)} opportunities")
    
    # Store in database
    conn = get_pg_conn()
    cursor = conn.cursor()
    
    for opp in opportunities:
        try:
            cursor.execute("""
                INSERT INTO arbitlens_products (platform, platform_id, title, price, category, sales_30d, review_count, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, true)
                ON CONFLICT (platform, platform_id) DO NOTHING
            """, (
                opp.get('platform', ''),
                opp.get('product_id', ''),
                opp.get('title', ''),
                opp.get('price_china', 0),
                opp.get('category', ''),
                opp.get('sales_30d', 0),
                opp.get('review_count', 0),
            ))
        except Exception:
            pass
    
    conn.commit()
    conn.close()
    return len(opportunities)

def step_clean_cache():
    """Clean stale cache entries."""
    print("\n=== Step 4: Cleaning cache ===")
    cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', 'search_cache.db')
    if os.path.exists(cache_path):
        import sqlite3
        conn = sqlite3.connect(cache_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM search_cache WHERE created_at < strftime('%s', 'now') - 86400")
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        print(f"  Cleaned {deleted} stale cache entries")
        return deleted
    print("  No cache file found")
    return 0

def main():
    """Run batch pipeline."""
    print(f"ArbitLens Batch Pipeline — {datetime.utcnow().isoformat()}")
    
    import argparse
    parser = argparse.ArgumentParser(description='Nightly batch pipeline')
    parser.add_argument('--step', choices=['embed', 'matches', 'opportunities', 'cache'], help='Run specific step')
    args = parser.parse_args()
    
    start = time.time()
    
    if args.step == 'embed' or args.step is None:
        step_embed_products()
    
    if args.step == 'matches' or args.step is None:
        step_update_matches()
    
    if args.step == 'opportunities' or args.step is None:
        step_refresh_opportunities()
    
    if args.step == 'cache' or args.step is None:
        step_clean_cache()
    
    elapsed = time.time() - start
    print(f"\nPipeline complete in {elapsed:.0f}s")

if __name__ == '__main__':
    main()

def step_update_taxonomy():
    """Update taxonomy product counts."""
    print("\n=== Step 5: Updating taxonomy counts ===")
    conn = get_pg_conn()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE taxonomy SET product_count = (
            SELECT COUNT(*) FROM arbitlens_products p
            WHERE p.is_active = true
            AND (p.category = taxonomy.slug 
                 OR p.category_n2 = taxonomy.slug 
                 OR p.category_n3 = taxonomy.slug 
                 OR p.category_n4 = taxonomy.slug
                 OR p.category_path LIKE taxonomy.slug || '.%')
        )
    ''')
    
    conn.commit()
    conn.close()
    print("  Taxonomy counts updated")
