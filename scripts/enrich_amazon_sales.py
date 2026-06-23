#!/usr/bin/env python3
"""
Amazon Sales Enricher — fetch /dp/{ASIN} for products with NULL sales_30d.

Uses Decodo Site Unblocker (SU) as forward proxy to bypass Amazon bot detection.
Parses patterns:
- "Mais de X mil compras no mês passado" → X * 1000
- "Mais de X compras no mês passado" → X
- "X bought in past month" → X (Amazon US)

Usage:
    python3 scripts/enrich_amazon_sales.py --platform amazon_br --limit 20 --delay 4
    python3 scripts/enrich_amazon_sales.py --platform amazon_us --limit 20 --delay 4
"""
import os
import sys
import re
import ssl
import time
import argparse
import urllib.request
import urllib.error
import socket
import json
import base64
import requests
from pathlib import Path

sys.path.insert(0, '/mnt/ssd/arbitlens')
os.environ['PGPASSFILE'] = '/tmp/.pgpass'

import psycopg2
import psycopg2.extras

# SSL self-signed for SU
ssl._create_default_https_context = ssl._create_unverified_context

# Load SU credentials
SU_KEY_FILE = '/tmp/decodo_keys/su.key'


def get_opener():
    """Build urllib opener with SU proxy."""
    with open(SU_KEY_FILE) as f:
        su_auth = f.read().strip()
    proxy_handler = urllib.request.ProxyHandler({
        'http': f'http://{su_auth}@unblock.decodo.com:60000',
        'https': f'http://{su_auth}@unblock.decodo.com:60000',
    })
    opener = urllib.request.build_opener(proxy_handler)
    opener.addheaders = [
        ('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'),
        ('Accept-Language', 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7'),
        ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
        ('X-SU-Locale', 'pt-br'),
        ('X-SU-Device-Type', 'desktop'),
        ('X-SU-Headless', 'html'),
    ]
    return opener


def fetch_via_scraping_api(url, platform):
    """Fetch URL via Decodo Scraping API (more reliable than SU for product pages)."""
    with open('/mnt/ssd/arbitlens/config/decodo_scraping.key') as f:
        auth_b64 = f.read().strip()
    # If file contains raw auth (user:pass), base64-encode it
    if not auth_b64.startswith('VTA'):
        auth_b64 = base64.b64encode(auth_b64.encode()).decode()
    headers = {
        'Authorization': f'Basic {auth_b64}',
        'Content-Type': 'application/json',
    }
    payload = {
        'url': url,
        'headless': 'html',
        'proxy_pool': 'premium',
        'locale': 'pt-br' if platform == 'amazon_br' else 'en-us',
        'timeout': 60,
    }
    for attempt in range(2):
        try:
            resp = requests.post('https://scraper-api.decodo.com/v2/scrape',
                                 headers=headers, json=payload, timeout=90)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get('results', [])
                if results and results[0].get('content'):
                    return results[0].get('content')
                print(f'   [scraping-api empty content]')
            else:
                print(f'   [scraping-api status {resp.status_code}]')
        except Exception as e:
            print(f'   [scraping-api error: {e}]')
        time.sleep(2)
    return None


def parse_sales_from_html(html, platform):
    """Extract 30-day sales from product page HTML.

    Returns (sales_int, sales_text) or (None, None).
    """
    # First, normalize HTML to remove tags between "Mais de" and "no mês passado"
    # Pattern: "Mais de X&nbsp;mil compras</span><span> no mês passado"
    # Use a more flexible regex that handles split spans

    # First, normalize the split-span pattern: "X&nbsp;mil compras</span><span> no mês passado"
    # → "X mil compras no mês passado"
    normalized = re.sub(r'&nbsp;', ' ', html)
    # Remove simple split spans
    normalized = re.sub(r'</span>\s*<span[^>]*>\s*', ' ', normalized)

    # Pattern 1: "Mais de X mil compras no mês passado" (BR)
    m = re.search(
        r'mais de\s+([\d.,]+)\s+mil\s+compras?\s+no\s+m[êe]s\s+passado',
        normalized, re.IGNORECASE
    )
    if m:
        num = float(m.group(1).replace('.', '').replace(',', '.'))
        return int(num * 1000), m.group(0)

    # Pattern 2: "Mais de X compras no mês passado" (BR, no "mil")
    m = re.search(
        r'mais de\s+([\d.,]+)\s+compras?\s+no\s+m[êe]s\s+passado',
        normalized, re.IGNORECASE
    )
    if m:
        num = float(m.group(1).replace('.', '').replace(',', '.'))
        return int(num), m.group(0)

    # Pattern 3: "X bought in past month" (US)
    m = re.search(r'([\d,]+)\+?\s+bought\s+in\s+past\s+month',
                  html, re.IGNORECASE)
    if m:
        num = int(m.group(1).replace(',', '').replace('.', ''))
        return num, m.group(0)

    # Pattern 4: "X+ bought in past month" (US with +)
    m = re.search(r'([\d,]+)\+\s+bought\s+in\s+past\s+month',
                  html, re.IGNORECASE)
    if m:
        num = int(m.group(1).replace(',', '').replace('.', ''))
        return num, m.group(0)

    return None, None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--platform', choices=['amazon_br', 'amazon_us'], required=True)
    parser.add_argument('--limit', type=int, default=20, help='Max products to enrich')
    parser.add_argument('--delay', type=float, default=4.0, help='Seconds between requests')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    # Get products with NULL sales
    conn = psycopg2.connect(host='localhost', database='arbtbr', user='hermes1688')
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        SELECT id, platform_id, title
        FROM products
        WHERE platform = %s
          AND is_active = true
          AND sales_30d IS NULL
        ORDER BY id
        LIMIT %s
    """, (args.platform, args.limit))

    products = cur.fetchall()
    print(f"Found {len(products)} {args.platform} products with NULL sales")
    if not products:
        return

    opener = get_opener()
    base_url = 'https://www.amazon.com.br' if args.platform == 'amazon_br' else 'https://www.amazon.com'
    socket.setdefaulttimeout(90)

    updated = 0
    failed = 0
    for i, p in enumerate(products, 1):
        url = f'{base_url}/dp/{p["platform_id"]}'
        print(f'[{i}/{len(products)}] {p["platform_id"]} - {p["title"][:50]}... ', end='', flush=True)

        # Try Scraping API first (more reliable), then SU as fallback
        html = fetch_via_scraping_api(url, args.platform)
        if html is None:
            # Fallback to SU
            for attempt in range(2):
                try:
                    resp = opener.open(url, timeout=90)
                    html = resp.read().decode('utf-8', errors='ignore')
                    break
                except Exception as e:
                    if attempt == 1:
                        print(f'✗ SU also failed: {e}')
                    time.sleep(args.delay * 0.5)

        # If both methods failed, skip
        if html is None:
            print(f'✗ All methods failed')
            failed += 1
            time.sleep(args.delay)
            continue

        # Check for captcha / block
        if 'captcha' in html.lower() or 'enter the characters' in html.lower():
            print(f'⚠️  CAPTCHA')
            failed += 1
            time.sleep(args.delay * 2)
            continue

        sales, sales_text = parse_sales_from_html(html, args.platform)
        if sales is None and 'compras no mês' in html.lower():
            # Save debug HTML
            debug_path = f'/tmp/debug_{args.platform}_{p["platform_id"]}.html'
            with open(debug_path, 'w') as f:
                f.write(html)

        if sales is not None:
            print(f'✓ sales={sales}')
            if not args.dry_run:
                cur.execute("""
                    UPDATE products
                    SET sales_30d = %s
                    WHERE id = %s
                """, (sales, sales_text[:200] if sales_text else None, p['id']))
            updated += 1
        else:
            # Save HTML for debugging
            debug_path = f'/tmp/debug_{args.platform}_{p["platform_id"]}.html'
            with open(debug_path, 'w') as f:
                f.write(html)
            # Check for "Mais de" existence
            if 'Mais de' in html:
                print(f'✗ "Mais de" exists but pattern failed (saved {debug_path})')
            else:
                print(f'✗ no sales pattern found (saved {debug_path})')
            failed += 1

        if not args.dry_run:
            conn.commit()

        time.sleep(args.delay)

    conn.close()
    print(f"\n{'='*60}")
    print(f"Updated: {updated}, Failed: {failed}, Total: {len(products)}")
    if args.dry_run:
        print("(dry run, no changes)")


if __name__ == "__main__":
    main()
