#!/usr/bin/env python3
"""
scrape_ml_sales.py — Scrape individual ML product pages for sales data.

ML product pages show "X+ vendidos" or "X mil+ vendidos" on the page.
This script scrapes each product page and extracts the sales count.

Usage:
  python3 scripts/scrape_ml_sales.py --dry-run --limit 5
  python3 scripts/scrape_ml_sales.py --limit 10 --update-db
  python3 scripts/scrape_ml_sales.py --update-db  # all without sales
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

def get_decodo_auth():
    path = os.path.abspath(DECODO_API_AUTH_FILE)
    if os.path.exists(path):
        with open(path) as f:
            return f.read().strip()
    return os.environ.get('DECODO_API_AUTH', '')

def scrape_ml_product(url, auth):
    """Scrape a single ML product page using Decodo."""
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

def extract_sales_from_html(html):
    """Extract sales count from ML product page HTML."""
    if not html:
        return None
    
    # ML shows sales like "100+ vendidos" or "1k+ vendidos" or "50 mil+ vendidos"
    # Pattern 1: "X+ vendidos" or "X vendidos"
    patterns = [
        r'(\d[\d.,]*)\+?\s*vendidos',
        r'(\d[\d.,]*)\s*vendido',
        r'(\d+)\s*mil\+?\s*vendidos',
        r'(\d+)\s*mil\s*vendidos',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            num_str = match.group(1).replace('.', '').replace(',', '')
            try:
                num = int(num_str)
                # Check if "mil" is in the context
                if 'mil' in html[max(0, match.start()-10):match.end()+10].lower():
                    num *= 1000
                return num
            except:
                continue
    
    return None

def main():
    parser = argparse.ArgumentParser(description='Scrape ML product pages for sales data')
    parser.add_argument('--dry-run', action='store_true', help='Preview without updating DB')
    parser.add_argument('--limit', type=int, default=10, help='Number of products to scrape')
    parser.add_argument('--update-db', action='store_true', help='Update database with scraped data')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay between requests (seconds)')
    args = parser.parse_args()
    
    auth = get_decodo_auth()
    if not auth:
        print("ERROR: No Decodo API key found")
        sys.exit(1)
    
    # Get ML products without sales
    products = query("""
        SELECT id, platform_id, title, url
        FROM products 
        WHERE is_active = true 
          AND platform = 'ml'
          AND (sales_30d = 0 OR sales_30d IS NULL)
        ORDER BY RANDOM()
        LIMIT %s
    """, (args.limit,))
    
    print(f"Scraping {len(products)} ML products for sales data...")
    print(f"Delay: {args.delay}s between requests")
    print()
    
    updated = 0
    failed = 0
    
    for i, p in enumerate(products):
        mlb_id = p['platform_id']
        url = f"https://www.mercadolivre.com.br/p/{mlb_id}"
        
        print(f"[{i+1}/{len(products)}] {mlb_id}: {p['title'][:50]}...")
        
        html = scrape_ml_product(url, auth)
        
        if html:
            sales = extract_sales_from_html(html)
            if sales:
                print(f"  Found sales: {sales}")
                if args.update_db and not args.dry_run:
                    execute("""
                        UPDATE products SET sales_30d = %s, last_updated = NOW()
                        WHERE id = %s
                    """, (sales, p['id']))
                    updated += 1
                    print(f"  Updated in DB")
            else:
                print(f"  No sales data found in HTML")
                failed += 1
        else:
            print(f"  Failed to scrape")
            failed += 1
        
        if i < len(products) - 1:
            time.sleep(args.delay)
    
    print()
    print(f"Results: {updated} updated, {failed} failed")
    
    if args.dry_run:
        print("(DRY RUN - no changes made)")

if __name__ == '__main__':
    main()
