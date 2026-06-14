#!/usr/bin/env python3
"""Cluster Products — Groups products by CLIP embedding similarity.

Discovers potential new categories by finding clusters of visually similar products.

Usage:
    python3 scripts/cluster_products.py                    # Cluster all
    python3 scripts/cluster_products.py --category Audio   # Cluster specific L1
    python3 scripts/cluster_products.py --threshold 0.75   # Similarity threshold
"""
import sys
import os
import argparse
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from scripts.db import query, execute


def cosine_similarity(a, b):
    """Compute cosine similarity between two vectors."""
    import numpy as np
    a = np.array(a)
    b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def cluster_products(category=None, threshold=0.70):
    """Cluster products by CLIP embedding similarity."""
    try:
        import numpy as np
    except ImportError:
        print("Error: numpy required")
        print("Install: pip install numpy")
        return []
    
    # Get products with embeddings
    conditions = ["is_active = TRUE", "embedding IS NOT NULL"]
    params = []
    
    if category:
        conditions.append("category_l1 = %s")
        params.append(category)
    
    where = " AND ".join(conditions)
    products = query(f"""
        SELECT id, platform, platform_id, title, category_l1, category_l2, category_l3, embedding
        FROM products
        WHERE {where}
        ORDER BY id
    """, tuple(params))
    
    if len(products) < 2:
        print(f"Need at least 2 products with embeddings (found {len(products)})")
        return []
    
    print(f"Clustering {len(products)} products (threshold={threshold})")
    
    # Convert embeddings to numpy arrays
    embeddings = [np.array(p['embedding']) for p in products]
    
    # Simple clustering: group products with similarity > threshold
    clusters = []
    assigned = set()
    
    for i, p1 in enumerate(products):
        if i in assigned:
            continue
        
        cluster = [i]
        assigned.add(i)
        
        for j, p2 in enumerate(products):
            if j in assigned or j <= i:
                continue
            
            sim = cosine_similarity(embeddings[i], embeddings[j])
            if sim >= threshold:
                cluster.append(j)
                assigned.add(j)
        
        if len(cluster) >= 2:
            clusters.append(cluster)
    
    # Analyze clusters
    results = []
    for cluster_indices in clusters:
        cluster_products = [products[i] for i in cluster_indices]
        
        # Get common category info
        categories = set()
        for p in cluster_products:
            cat = f"{p['category_l1']}/{p['category_l2']}/{p['category_l3']}"
            categories.add(cat)
        
        # Get title words for naming suggestion
        all_words = []
        for p in cluster_products:
            words = p['title'].lower().split()
            all_words.extend(words)
        
        # Find most common meaningful words (not stopwords)
        stopwords = {'de', 'para', 'com', 'em', 'o', 'a', 'os', 'as', 'um', 'uma', 
                     'the', 'and', 'for', 'with', 'in', 'is', 'it', 'to', 'of'}
        word_freq = defaultdict(int)
        for w in all_words:
            if len(w) > 2 and w not in stopwords:
                word_freq[w] += 1
        
        # Suggest name from top words
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:3]
        suggested_name = ' '.join(w for w, _ in top_words)
        
        results.append({
            'size': len(cluster_indices),
            'products': [{'id': p['id'], 'platform': p['platform'], 'title': p['title'][:60]} 
                        for p in cluster_products],
            'current_categories': list(categories),
            'suggested_name': suggested_name,
            'avg_similarity': 0.0,  # Would need to compute pairwise
        })
    
    return results


def main():
    parser = argparse.ArgumentParser(description='Cluster Products by CLIP Embeddings')
    parser.add_argument('--category', type=str, help='Cluster specific L1 category')
    parser.add_argument('--threshold', type=float, default=0.70, help='Similarity threshold')
    parser.add_argument('--apply', action='store_true', help='Apply cluster suggestions to database')
    args = parser.parse_args()
    
    clusters = cluster_products(category=args.category, threshold=args.threshold)
    
    if not clusters:
        print("No clusters found")
        return
    
    print(f"\nFound {len(clusters)} clusters:\n")
    
    for i, c in enumerate(clusters):
        print(f"Cluster {i+1}: {c['size']} products")
        print(f"  Suggested name: {c['suggested_name']}")
        print(f"  Current categories: {', '.join(c['current_categories'])}")
        for p in c['products'][:3]:
            print(f"    - [{p['platform']}] {p['title']}")
        if c['size'] > 3:
            print(f"    ... and {c['size'] - 3} more")
        print()


if __name__ == '__main__':
    main()
