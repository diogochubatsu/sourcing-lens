#!/usr/bin/env python3
"""
DHgate.com scraper — parses __NEXT_DATA__ JSON from search results.
No anti-bot, no auth needed.
"""
import json
import re
import sys
import urllib.request
import urllib.parse
sys.path.insert(0, '.')
from schema import ArbitlensProduct, save_products, print_summary


def parse_sales(val):
    """Parse '1.4K+' -> 1400, '500' -> 500, None -> None"""
    if not val:
        return None
    val = str(val).replace(',', '').strip()
    multiplier = 1
    if val.endswith('K+') or val.endswith('k+'):
        multiplier = 1000
        val = val[:-2]
    elif val.endswith('K') or val.endswith('k'):
        multiplier = 1000
        val = val[:-1]
    elif val.endswith('M+') or val.endswith('m+'):
        multiplier = 1000000
        val = val[:-2]
    elif val.endswith('M') or val.endswith('m'):
        multiplier = 1000000
        val = val[:-1]
    try:
        return int(float(val) * multiplier)
    except (ValueError, TypeError):
        return None


def scrape_dhgate(query: str, page: int = 1) -> list:
    """Scrape DHgate search results for a query."""
    encoded_query = urllib.parse.quote_plus(query)
    search_url = f"https://www.dhgate.com/wholesale/search.do?searchkey={encoded_query}&pageNo={page}"
    
    req = urllib.request.Request(search_url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    })
    
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode('utf-8', errors='replace')
    
    # Extract __NEXT_DATA__ JSON
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
    if not match:
        print("ERROR: Could not find __NEXT_DATA__ in DHgate response", file=sys.stderr)
        return []
    
    data = json.loads(match.group(1))
    
    # Navigate to product list
    products = []
    try:
        props = data.get('props', {}).get('pageProps', {})
        # Try different paths to find the product list
        product_list = None
        
        # Path 1: direct productList
        if 'productList' in props:
            product_list = props['productList']
        # Path 2: nested in data
        elif 'data' in props and 'productList' in props.get('data', {}):
            product_list = props['data']['productList']
        # Path 3: search result data
        else:
            # Deep search for any list with product-like items
            for key, val in props.items():
                if isinstance(val, list) and len(val) > 3:
                    if isinstance(val[0], dict) and ('productname' in val[0] or 'itemcode' in val[0]):
                        product_list = val
                        break
                elif isinstance(val, dict):
                    for k2, v2 in val.items():
                        if isinstance(v2, list) and len(v2) > 3:
                            if isinstance(v2[0], dict) and ('productname' in v2[0] or 'itemcode' in v2[0]):
                                product_list = v2
                                break
        
        if not product_list:
            # Fallback: dump structure to find products
            print(f"WARNING: Could not find product list. Props keys: {list(props.keys())}", file=sys.stderr)
            return []
        
        for item in product_list:
            if not isinstance(item, dict):
                continue
            
            # Parse price range
            price_str = item.get('pricebeforerate', item.get('simHighPrice', ''))
            price_low = None
            price_high = None
            if price_str:
                nums = re.findall(r'[\d.]+', str(price_str))
                if nums:
                    price_low = float(nums[0])
                    if len(nums) > 1:
                        price_high = float(nums[1])
            
            product = ArbitlensProduct(
                source_platform='dhgate',
                source_product_id=str(item.get('itemcode', '')),
                source_url=f"https://www.dhgate.com{item.get('productDetailUrl', '')}" if item.get('productDetailUrl', '').startswith('/') else item.get('productDetailUrl', ''),
                product_name=item.get('productname', ''),
                price_low=price_low,
                price_high=price_high,
                price_currency='USD',
                seller_name=item.get('domainname', ''),
                seller_id=str(item.get('supplierid', '')),
                seller_rating=float(str(item.get('feedBackPercent', '0')).replace('%', '')) if item.get('feedBackPercent') else None,
                seller_url=item.get('sellerStoreUrl', ''),
                moq=int(item.get('minOrderNum', 0)) if item.get('minOrderNum') else None,
                image_url=item.get('seo300ImagePath', item.get('bigimagepath', '')),
                monthly_sales=parse_sales(item.get('recentlysold')),
                review_count=int(item.get('reviewCount', 0)) if item.get('reviewCount') else None,
                raw_data=item,
            )
            products.append(product)
    
    except (KeyError, IndexError, TypeError) as e:
        print(f"ERROR parsing DHgate data: {e}", file=sys.stderr)
    
    return products


if __name__ == '__main__':
    query = sys.argv[1] if len(sys.argv) > 1 else "wireless+lapel+microphone+type-c"
    print(f"Scraping DHgate for: {query}")
    
    products = scrape_dhgate(query)
    
    if products:
        outpath = f"scripts/arbitlens/output/dhgate_{query.replace('+','_')}.json"
        import os
        os.makedirs(os.path.dirname(outpath), exist_ok=True)
        count = save_products(products, outpath)
        print_summary(products, "DHgate")
        print(f"\nSaved to: {outpath}")
    else:
        print("No products found!")
