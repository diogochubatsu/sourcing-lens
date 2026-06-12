#!/usr/bin/env python3 -u
"""Scrape automotive tools from Mercado Livre via Decodo API."""
import os, sys, re, time, json, requests
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import imagehash

sys.path.insert(0, '/mnt/ssd/arbitlens')
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Load .env
env_path = '/mnt/ssd/arbitlens/config/.env'
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                if k not in os.environ:
                    os.environ[k] = v

DECODO_USER = os.environ['DECODO_USER']
DECODO_PASS = os.environ['DECODO_PASS']
DECODO_API = 'https://scraper-api.decodo.com/v2/scrape'

DB_CONFIG = dict(host='localhost', port=5432, user='hermes1688',
                 password='Lndgcp@#12', dbname='arbtbr')

import psycopg2
import psycopg2.extras

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

def execute(sql, params=None):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        rc = cur.rowcount
        cur.close()
        return rc
    finally:
        conn.close()

def execute_returning(sql, params=None):
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params)
        result = cur.fetchall()
        conn.commit()
        cur.close()
        return result
    finally:
        conn.close()


def fetch_ml_html(search_url):
    auth = (DECODO_USER, DECODO_PASS)
    payload = {'url': search_url, 'headless': 'html', 'proxy_pool': 'premium', 'locale': 'pt-br'}
    print(f'  Fetching: {search_url}', flush=True)
    r = requests.post(DECODO_API, json=payload, auth=auth, timeout=120)
    r.raise_for_status()
    data = json.loads(r.text)
    if data.get('status') == 'failed':
        raise Exception(f"Decodo API failed: {data.get('message')}")
    return data['results'][0]['content']


def extract_wid(url):
    parsed = urlparse(url)
    qs = parse_qs(parsed.fragment if parsed.fragment else parsed.query)
    if 'wid' in qs:
        return qs['wid'][0]
    qs2 = parse_qs(parsed.query)
    if 'wid' in qs2:
        return qs2['wid'][0]
    return None


def extract_products(html):
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.select('div.poly-card')
    if not cards:
        cards = soup.select('ol.ui-search-layout li.ui-search-layout__item')
    if not cards:
        cards = soup.select('[class*="poly-card"], [class*="ui-search-result"]')
    
    products = []
    seen_wids = set()
    
    for card in cards:
        try:
            title_el = card.select_one('a.poly-component__title, a.ui-search-item__group__element a, h2 a')
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            href = title_el.get('href', '')
            if not href:
                continue
            
            platform_id = extract_wid(href)
            if not platform_id or platform_id in seen_wids:
                continue
            seen_wids.add(platform_id)
            
            # Price
            price_el = card.select_one('.andes-money-amount--cents-superscript .andes-money-amount__fraction')
            if not price_el:
                price_el = card.select_one('[class*="money-amount"] [class*="fraction"]')
            price = None
            if price_el:
                price_str = price_el.get_text(strip=True)
                cents_el = card.select_one('.andes-money-amount--cents-superscript .andes-money-amount__cents, [class*="money-amount"] [class*="cents"]')
                if cents_el:
                    price_str += '.' + cents_el.get_text(strip=True)
                price = float(price_str.replace(',', '.'))
            
            # Image
            img_el = card.select_one('img.poly-component__picture, img[data-src], img.ui-search-result-image__element')
            image_url = None
            if img_el:
                image_url = img_el.get('data-src') or img_el.get('src')
            
            # Supplier
            seller_el = card.select_one('span.poly-component__seller, span.ui-search-result__seller')
            supplier_name = None
            if seller_el:
                brand_span = seller_el.find('span')
                supplier_name = brand_span.get_text(strip=True) if brand_span else seller_el.get_text(strip=True).split(' por ')[0].strip()
            
            # Review
            review_el = card.select_one('span.poly-component__review-compacted, span.ui-search-reviews__rating')
            review_avg = None
            if review_el:
                try:
                    review_avg = float(review_el.get_text(strip=True).replace(',', '.'))
                except ValueError:
                    pass
            
            # Sales
            sales_text = None
            vendido_el = card.find(string=re.compile(r'MAIS VENDIDO', re.IGNORECASE))
            if vendido_el:
                sales_text = 'MAIS VENDIDO'
            
            if not price:
                continue
            
            # Build full URL
            if not href.startswith('http'):
                href = 'https://www.mercadolivre.com.br' + href
            
            products.append({
                'platform': 'ml',
                'platform_id': platform_id,
                'title': title,
                'price': price,
                'currency': 'BRL',
                'url': href,
                'image_url': image_url,
                'image_urls': [image_url] if image_url else [],
                'sales_30d': None,
                'sales_30d_text': sales_text,
                'review_avg': review_avg,
                'supplier_name': supplier_name,
                'is_active': True,
                'image_hash': None
            })
        except Exception as e:
            print(f'    Parse error: {e}', flush=True)
            continue
    
    return products


