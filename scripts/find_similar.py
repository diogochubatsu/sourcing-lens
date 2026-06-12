#!/usr/bin/env python3
"""Find similar products by CLIP embedding cosine similarity.

Usage:
    python3 scripts/find_similar.py --product-id 123 --limit 10
    python3 scripts/find_similar.py --platform-id B0CT633X1L --platform amazon_br --limit 5
    python3 scripts/find_similar.py --match --category microfone
"""
import argparse, sys
sys.path.insert(0, '.')
from scripts.db import query

def find_similar(embedding, limit=10, category=None, exclude_id=None):
    where = "WHERE p.embedding IS NOT NULL"
    params = [embedding]
    
    if category:
        where += " AND p.category = %s"
        params.append(category)
    if exclude_id:
        where += " AND p.id != %s"
        params.append(exclude_id)
    
    sql = f"""
        SELECT p.id, p.platform, p.platform_id, p.title, p.price, p.sales_30d,
               p.category, p.image_urls[1] as img,
               1 - (p.embedding <=> %s::vector) as similarity
        FROM products p
        {where}
        ORDER BY p.embedding <=> %s::vector
        LIMIT %s
    """
    params.append(limit)
    return query(sql, tuple(params))

def match_category(category):
    """Run matching within a category using embedding similarity."""
    products = query("""
        SELECT id, platform, platform_id, embedding 
        FROM products WHERE category=%s AND embedding IS NOT NULL
        ORDER BY platform, id
    """, (category,))
    
    br_products = [p for p in products if p['platform'] == 'amazon_br']
    ml_products = [p for p in products if p['platform'] == 'ml']
    
    print(f'{category}: {len(br_products)} BR, {len(ml_products)} ML with embeddings')
    
    matches = []
    for br in br_products:
        sql = """
            SELECT id, platform_id, 1 - (embedding <=> %s::vector) as sim
            FROM products WHERE platform='ml' AND category=%s AND embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector LIMIT 1
        """
        best = query(sql, (br['embedding'], category, br['embedding']))
        if best and best[0]['sim'] >= 0.7:
            matches.append((br, best[0], best[0]['sim']))
    
    return matches

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--product-id', type=int)
    parser.add_argument('--platform-id')
    parser.add_argument('--platform')
    parser.add_argument('--category')
    parser.add_argument('--limit', type=int, default=10)
    parser.add_argument('--match', action='store_true')
    args = parser.parse_args()
    
    if args.match and args.category:
        # Run category matching by embedding
        matches = match_category(args.category)
        print(f'\nMatches found: {len(matches)}')
        for br, ml, sim in matches[:10]:
            print(f'  sim={sim:.4f} | {br["platform_id"]} ↔ {ml["platform_id"]}')
    
    elif args.product_id:
        emb = query("SELECT embedding FROM products WHERE id=%s", (args.product_id,))
        if emb and emb[0]['embedding']:
            results = find_similar(emb[0]['embedding'], args.limit, exclude_id=args.product_id)
            for r in results:
                print(f'  {r["similarity"]:.4f} | {r["platform"]:15s} {r["platform_id"]:20s} | {r["title"][:50]}')
    
    elif args.platform_id and args.platform:
        emb = query("SELECT id, embedding FROM products WHERE platform_id=%s AND platform=%s", 
                    (args.platform_id, args.platform))
        if emb and emb[0]['embedding']:
            results = find_similar(emb[0]['embedding'], args.limit, exclude_id=emb[0]['id'])
            for r in results:
                print(f'  {r["similarity"]:.4f} | {r["platform"]:15s} {r["platform_id"]:20s} | {r["title"][:50]}')
