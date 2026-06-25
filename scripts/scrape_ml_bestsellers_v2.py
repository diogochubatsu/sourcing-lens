#!/usr/bin/env python3
"""
scrape_ml_bestsellers_v2.py — Scrape ML best sellers pages for sales data.

ML best sellers pages show total lifetime sales for each product.
This script scrapes the best sellers pages and extracts sales data.

Usage:
  python3 scripts/scrape_ml_bestsellers_v2.py --dry-run --limit 3
  python3 scripts/scrape_ml_bestsellers_v2.py --limit 5 --update-db
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request
import ssl

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.db import query, execute

# ── Config ──────────────────────────────────────────────────────────

DECODO_API_AUTH_FILE = os.path.join(os.path.dirname(__file__), '..', 'config', 'decodo_scraping.key')
DECODO_URL = 'https://scraper-api.decodo.com/v2/scrape'

# ML category IDs for best sellers pages
ML_CATEGORY_IDS = {
    'Audio': 'MLB3835',
    'Acessórios Mobile': 'MLB3813',
    'Bebê': 'MLB1384',
    'Beleza': 'MLB1246',
    'Bolsas': 'MLB1457',
    'Brinquedos': 'MLB1132',
    'Casa': 'MLB1574',
    'Cozinha': 'MLB1618',
    'Esportes': 'MLB1276',
    'Ferramentas': 'MLB263532',
    'Fotografia': 'MLB1744',
    'Iluminação': 'MLB1575',
    'Meias': 'MLB437816',
    'Mochilas': 'MLB3127',
    'Moda': 'MLB1430',
    'Moda Intima': 'MLB108786',
    'Pet Shop': 'MLB1071',
    'Praia': 'MLB430391',
    'Wearables': 'MLB417704',
}

def get_decodo_auth():
    path = os.path.abspath(DECODO_API_AUTH_FILE)
    if os.path.exists(path):
        with open(path) as f:
            return f.read().strip()
    return os.environ.get('DECODO_API_AUTH', '')

def scrape_ml_bestsellers(category_l1, auth):
    """Scrape ML best sellers page for a category."""
    mlb_id = ML_CATEGORY_IDS.get(category_l1)
    if not mlb_id:
        print(f"  No MLB ID for category: {category_l1}")
        return None
    
    url = f"https://www.mercadolivre.com.br/mais-vendidos/{mlb_id}"
    
    data = json.dumps({
        'url': url,
        'headless': 'html',
        'proxy_pool': 'premium',
        'locale': 'pt-br'
    }).encode()
    
    req = urllib.request.Request(
        DECODO_URL,
        data=data,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {auth}'
        }
    )
    
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        resp = urllib.request.urlopen(req, timeout=30, context=ctx)
        result = json.loads(resp.read().decode())
        
        if 'results' in result and len(result['results']) > 0:
            return result['results'][0].get('content', '')
        return None
    except Exception as e:
        print(f"  Error scraping: {e}")
        return None

def extract_sales_from_bestsellers(html):
    """Extract sales data from ML best sellers page HTML."""
    if not html:
        return {}
    
    sales_data = {}
    
    # Look for MLB IDs and sales counts
    # ML best sellers pages show products with sales like "10.000 vendidos"
    # or "5.000+ vendidos"
    
    # Pattern 1: MLB ID followed by sales
    mlb_pattern = r'(MLB\d+).*?(\d[\d.,]*)\+?\s*vendidos?'
    matches = re.findall(mlb_pattern, html, re.IGNORECASE | re.DOTALL)
    
    for mlb_id, sales_str in matches:
        try:
            sales = int(sales_str.replace('.', '').replace(',', ''))
            sales_data[mlb_id] = sales
        except:
            continue
    
    # Pattern 2: Look for "Mais de X vendidos" or similar
    mais_pattern = r'Mais de (\d[\d.,]*)\+?\s*vendidos?'
    mais_matches = re.findall(mais_pattern, html, re.IGNORECASE)
    
    # If we found products but no sales, try to extract from structured data
    if not sales_data:
        # Look for JSON-LD or other structured data
        jsonld_pattern = r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>'
        jsonld_matches = re.findall(jsonld_pattern, html, re.DOTALL)
        
        for match in jsonld_matches:
            try:
                data = json.loads(match)
                if isinstance(data, dict) and 'itemListElement' in data:
                    for item in data['itemListElement']:
                        if 'url' in item:
                            # Extract MLB ID from URL
                            mlb_match = re.search(r'(MLB\d+)', item['url'])
                            if mlb_match:
                                mlb_id = mlb_match.group(1)
                                # Look for sales in the item
                                if 'offers' in item and 'availability' in item['offers']:
                                    # This is a stretch, but some pages include sales info
                                    pass
            except:
                continue
    
    return sales_data

def main():
    parser = argparse.ArgumentParser(description='Scrape ML best sellers for sales data')
    parser.add_argument('--dry-run', action='store_true', help='Preview without updating DB')
    parser.add_argument('--limit', type=int, default=3, help='Number of categories to scrape')
    parser.add_argument('--update-db', action='store_true', help='Update database with scraped data')
    parser.add_argument('--delay', type=float, default=3.0, help='Delay between requests (seconds)')
    parser.add_argument('--category', type=str, help='Scrape only this category')
    args = parser.parse_args()
    
    auth = get_decodo_auth()
    if not auth:
        print("ERROR: No Decodo API key found")
        sys.exit(1)
    
    # Get categories that need sales data
    if args.category:
        categories = [args.category]
    else:
        categories = query("""
            SELECT DISTINCT category_l1
            FROM products 
            WHERE is_active = true 
              AND platform = 'ml'
              AND (sales_30d = 0 OR sales_30d IS NULL)
            ORDER BY category_l1
            LIMIT %s
        """, (args.limit,))
        categories = [r['category_l1'] for r in categories]
    
    print(f"Scraping {len(categories)} ML categories for sales data...")
    print(f"Delay: {args.delay}s between requests")
    print()
    
    total_updated = 0
    total_failed = 0
    
    for i, category in enumerate(categories):
        print(f"[{i+1}/{len(categories)}] Category: {category}")
        
        html = scrape_ml_bestsellers(category, auth)
        
        if html:
            sales_data = extract_sales_from_bestsellers(html)
            print(f"  Found {len(sales_data)} products with sales data")
            
            # Update DB for products in this category
            for mlb_id, sales in sales_data.items():
                result = execute("""
                    UPDATE products SET sales_30d = %s, last_updated = NOW()
                    WHERE platform_id = %s AND platform = 'ml' 
                      AND category_l1 = %s
                      AND (sales_30d = 0 OR sales_30d IS NULL)
                """, (sales, mlb_id, category))
                
                if result > 0:
                    total_updated += 1
                    print(f"    Updated {mlb_id}: {sales} sales")
        else:
            total_failed += 1
            print(f"  Failed to scrape")
        
        if i < len(categories) - 1:
            time.sleep(args.delay)
    
    print()
    print(f"Results: {total_updated} products updated, {total_failed} categories failed")
    
    if args.dry_run:
        print("(DRY RUN - no changes made)")

if __name__ == '__main__':
    main()