def download_phash(image_url):
    if not image_url:
        return None
    try:
        r = requests.get(image_url, timeout=30)
        r.raise_for_status()
        img = Image.open(BytesIO(r.content))
        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')
        return str(imagehash.phash(img))
    except Exception as e:
        print(f'    Image error: {e}', flush=True)
        return None


def insert_product(prod, category):
    sql = """
        INSERT INTO products 
            (platform, platform_id, title, price, currency, url, image_urls, 
             sales_30d, sales_30d_text, review_avg, review_count, category, 
             is_active, image_hash, supplier_name)
        VALUES 
            (%(platform)s, %(platform_id)s, %(title)s, %(price)s, %(currency)s, 
             %(url)s, %(image_urls)s, %(sales_30d)s, %(sales_30d_text)s, 
             %(review_avg)s, %(review_count)s, %(category)s, %(is_active)s, 
             %(image_hash)s, %(supplier_name)s)
        ON CONFLICT (platform, platform_id) DO NOTHING
        RETURNING id
    """
    params = {**prod, 'category': category, 'review_count': None}
    try:
        result = execute_returning(sql, params)
        return len(result) > 0
    except Exception as e:
        print(f'    DB error: {e}', flush=True)
        return False


def process(category, search_name, search_url):
    print(f'\n{"="*60}', flush=True)
    print(f'{category} - {search_name}', flush=True)
    print(f'{search_url}', flush=True)
    print(f'{"="*60}', flush=True)
    
    try:
        html = fetch_ml_html(search_url)
    except Exception as e:
        print(f'  FAIL: {e}', flush=True)
        return []
    
    products = extract_products(html)
    print(f'  Found {len(products)} products', flush=True)
    
    inserted = 0
    skipped = 0
    prices = []
    
    for i, prod in enumerate(products):
        print(f'  [{i+1}/{len(products)}] {prod["title"][:60]}...', flush=True)
        
        phash = download_phash(prod['image_url'])
        if phash:
            prod['image_hash'] = phash
        
        if insert_product(prod, category):
            inserted += 1
            prices.append(prod['price'])
            print(f'    INSERTED R${prod["price"]:.2f} hash={phash}', flush=True)
        else:
            skipped += 1
            print(f'    SKIPPED (exists)', flush=True)
        
        if i < len(products) - 1:
            time.sleep(3)
    
    print(f'  Result: {inserted} inserted, {skipped} skipped', flush=True)
    if prices:
        print(f'  Price range: R${min(prices):.2f} - R${max(prices):.2f}', flush=True)
    return products


if __name__ == '__main__':
    print('Starting ML automotive tool extraction...', flush=True)
    
    # Search for various automotive and hand tools
    searches = [
        ('automotive_tool', 'ferramentas automotivas',
         'https://lista.mercadolivre.com.br/ferramentas-automotivas'),
        ('automotive_tool', 'jogo de soquetes',
         'https://lista.mercadolivre.com.br/jogo-de-soquetes'),
        ('automotive_tool', 'kit ferramentas',
         'https://lista.mercadolivre.com.br/kit-ferramentas'),
        ('automotive_tool', 'chave combinada',
         'https://lista.mercadolivre.com.br/chave-combinada'),
        ('automotive_tool', 'alicate ferramenta',
         'https://lista.mercadolivre.com.br/alicate-ferramenta'),
        ('automotive_tool', 'parafusadeira eletrica',
         'https://lista.mercadolivre.com.br/parafusadeira-eletrica'),
        ('automotive_tool', 'furadeira impacto',
         'https://lista.mercadolivre.com.br/furadeira-impacto'),
    ]
    
    total_inserted = 0
    total_skipped = 0
    
    for cat, name, url in searches:
        prods = process(cat, name, url)
        ins = sum(1 for p in prods if p.get('_inserted', False))
        # Count via returned products
        total_inserted += ins
        time.sleep(6)  # Wait 6 seconds between ML searches
    
    print(f'\n{"="*60}', flush=True)
    print(f'ML Extraction Complete', flush=True)
    print(f'{"="*60}', flush=True)
