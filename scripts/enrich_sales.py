#!/usr/bin/env python3
"""
enrich_sales.py — Fill missing sales_30d by scraping individual product pages.

Strategy:
  1. Try Decodo Scraping API (fast, bulk)
  2. Fall back to browser if Decodo rate-limited
  3. Skip products that can't be scraped

Usage:
  python3 scripts/enrich_sales.py --dry-run --marketplace ml --limit 10
  python3 scripts/enrich_sales.py --marketplace ml --limit 50 --update-db
  python3 scripts/enrich_sales.py --marketplace amazon_br --limit 50 --update-db
  python3 scripts/enrich_sales.py --marketplace amazon_usa --limit 50 --update-db
  python3 scripts/enrich_sales.py --limit 100 --update-db  # all marketplaces
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request
import ssl
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# ── Config ──────────────────────────────────────────────────────────

IS_DB = {
    'host': '34.170.210.220',
    'port': 5432,
    'dbname': 'importasimples_products',
    'user': 'importasimples',
    'password': 'R{[{f<VajbC{<kvU',
    'sslmode': 'require'
}

DECODO_API_AUTH_FILE = os.path.join(os.path.dirname(__file__), '..', 'config', 'decodo_scraping.key')
DECODO_URL = 'https://scraper-api.decodo.com/v2/scrape'


def get_decodo_auth():
    path = os.path.abspath(DECODO_API_AUTH_FILE)
    if os.path.exists(path):
        with open(path) as f:
            return f.read().strip()
    return os.environ.get('DECODO_API_AUTH', '')


def decodo_fetch(url, timeout=60):
    auth = get_decodo_auth()
    if not auth:
        return None
    payload = json.dumps({
        'url': url,
        'headless': 'html',
        'proxy_pool': 'premium',
        'locale': 'pt-br',
    }).encode()
    req = urllib.request.Request(DECODO_URL, data=payload, method='POST')
    req.add_header('Authorization', f'Basic {auth}')
    req.add_header('Content-Type', 'application/json')
    ctx = ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            body = json.loads(r.read())
        return body.get('results', [{}])[0].get('content', '')
    except Exception as e:
        return None


def curl_fetch(url, timeout=30):
    """Fallback: fetch URL via curl."""
    try:
        result = subprocess.run(
            ['curl', '-s', '-L', '--max-time', str(timeout),
             '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
             '-H', 'Accept-Language: pt-BR,pt;q=0.9',
             url],
            capture_output=True, text=True, timeout=timeout + 5
        )
        return result.stdout if result.returncode == 0 else None
    except Exception:
        return None


# ── Extractors ──────────────────────────────────────────────────────

def extract_amazon_sales(html):
    """Extract sales from Amazon product page."""
    patterns = [
        # "100+ comprados no último mês" / "50+ bought in past month"
        r'([\d,.]+)\s*\+?\s*(?:comprad|bought|adquirid).*?(?:mês|month)',
        # "Mais de 100 vendidos"
        r'[Mm]ais de\s+([\d,.]+)\s+vendid',
        # "100+ vendidos no último mês"
        r'([\d,.]+)\s*\+?\s*vendid.*?(?:mês|month|último|last)',
        # "#1 mais vendido" (BSR rank 1 — not sales but useful)
        r'#([\d,.]+)\s+.*?mais\s+vendid',
    ]
    for pat in patterns:
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            num_str = m.group(1).replace('.', '').replace(',', '.')
            try:
                return int(float(num_str))
            except ValueError:
                continue
    return None


def extract_ml_sales(html):
    """Extract sales from ML product page."""
    patterns = [
        r'([\d,.]+)\s*(mil|milhão|mi|k)?\s*(?:produtos?\s+)?vendidos',
        r'[Mm]ais de\s+([\d,.]+)\s*(mil|milhão|mi|k)?\s*(?:produtos?\s+)?vendidos',
    ]
    for pat in patterns:
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            num_str = m.group(1).replace('.', '').replace(',', '.')
            multiplier = m.group(2) if m.lastindex and m.lastindex >= 2 else None
            try:
                num = float(num_str)
            except ValueError:
                continue
            if multiplier:
                if multiplier.lower() in ('mil', 'k'):
                    num *= 1000
                elif multiplier.lower() in ('milhão', 'mi'):
                    num *= 1000000
            return int(num)
    return None


def get_product_url(marketplace, source_id):
    """Build product URL, stripping marketplace prefix if present."""
    # Strip prefix like "amazon_br:" or "mercadolivre:"
    clean_id = source_id.split(':')[-1] if ':' in source_id else source_id
    
    if marketplace == 'amazon_br':
        return f'https://www.amazon.com.br/dp/{clean_id}'
    elif marketplace == 'amazon_usa':
        return f'https://www.amazon.com/dp/{clean_id}'
    elif marketplace == 'mercadolivre':
        mlb = clean_id.replace('MLB', '')
        return f'https://www.mercadolivre.com.br/p/MLB{mlb}'
    return None


# ── Main ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Enrich sales_30d')
    parser.add_argument('--marketplace', choices=['amazon_br', 'amazon_usa', 'mercadolivre'])
    parser.add_argument('--limit', type=int, default=10)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--update-db', action='store_true')
    parser.add_argument('--delay', type=float, default=3.0)
    parser.add_argument('--method', choices=['decodo', 'curl', 'auto'], default='auto')
    args = parser.parse_args()

    import psycopg2

    print('Connecting to ImportaSimples...')
    conn = psycopg2.connect(**IS_DB)
    cur = conn.cursor()

    query_sql = '''
        SELECT id, source_id, marketplace, title, sales_30d, url
        FROM bronze_products
        WHERE source = 'arbt.ly'
        AND (sales_30d = 0 OR sales_30d IS NULL)
    '''
    params = []
    if args.marketplace:
        query_sql += ' AND marketplace = %s'
        params.append(args.marketplace)
    query_sql += ' ORDER BY marketplace, source_id LIMIT %s'
    params.append(args.limit)

    cur.execute(query_sql, params)
    products = cur.fetchall()

    print(f'Found {len(products)} products to enrich')

    if args.dry_run:
        for p in products:
            url = p[5] or get_product_url(p[2], p[1])
            print(f'  [{p[2]}] {p[1]} → {url}')
        conn.close()
        return

    # Test Decodo first
    decodo_ok = False
    if args.method in ('decodo', 'auto'):
        print('Testing Decodo API...')
        test = decodo_fetch('https://www.amazon.com.br', timeout=15)
        if test and len(test) > 1000:
            print('  ✅ Decodo working')
            decodo_ok = True
        else:
            print('  ❌ Decodo rate-limited, using curl fallback')

    # Scrape
    updated = 0
    errors = 0
    skipped = 0

    for i, p in enumerate(products):
        db_id, source_id, marketplace, title, current_sales, existing_url = p
        clean_id = source_id.split(':')[-1] if ':' in source_id else source_id
        product_url = existing_url or get_product_url(marketplace, source_id)
        
        print(f'[{i+1}/{len(products)}] {marketplace}:{clean_id} — {title[:45]}...', end=' ', flush=True)

        if not product_url:
            print('SKIP (no URL)')
            skipped += 1
            continue

        html = None
        if decodo_ok and args.method in ('decodo', 'auto'):
            html = decodo_fetch(product_url)
            if not html or len(html) < 1000:
                html = None
        
        if not html and args.method in ('curl', 'auto'):
            html = curl_fetch(product_url)

        if not html or len(html) < 1000:
            print('SKIP (empty)')
            errors += 1
            time.sleep(args.delay)
            continue

        # Extract sales
        if marketplace in ('amazon_br', 'amazon_usa'):
            sales = extract_amazon_sales(html)
        elif marketplace == 'mercadolivre':
            sales = extract_ml_sales(html)
        else:
            sales = None

        if sales and sales > 0:
            print(f'✅ sales={sales}')
            if args.update_db:
                cur.execute('''
                    UPDATE bronze_products
                    SET sales_30d = %s
                    WHERE id = %s AND (sales_30d = 0 OR sales_30d IS NULL OR sales_30d < %s)
                ''', (sales, db_id, sales))
                conn.commit()
            updated += 1
        else:
            # Try to extract review count as fallback info
            review_m = re.search(r'([\d,.]+)\s*(?:avaliações|ratings|reviews)', html[:50000], re.IGNORECASE)
            if review_m:
                print(f'no sales (reviews: {review_m.group(1)})')
            else:
                print('no sales found')
            skipped += 1

        time.sleep(args.delay)

    # Summary
    print(f'\n{"="*50}')
    print(f'Updated: {updated} | No sales: {skipped} | Errors: {errors}')

    if args.update_db:
        cur.execute('''
            SELECT marketplace,
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE sales_30d > 0) as has_sales
            FROM bronze_products WHERE source = 'arbt.ly'
            GROUP BY marketplace ORDER BY marketplace
        ''')
        print(f'\nAfter enrichment:')
        for r in cur.fetchall():
            gap = r[1] - r[2]
            print(f'  {r[0]:<18} {r[2]:>4}/{r[1]:<4} have sales  (gap: {gap})')

    conn.close()


if __name__ == '__main__':
    main()
