#!/usr/bin/env python3
"""
Alibaba.com Direct Scraper — Uses Decodo Site Unblocker to bypass CAPTCHA.

Unlike the Rakumart proxy approach, this scrapes Alibaba directly with
residential proxies to get fresh, unfiltered data.

Usage:
  python3 scrape_alibaba_direct.py "microfone bluetooth" 30
  python3 scrape_alibaba_direct.py --query "wireless speaker" --limit 50
"""
import json
import re
import sys
import os
import urllib.request
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schema import ArbitlensProduct, save_products, print_summary

# Decodo Site Unblocker credentials
DECODO_USER = os.environ.get('SU_USER')
DECODO_PASS = os.environ.get('SU_PASS')
DECODO_HOST = 'unblock.decodo.com'
DECODO_PORT = '60000'


def scrape_alibaba_direct(query, limit=30):
    """Scrape Alibaba search results using Decodo Site Unblocker."""
    # URL encode the query
    encoded_query = urllib.parse.quote(query)
    url = f'https://www.alibaba.com/trade/search?SearchText={encoded_query}'
    
    # Set up proxy
    proxy_url = f'http://{DECODO_USER}:{DECODO_PASS}@{DECODO_HOST}:{DECODO_PORT}'
    proxy_handler = urllib.request.ProxyHandler({
        'http': proxy_url,
        'https': proxy_url,
    })
    opener = urllib.request.build_opener(proxy_handler)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'X-SU-Geo': 'Brazil',
        'X-SU-Locale': 'pt-br',
    }
    
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with opener.open(req, timeout=60) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error fetching Alibaba: {e}", file=sys.stderr)
        return []
    
    # Parse products from HTML
    products = []
    
    # Extract product cards using regex
    # Pattern: product title + price + image
    title_pattern = re.compile(r'class="elements-title[^"]*"[^>]*>([^<]+)</span>', re.IGNORECASE)
    price_pattern = re.compile(r'R\$\s*([\d.,]+)', re.IGNORECASE)
    image_pattern = re.compile(r'<img[^>]+src="([^"]+\.jpg[^"]*)"', re.IGNORECASE)
    link_pattern = re.compile(r'href="([^"]*product-detail[^"]*)"', re.IGNORECASE)
    
    titles = title_pattern.findall(html)
    prices = price_pattern.findall(html)
    images = image_pattern.findall(html)
    links = link_pattern.findall(html)
    
    # Match titles with prices and images
    for i, title in enumerate(titles[:limit]):
        title = title.strip()
        if not title or len(title) < 10:
            continue
            
        price_str = prices[i] if i < len(prices) else None
        price = None
        if price_str:
            try:
                price = float(price_str.replace('.', '').replace(',', '.'))
            except:
                pass
        
        image = images[i] if i < len(images) else None
        if image and not image.startswith('http'):
            image = 'https:' + image if image.startswith('//') else 'https://www.alibaba.com' + image
        
        link = links[i] if i < len(links) else None
        product_url = link
        if link and not link.startswith('http'):
            product_url = 'https://www.alibaba.com' + link
        
        products.append(ArbitlensProduct(
            source_platform='alibaba-direct',
            source_product_id=link.split('/')[-1].split('.html')[0] if link else str(i),
            source_url=product_url or '',
            product_name=title,
            price_low=price,
            price_currency='USD',
            image_url=image or '',
        ))
    
    return products


if __name__ == '__main__':
    query = sys.argv[1] if len(sys.argv) > 1 else 'microfone bluetooth'
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    print(f"Scraping Alibaba Direct via Decodo: '{query}'")
    products = scrape_alibaba_direct(query, limit)
    
    if products:
        os.makedirs(os.path.join(os.path.dirname(__file__), 'output'), exist_ok=True)
        outpath = os.path.join(os.path.dirname(__file__), 'output', 'alibaba_direct.json')
        save_products(products, outpath)
        print_summary(products, "Alibaba Direct")
        print(f"\nSaved to: {outpath}")
    else:
        print("No products found!")
