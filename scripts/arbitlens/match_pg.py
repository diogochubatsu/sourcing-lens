#!/usr/bin/env python3
"""
match_pg.py — PostgreSQL+pgvector similarity search.

Uses HNSW index for sub-millisecond nearest-neighbor queries.

Usage:
  python3 match_pg.py --product-id "rakumart-1688_12345" --limit 10
  python3 match_pg.py --image-url "https://..." --limit 10
  python3 match_pg.py --text "microfone bluetooth" --limit 10
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def get_pg_conn():
    """Get PostgreSQL connection."""
    import psycopg2
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL not set")
    return psycopg2.connect(database_url)

def find_similar_by_product_id(product_id, limit=10, exclude_same_platform=True):
    """Find similar products by product ID using pgvector."""
    conn = get_pg_conn()
    cursor = conn.cursor()
    
    # Get the source product's embedding
    cursor.execute(
        'SELECT id, platform, platform_id, title, price, image_embedding FROM arbitlens_products WHERE platform || \'_\' || platform_id = %s',
        (product_id,)
    )
    row = cursor.fetchone()
    if not row or not row[5]:
        conn.close()
        return {'error': f'Product not found or no embedding: {product_id}'}
    
    source_id = row[0]
    embedding = row[5]
    
    # psycopg2 returns pgvector as string like "[-0.69,0.26,...]"
    # For pgvector queries we pass it directly as a string
    if isinstance(embedding, str):
        embedding_str = embedding
    else:
        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
    
    # Find similar products
    where_clause = "id != %s AND image_embedding IS NOT NULL"
    params = [source_id]
    
    if exclude_same_platform:
        where_clause += " AND platform != %s"
        params.append(row[1])
    
    query_sql = f"""
        SELECT 
            id,
            platform || '_' || platform_id as product_id,
            title,
            price,
            image_urls,
            category,
            1 - (image_embedding <=> %s::vector) AS similarity
        FROM arbitlens_products
        WHERE {where_clause}
        ORDER BY image_embedding <=> %s::vector
        LIMIT %s
    """
    
    params.insert(0, embedding_str)
    params.append(embedding_str)
    params.append(limit)
    
    cursor.execute(query_sql, params)
    results = cursor.fetchall()
    conn.close()
    
    return {
        'source': {
            'product_id': product_id,
            'platform': row[1],
            'title': row[3],
            'price': float(row[4]) if row[4] else None,
        },
        'matches': [{
            'product_id': r[1],
            'platform': r[1].split('_')[0],
            'title': r[2],
            'price': float(r[3]) if r[3] else None,
            'category': r[5],
            'similarity': round(float(r[6]) * 100, 1),
        } for r in results],
        'total_matches': len(results),
    }

def find_similar_by_embedding(embedding, limit=10, platform_filter=None, category_filter=None):
    """Find similar products by embedding vector."""
    conn = get_pg_conn()
    cursor = conn.cursor()
    
    where_clauses = ["image_embedding IS NOT NULL"]
    params = []
    
    if platform_filter:
        where_clauses.append("platform = %s")
        params.append(platform_filter)
    
    if category_filter:
        where_clauses.append("category = %s")
        params.append(category_filter)
    
    where_sql = " AND ".join(where_clauses)
    
    query_sql = f"""
        SELECT 
            id,
            platform || '_' || platform_id as product_id,
            platform,
            title,
            price,
            category,
            1 - (image_embedding <=> %s::vector) AS similarity
        FROM arbitlens_products
        WHERE {where_sql}
        ORDER BY image_embedding <=> %s::vector
        LIMIT %s
    """
    
    embedding_str = '[' + ','.join(map(str, embedding)) + ']'
    params.insert(0, embedding_str)
    params.append(embedding_str)
    params.append(limit)
    
    cursor.execute(query_sql, params)
    results = cursor.fetchall()
    conn.close()
    
    return [{
        'product_id': r[1],
        'platform': r[2],
        'title': r[3],
        'price': float(r[4]) if r[4] else None,
        'category': r[5],
        'similarity': round(float(r[6]) * 100, 1),
    } for r in results]

def embed_and_search(image_url=None, image_path=None, limit=10):
    """Compute CLIP embedding for an image and find similar products."""
    try:
        from embed import compute_embedding, _get_model, _processor
    except ImportError:
        return {'error': 'embed.py not available'}
    
    if image_path:
        from PIL import Image
        img = Image.open(image_path).convert('RGB')
        model, processor = _get_model()
        inputs = processor(images=img, return_tensors='pt')
        outputs = model.get_image_features(**inputs)
        import torch
        embedding = outputs.detach().numpy()[0]
    elif image_url:
        embedding = compute_embedding(image_url)
    else:
        return {'error': 'No image provided'}
    
    if embedding is None:
        return {'error': 'Failed to compute embedding'}
    
    return find_similar_by_embedding(embedding, limit=limit)

if __name__ == '__main__':
    if '--product-id' in sys.argv:
        idx = sys.argv.index('--product-id')
        pid = sys.argv[idx + 1]
        limit = int(sys.argv[sys.argv.index('--limit') + 1]) if '--limit' in sys.argv else 10
        results = find_similar_by_product_id(pid, limit=limit)
    elif '--embed-image' in sys.argv:
        idx = sys.argv.index('--embed-image')
        img_path = sys.argv[idx + 1]
        limit = int(sys.argv[sys.argv.index('--limit') + 1]) if '--limit' in sys.argv else 10
        results = embed_and_search(image_path=img_path, limit=limit)
    elif '--image-url' in sys.argv:
        idx = sys.argv.index('--image-url')
        url = sys.argv[idx + 1]
        limit = int(sys.argv[sys.argv.index('--limit') + 1]) if '--limit' in sys.argv else 10
        results = embed_and_search(image_url=url, limit=limit)
    elif '--text' in sys.argv:
        # Text-based search (not visual, just category/title)
        idx = sys.argv.index('--text')
        text = sys.argv[idx + 1]
        limit = int(sys.argv[sys.argv.index('--limit') + 1]) if '--limit' in sys.argv else 10
        conn = get_pg_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT platform || '_' || platform_id, platform, title, price, category FROM arbitlens_products WHERE title ILIKE %s ORDER BY price LIMIT %s",
            (f'%{text}%', limit)
        )
        results = [{'product_id': r[0], 'platform': r[1], 'title': r[2], 'price': float(r[3]) if r[3] else None, 'category': r[4]} for r in cursor.fetchall()]
        conn.close()
        results = {'query': text, 'results': results}
    else:
        print(__doc__)
        sys.exit(1)
    
    print(json.dumps(results, ensure_ascii=False, indent=2))
