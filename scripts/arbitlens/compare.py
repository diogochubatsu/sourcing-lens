#!/usr/bin/env python3
"""
arbitlens Price Comparison V2 — find same product across platforms.

V2 approach: extract keywords from product title, search other platforms,
show results side by side. User decides what's the same product.
NO automated matching, NO confidence scores.

Usage:
  python3 compare.py "Microfone de lapela sem fio Q8" "rakumart-1688"
  python3 compare.py "Wireless lapel microphone" "dhgate" --max 10
"""
import json
import os
import re
import sys
import time
import concurrent.futures

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Reuse scrapers
from scrape_rakumart_br import search_rakumart_br
from scrape_dhgate import scrape_dhgate
from scrape_alibaba import scrape_alibaba


# Stopwords to remove from title (Portuguese, English, Chinese)
STOPWORDS = {
    'de', 'para', 'com', 'sem', 'em', 'no', 'na', 'do', 'da', 'dos', 'das',
    'um', 'uma', 'uns', 'umas', 'o', 'a', 'os', 'as', 'e', 'ou', 'que',
    'é', 'não', 'mais', 'muito', 'nova', 'novo', 'novos', 'novas',
    'ideal', 'perfeito', 'ótimo', 'melhor', 'profissional', 'original',
    'and', 'the', 'for', 'with', 'without', 'new', 'best', 'top', 'pro',
    'mini', 'portátil', 'portable', 'wireless', 'bluetooth', 'tipo',
    'type', 'c', 'usb', 'kit', 'pack', '2', '3', '4', 'em', '1',
    'com', 'suporte', 'para', 'mais', 'vendas', 'atacado',
    'promoção', 'barato', 'qualidade', 'direto', 'fábrica',
    # Chinese common words
    '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一',
    '个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着',
    '没有', '看', '好', '自己', '这', '来', '吧', '吗', '啊', '哦',
}


def extract_keywords(title, max_keywords=6):
    """Extract meaningful keywords from a product title."""
    if not title:
        return []
    
    # Normalize: lowercase, remove special chars
    text = title.lower()
    text = re.sub(r'[^a-z0-9áéíóúãõçâêîôûàèìòùäëïöüñ\s-]', ' ', text)
    
    # Split into words
    words = re.split(r'[\s,-]+', text)
    
    # Filter: keep meaningful words (>= 3 chars, not stopwords, alphanumeric)
    keywords = []
    for w in words:
        w = w.strip()
        if len(w) >= 2 and w not in STOPWORDS:
            keywords.append(w)
    
    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for k in keywords:
        if k not in seen:
            seen.add(k)
            unique.append(k)
    
    return unique[:max_keywords]


def scrape_platform(platform, query, max_results=10):
    """Scrape a single platform and return products."""
    try:
        if platform == 'rakumart-1688':
            return search_rakumart_br(query, source='1688')[:max_results]
        elif platform == 'rakumart-taobao':
            return search_rakumart_br(query, source='taobao')[:max_results]
        elif platform == 'rakumart-alibaba':
            return search_rakumart_br(query, source='alibaba')[:max_results]
        elif platform == 'dhgate':
            return scrape_dhgate(query)[:max_results]
        elif platform == 'alibaba':
            return scrape_alibaba(query)[:max_results]
        return []
    except Exception as e:
        print(f"  Error scraping {platform}: {e}", file=sys.stderr)
        return []


def to_brl(price, curr):
    if not price:
        return None
    if curr == 'BRL':
        return round(price, 2)
    elif curr == 'CNY':
        return round(price * 0.78, 2)
    elif curr == 'USD':
        return round(price * 5.69, 2)
    return round(price, 2)


def product_to_dict(p):
    return {
        'platform': getattr(p, 'source_platform', 'unknown'),
        'product_name': (getattr(p, 'product_name', '') or '')[:120],
        'price_low': getattr(p, 'price_low', None),
        'price_high': getattr(p, 'price_high', None),
        'price_currency': getattr(p, 'price_currency', 'USD'),
        'price_brl': to_brl(getattr(p, 'price_low', None), getattr(p, 'price_currency', 'USD')),
        'image_url': getattr(p, 'image_url', ''),
        'product_url': getattr(p, 'source_url', ''),
        'seller_name': getattr(p, 'seller_name', '') or '',
        'monthly_sales': getattr(p, 'monthly_sales', None),
    }


# Which platforms to search beyond the source
PLATFORMS = ['rakumart-1688', 'rakumart-taobao', 'rakumart-alibaba', 'dhgate', 'alibaba']


def compare_prices(title, source_platform, max_results=10):
    """
    Search all OTHER platforms for the same product.
    Extract keywords from the title, search each platform.
    """
    keywords = extract_keywords(title)
    if not keywords:
        keywords = title.split()[:4]  # fallback: first 4 words
    
    search_query = ' '.join(keywords)
    print(f"  Keywords: {keywords}", file=sys.stderr)
    print(f"  Query: {search_query}", file=sys.stderr)
    
    # Define which platforms to search (exclude the source)
    platforms_to_search = [p for p in PLATFORMS if p != source_platform]
    # Always search at least 2 platforms
    if not platforms_to_search:
        platforms_to_search = PLATFORMS
    
    # Search in parallel
    all_products = []
    platform_counts = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(scrape_platform, p, search_query, max_results): p
            for p in platforms_to_search
        }
        for future in concurrent.futures.as_completed(futures):
            p = futures[future]
            try:
                products = future.result()
                all_products.extend(products)
                platform_counts[p] = len(products)
                print(f"  {p}: {len(products)} products", file=sys.stderr)
            except Exception as e:
                print(f"  {p}: error - {e}", file=sys.stderr)
                platform_counts[p] = 0
    
    # Convert to dicts
    flat = [product_to_dict(p) for p in all_products]
    
    # Sort by BRL price
    flat.sort(key=lambda x: (x['price_brl'] is None, x['price_brl'] or 0))
    
    # Group by platform for the response
    by_platform = {}
    for product in flat:
        plat = product['platform']
        if plat not in by_platform:
            by_platform[plat] = []
        by_platform[plat].append(product)
    
    return {
        'original_title': title,
        'source_platform': source_platform,
        'keywords_used': keywords,
        'search_query': search_query,
        'products': flat,
        'total_products': len(flat),
        'by_platform': by_platform,
        'platform_counts': platform_counts,
    }


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 compare.py \"product title\" [source_platform]")
        sys.exit(1)
    
    title = sys.argv[1]
    source = sys.argv[2] if len(sys.argv) > 2 else 'unknown'
    max_results = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    
    start = time.time()
    result = compare_prices(title, source, max_results)
    elapsed = int((time.time() - start) * 1000)
    result['search_time_ms'] = elapsed
    
    print(json.dumps(result, ensure_ascii=False, indent=2))