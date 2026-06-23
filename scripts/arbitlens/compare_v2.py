#!/usr/bin/env python3
"""
compare_v2.py — Enhanced cross-platform comparison with visual matching.

Combines:
1. Text keyword extraction (existing)
2. Visual similarity via CLIP embeddings (new)
3. Price proximity scoring

Usage:
  python3 compare_v2.py --title "microfone bluetooth" --platform rakumart-1688 --limit 10
  python3 compare_v2.py --product-id "rakumart-1688_https://..." --limit 10
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

def compare_by_title(title, source_platform=None, limit=10):
    """Compare products by title similarity + visual matching."""
    conn = get_pg_conn()
    cursor = conn.cursor()
    
    # Text-based search: find products with similar titles
    text_query = f"""
        SELECT 
            id,
            platform || '_' || platform_id as product_id,
            platform,
            title,
            price,
            category,
            image_urls,
            image_embedding
        FROM arbitlens_products
        WHERE title ILIKE %s
            AND is_active = true
        ORDER BY 
            CASE WHEN platform NOT LIKE '%%mercado%%' THEN 0 ELSE 1 END,
            price ASC
        LIMIT {limit * 2}
    """
    cursor.execute(text_query, (f'%{title}%',))
    text_results = cursor.fetchall()
    
    # If we have visual embeddings, enhance with similarity scoring
    visual_results = []
    if text_results and text_results[0][7]:  # has embedding
        source_embedding = text_results[0][7]
        
        # Find visually similar products
        visual_query = f"""
            SELECT 
                id,
                platform || '_' || platform_id as product_id,
                platform,
                title,
                price,
                category,
                image_urls,
                1 - (image_embedding <=> %s::vector) as similarity
            FROM arbitlens_products
            WHERE image_embedding IS NOT NULL
                AND is_active = true
            ORDER BY image_embedding <=> %s::vector
            LIMIT {limit}
        """
        cursor.execute(visual_query, (source_embedding, source_embedding))
        visual_results = cursor.fetchall()
    
    conn.close()
    
    # Merge and deduplicate results
    seen = set()
    combined = []
    
    # Add text results with text_score
    for r in text_results[:limit]:
        pid = r[1]
        if pid not in seen:
            seen.add(pid)
            combined.append({
                'product_id': r[1],
                'platform': r[2],
                'title': r[3],
                'price': float(r[4]) if r[4] else None,
                'category': r[5],
                'image_url': r[6][0] if r[6] and len(r[6]) > 0 else None,
                'match_type': 'text',
                'text_score': None,  # Will be calculated below
                'visual_score': None,
                'composite_score': None,
            })
    
    # Add visual results with visual_score
    for r in visual_results:
        pid = r[1]
        similarity = float(r[7]) * 100 if r[7] else 0
        if pid not in seen:
            seen.add(pid)
            combined.append({
                'product_id': r[1],
                'platform': r[2],
                'title': r[3],
                'price': float(r[4]) if r[4] else None,
                'category': r[5],
                'image_url': r[6][0] if r[6] and len(r[6]) > 0 else None,
                'match_type': 'visual',
                'text_score': None,
                'visual_score': round(similarity, 1),
                'composite_score': round(similarity, 1),
            })
        else:
            # Update existing entry with visual score
            for item in combined:
                if item['product_id'] == pid:
                    item['visual_score'] = round(similarity, 1)
                    item['composite_score'] = round(
                        (item.get('text_score') or 0) * 0.4 + similarity * 0.6, 1
                    )
                    item['match_type'] = 'hybrid'
                    break
    
    # Calculate text scores for all results
    from scoring import text_score, price_score, sales_score, composite_score
    prices = [r.get('price') for r in combined if r.get('price')]
    min_price = min(prices) if prices else 0
    max_price = max(prices) if prices else 1000
    
    for item in combined:
        t_score = text_score(title, item.get('title', ''))
        v_score = item.get('visual_score') or 0
        p_score = price_score(item.get('price'), min_price, max_price) if item.get('price') else 50
        s_score = 0  # No sales data in comparison
        
        item['text_score'] = round(t_score, 1)
        item['composite_score'] = round(composite_score(t_score, v_score, p_score, s_score), 1)
    
    # Sort by composite score
    combined.sort(key=lambda x: x['composite_score'], reverse=True)
    
    return {
        'query': title,
        'source_platform': source_platform,
        'results': combined[:limit],
        'total_results': len(combined),
    }

def compare_by_product_id(product_id, limit=10):
    """Compare products by visual similarity from a product ID."""
    conn = get_pg_conn()
    cursor = conn.cursor()
    
    # Get source product
    cursor.execute(
        "SELECT id, platform, title, price, category, image_embedding "
        "FROM arbitlens_products WHERE platform || '_' || platform_id = %s",
        (product_id,)
    )
    source = cursor.fetchone()
    if not source or not source[5]:
        conn.close()
        return {'error': f'Product not found or no embedding: {product_id}'}
    
    # Find visually similar products
    visual_query = f"""
        SELECT 
            platform || '_' || platform_id as product_id,
            platform,
            title,
            price,
            category,
            CASE WHEN array_length(image_urls, 1) > 0 THEN image_urls[1] ELSE NULL END,
            1 - (image_embedding <=> %s::vector) as similarity
        FROM arbitlens_products
        WHERE id != %s AND image_embedding IS NOT NULL AND is_active = true
        ORDER BY image_embedding <=> %s::vector
        LIMIT {limit}
    """
    cursor.execute(visual_query, (source[5], source[0], source[5]))
    results = cursor.fetchall()
    conn.close()
    
    return {
        'source': {
            'product_id': product_id,
            'platform': source[1],
            'title': source[2],
            'price': float(source[3]) if source[3] else None,
            'category': source[4],
        },
        'results': [{
            'product_id': r[0],
            'platform': r[1],
            'title': r[2],
            'price': float(r[3]) if r[3] else None,
            'category': r[4],
            'image_url': r[5],
            'visual_score': round(float(r[6]) * 100, 1),
            'composite_score': round(float(r[6]) * 100, 1),
            'match_type': 'visual',
        } for r in results],
        'total_results': len(results),
    }

if __name__ == '__main__':
    if '--title' in sys.argv:
        idx = sys.argv.index('--title')
        title = sys.argv[idx + 1]
        platform = None
        if '--platform' in sys.argv:
            pidx = sys.argv.index('--platform')
            platform = sys.argv[pidx + 1]
        limit = 10
        if '--limit' in sys.argv:
            lidx = sys.argv.index('--limit')
            limit = int(sys.argv[lidx + 1])
        result = compare_by_title(title, platform, limit)
    elif '--product-id' in sys.argv:
        idx = sys.argv.index('--product-id')
        pid = sys.argv[idx + 1]
        limit = 10
        if '--limit' in sys.argv:
            lidx = sys.argv.index('--limit')
            limit = int(sys.argv[lidx + 1])
        result = compare_by_product_id(pid, limit)
    else:
        print(__doc__)
        sys.exit(1)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
