#!/usr/bin/env python3
"""
enrich_sales_bestsellers.py — Enrich sales_30d by scraping best sellers pages.

Strategy:
- Amazon: scrape /gp/bestsellers/{category_id} → extract "X+ bought in past month"
- ML: scrape /mais-vendidos/MLB{id} → extract "X vendidos" (total lifetime)

Only updates products that are found in best sellers lists.
Does NOT use estimates — only real data from best sellers pages.

Usage:
  python3 scripts/enrich_sales_bestsellers.py --dry-run
  python3 scripts/enrich_sales_bestsellers.py --marketplace amazon_br --update-db
  python3 scripts/enrich_sales_bestsellers.py --marketplace ml --update-db
  python3 scripts/enrich_sales_bestsellers.py --update-db  # all
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

# ── Config ──────────────────────────────────────────────────────────

IS_DB = {
    'host': '34.170.210.220',
    'port': 5432,
    'dbname': 'importasimples_products',
    'user': 'importasimples',
    'password': 'R{[{f<VajbC{<kvU',
    'sslmode': 'require'
}

DECODO_API_AUTH_FILE=os.path.join(os.path.dirname(__file__), "..", "config", "decodo_scraping.key")
DECODO_URL = 'https://scraper-api.decodo.com/v2/scrape'

# Amazon BR category IDs for best sellers
AMAZON_BR_CATEGORIES = {
    'Audio': '14513987011',
    'Moda': '14513987011',  # placeholder
    'Home': '14513987011',
    'Photography': '14513987011',
    'Tools': '14513987011',
    'Lighting': '14513987011',
    'Pet': '14513987011',
    'Tech': '14513987011',
    'Kitchen': '14513987011',
    'Meias': '14513987011',
    'Moda Intima': '14513987011',
    'Sports': '14513987011',
    'Automotive': '14513987011',
    'Musical': '14513987011',
    'Acessórios Mobile': '14513987011',
    'Toys': '14513987011',
    'Health': '14513987011',
    'Fashion': '14513987011',
    'Cozinha': '14513987011',
    'Praia': '14513987011',
    'Brinquedos': '14513987011',
    'Beleza': '14513987011',
    'Bebê': '14513987011',
    'Ferramentas': '14513987011',
    'Esportes': '14513987011',
    'Fotografia': '14513987011',
    'Casa': '14513987011',
    'Wearables': '14513987011',
    'Iluminação': '14513987011',
}

# ML category IDs for best sellers
ML_CATEGORIES = {
    'Audio': 'MLB3835',
    'Tech': 'MLB1000',
    'Health': 'MLB1246',
    'Sports': 'MLB1276',
    'Home': 'MLB1574',
    'Pet': 'MLB1071',
    'Tools': 'MLB263532',
    'Bebê': 'MLB1384',
    'Photography': 'MLB1039',
    'Esportes': 'MLB1276',
    'Acessórios Mobile': 'MLB3813',
    'Brinquedos': 'MLB1132',
    'Casa': 'MLB1574',
    'Beleza': 'MLB1246',
    'Toys': 'MLB1132',
    'Praia': 'MLB430391',
    'Iluminação': 'MLB430378',
    'Lighting': 'MLB430378',
    'Fotografia': 'MLB1039',
    'Ferramentas': 'MLB263532',
    'Moda': 'MLB1430',
    'Bolsas': 'MLB1457',
    'Fashion': 'MLB1430',
    'Moda Intima': 'MLB108786',
    'Meias': 'MLB1430',
    'Pet Shop': 'MLB1071',
    'Wearables': 'MLB417704',
    'Mochilas': 'MLB3127',
}


def get_decodo_auth():
    path = os.path.abspath(DECODO_API_AUTH_FILE)
    if os.path.exists(path):
        with open(path) as f:
            return f.read().strip()
    return os.environ.get('DECODO_API_AUTH', '')


def decodo_fetch(url, timeout=90):
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
        print(f'  Decodo error: {e}')
        return None


def extract_amazon_bestsellers(html):
    """Extract products from Amazon best sellers page."""
    products = []
    
    # Pattern for product cards
    # Amazon best sellers show: rank, title, price, reviews, "X+ bought in past month"
    
    # Find all ASINs
    asins = re.findall(r'data-asin="([A-Z0-9]{10})"', html)
    
    for asin in set(asins):
        # Find the block around this ASIN
        pos = html.find(f'data-asin="{asin}"')
        if pos < 0:
            continue
        block = html[max(0, pos-500):pos+2000]
        
        # Extract sales
        sales = None
        sales_match = re.search(r'([\d,.]+)\s*\+?\s*(?:comprad|bought|adquirid).*?(?:mês|month)', block, re.IGNORECASE)
        if sales_match:
            num_str = sales_match.group(1).replace('.', '').replace(',', '.')
            try:
                sales = int(float(num_str))
            except ValueError:
                pass
        
        # Extract reviews count
        reviews = None
        rev_match = re.search(r'([\d,.]+)\s*(?:avaliaç|ratings|reviews)', block, re.IGNORECASE)
        if rev_match:
            num_str = rev_match.group(1).replace('.', '').replace(',', '.')
            try:
                reviews = int(float(num_str))
            except ValueError:
                pass
        
        if sales or reviews:
            products.append({
                'asin': asin,
                'sales': sales,
                'reviews': reviews,
            })
    
    return products


def extract_ml_bestsellers(html):
    """Extract products from ML best sellers page."""
    products = []
    
    # Find all MLB IDs
    mlb_ids = re.findall(r'"product_id":"(MLB\d+)"', html)
    if not mlb_ids:
        mlb_ids = re.findall(r'MLB(\d{8,})', html)
        mlb_ids = [f'MLB{mid}' for mid in mlb_ids]
    
    for mlb_id in set(mlb_ids):
        # Find block around this product
        pos = html.find(mlb_id)
        if pos < 0:
            continue
        block = html[max(0, pos-500):pos+3000]
        
        # Extract sales (total lifetime)
        sales = None
        sales_match = re.search(r'([\d,.]+)\s*(mil|milhão|mi|k)?\s*(?:produtos?\s+)?vendidos', block, re.IGNORECASE)
        if sales_match:
            num_str = sales_match.group(1).replace('.', '').replace(',', '.')
            multiplier = sales_match.group(2) if sales_match.lastindex and sales_match.lastindex >= 2 else None
            try:
                num = float(num_str)
            except ValueError:
                continue
            if multiplier:
                if multiplier.lower() in ('mil', 'k'):
                    num *= 1000
                elif multiplier.lower() in ('milhão', 'mi'):
                    num *= 1000000
            sales = int(num)
        
        # Extract price
        price = None
        price_match = re.search(r'"current_price":\{"value":([\d.]+)', block)
        if price_match:
            try:
                price = float(price_match.group(1))
            except ValueError:
                pass
        
        if sales:
            products.append({
                'platform_id': mlb_id,
                'sales': sales,
                'price': price,
            })
    
    return products


def main():
    parser = argparse.ArgumentParser(description='Enrich sales_30d from best sellers pages')
    parser.add_argument('--marketplace', choices=['amazon_br', 'amazon_usa', 'mercadolivre'])
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--update-db', action='store_true')
    parser.add_argument('--delay', type=float, default=5.0)
    args = parser.parse_args()

    import psycopg2

    print('Connecting to ImportaSimples...')
    conn = psycopg2.connect(**IS_DB)
    cur = conn.cursor()

    # Get categories that need sales
    cat_query = '''
        SELECT marketplace, category_l1, COUNT(*) as no_sales
        FROM bronze_products
        WHERE source = 'arbt.ly'
        AND (sales_30d = 0 OR sales_30d IS NULL)
        GROUP BY marketplace, category_l1
        HAVING COUNT(*) > 0
        ORDER BY marketplace, no_sales DESC
    '''
    cur.execute(cat_query)
    categories = cur.fetchall()

    if args.marketplace:
        categories = [c for c in categories if c[0] == args.marketplace]

    print(f'\nFound {len(categories)} category/marketplace combos to scrape\n')

    total_updated = 0
    total_not_found = 0

    for marketplace, category_l1, no_sales in categories:
        print(f'\n{"="*60}')
        print(f'{marketplace} / {category_l1} ({no_sales} products without sales)')
        print(f'{"="*60}')

        # Get products in this category without sales
        cur.execute('''
            SELECT id, source_id, title, sales_30d
            FROM bronze_products
            WHERE source = 'arbt.ly'
            AND marketplace = %s
            AND category_l1 = %s
            AND (sales_30d = 0 OR sales_30d IS NULL)
        ''', (marketplace, category_l1))
        products = cur.fetchall()

        if not products:
            print('  No products to enrich')
            continue

        # Build lookup by source_id (strip prefix)
        lookup = {}
        for p in products:
            clean_id = p[1].split(':')[-1] if ':' in p[1] else p[1]
            lookup[clean_id] = {'db_id': p[0], 'source_id': p[1], 'title': p[2]}

        # Build best sellers URL
        if marketplace in ('amazon_br', 'amazon_usa'):
            cat_id = AMAZON_BR_CATEGORIES.get(category_l1)
            if not cat_id:
                print(f'  No category ID mapping for {category_l1}')
                continue
            if marketplace == 'amazon_usa':
                url = f'https://www.amazon.com/gp/bestsellers/{cat_id}'
            else:
                url = f'https://www.amazon.com.br/gp/bestsellers/{cat_id}'
        elif marketplace == 'mercadolivre':
            mlb_id = ML_CATEGORIES.get(category_l1)
            if not mlb_id:
                print(f'  No ML category ID mapping for {category_l1}')
                continue
            url = f'https://www.mercadolivre.com.br/mais-vendidos/{mlb_id}'
        else:
            continue

        print(f'  URL: {url}')

        if args.dry_run:
            print(f'  Products to match: {len(lookup)}')
            continue

        # Fetch best sellers page
        html = decodo_fetch(url)
        if not html or len(html) < 1000:
            print(f'  ❌ Failed to fetch (empty response)')
            time.sleep(args.delay)
            continue

        # Extract products
        if marketplace in ('amazon_br', 'amazon_usa'):
            bs_products = extract_amazon_bestsellers(html)
        elif marketplace == 'mercadolivre':
            bs_products = extract_ml_bestsellers(html)
        else:
            bs_products = []

        print(f'  Found {len(bs_products)} products in best sellers')

        # Match and update
        matched = 0
        for bs in bs_products:
            pid = bs.get('asin') or bs.get('platform_id')
            sales = bs.get('sales')
            
            if pid in lookup and sales and sales > 0:
                db_id = lookup[pid]['db_id']
                if args.update_db:
                    cur.execute('''
                        UPDATE bronze_products
                        SET sales_30d = %s
                        WHERE id = %s AND (sales_30d = 0 OR sales_30d IS NULL OR sales_30d < %s)
                    ''', (sales, db_id, sales))
                matched += 1
                total_updated += 1

        if args.update_db:
            conn.commit()

        print(f'  ✅ Matched: {matched}/{len(lookup)} products updated')
        total_not_found += len(lookup) - matched

        time.sleep(args.delay)

    # Final summary
    print(f'\n{"="*60}')
    print(f'ENRICHMENT COMPLETE')
    print(f'{"="*60}')
    print(f'  Updated: {total_updated}')
    print(f'  Not found in best sellers: {total_not_found}')

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
