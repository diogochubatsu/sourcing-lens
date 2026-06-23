#!/usr/bin/env python3
"""
Migrate CLIP embeddings from SQLite to PostgreSQL+pgvector.

Usage:
  python3 migrate_embeddings_to_pg.py              # migrate all
  python3 migrate_embeddings_to_pg.py --batch 500  # migrate in batches
  python3 migrate_embeddings_to_pg.py --verify      # verify migration
"""
import os
import sys
import sqlite3
import struct
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# SQLite path
SQLITE_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', 'embeddings.db')

def get_pg_connection():
    """Get PostgreSQL connection."""
    import psycopg2
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL not set")
    return psycopg2.connect(database_url)

def blob_to_embedding(blob):
    """Convert binary blob to list of floats."""
    if not blob:
        return None
    # 512 floats * 4 bytes each
    count = len(blob) // 4
    return list(struct.unpack(f'{count}f', blob[:count * 4]))

def migrate_batch(cursor, products, batch_size=500):
    """Insert batch of products with embeddings."""
    insert_sql = """
        INSERT INTO arbitlens_products (
            platform, platform_id, title, price, currency,
            image_embedding, category, image_urls
        ) VALUES (
            %s, %s, %s, %s, 'BRL', %s::vector, %s, %s
        )
        ON CONFLICT (platform, platform_id) DO UPDATE SET
            title = EXCLUDED.title,
            price = EXCLUDED.price,
            image_embedding = EXCLUDED.image_embedding,
            category = EXCLUDED.category,
            image_urls = EXCLUDED.image_urls,
            last_updated = NOW()
    """
    
    batch = []
    for prod in products:
        pid = prod['id'] or ''
        platform = prod['source_platform'] or 'unknown'
        
        # Parse embedding blob
        emb_blob = prod['embedding']
        if not emb_blob:
            continue
        
        embedding = blob_to_embedding(emb_blob)
        if not embedding:
            continue
        
        # Format embedding for pgvector
        emb_str = '[' + ','.join(map(str, embedding)) + ']'
        
        # Parse metadata
        metadata = json.loads(prod.get('metadata', '{}'))
        image_url = prod.get('image_url', '') or metadata.get('image_url', '')
        
        batch.append((
            platform,
            pid,
            (prod.get('product_name', '') or '')[:500],
            prod.get('price_brl'),
            emb_str,
            prod.get('category_n1', ''),
            [image_url] if image_url else [],
        ))
        
        if len(batch) >= batch_size:
            cursor.executemany(insert_sql, batch)
            batch = []
    
    if batch:
        cursor.executemany(insert_sql, batch)
    
    return len(products)

def main():
    """Main migration logic."""
    print("Migrating CLIP embeddings from SQLite to PostgreSQL+pgvector")
    
    # Connect to SQLite
    if not os.path.exists(SQLITE_DB):
        print(f"Error: SQLite database not found at {SQLITE_DB}")
        sys.exit(1)
    
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_conn.row_factory = sqlite3.Row
    
    # Connect to PostgreSQL
    try:
        pg_conn = get_pg_connection()
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        print("Make sure DATABASE_URL is set and PostgreSQL is running")
        sys.exit(1)
    
    pg_cursor = pg_conn.cursor()
    
    # Count total
    total = sqlite_conn.execute('SELECT COUNT(*) FROM products WHERE embedding IS NOT NULL').fetchone()[0]
    print(f"Found {total} products with embeddings in SQLite")
    
    # Migrate in batches
    batch_size = 500
    offset = 0
    migrated = 0
    start_time = time.time()
    
    while offset < total:
        products = sqlite_conn.execute(
            'SELECT * FROM products WHERE embedding IS NOT NULL LIMIT ? OFFSET ?',
            (batch_size, offset)
        ).fetchall()
        
        if not products:
            break
        
        count = migrate_batch(pg_cursor, [dict(p) for p in products])
        pg_conn.commit()
        migrated += count
        
        elapsed = time.time() - start_time
        rate = migrated / elapsed if elapsed > 0 else 0
        eta = (total - migrated) / rate if rate > 0 else 0
        
        print(f"  [{migrated}/{total}] migrated in {elapsed:.0f}s | Rate: {rate:.0f}/s | ETA: {eta:.0f}s")
        offset += batch_size
    
    # Verify
    pg_cursor.execute('SELECT COUNT(*) FROM arbitlens_products WHERE image_embedding IS NOT NULL')
    pg_count = pg_cursor.fetchone()[0]
    
    print(f"\nMigration complete")
    print(f"  SQLite: {total} embeddings")
    print(f"  PostgreSQL: {pg_count} embeddings")
    
    sqlite_conn.close()
    pg_conn.close()

if __name__ == '__main__':
    main()
