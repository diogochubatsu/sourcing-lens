#!/usr/bin/env python3 -u
"""Extract ML products from Decodo HTML and insert into DB."""
import os, sys, re, time, json, requests
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import imagehash
import psycopg2
import psycopg2.extras

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Load .env
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', '.env')
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

DB_CONFIG = dict(host="localhost", port=5432, user='hermes1688',
                 password='Lndgcp@#12', dbname='arbtbr')


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
    products = []
    
    for card in cards:
        try:
            title_el = card.select_one('a.poly-component__title')
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            href = title_el.get('href', '')
            platform_id = extract_wid(href)
            if not platform_id:
                continue
            
            # Price
            price_el = card.select_one('.andes-money-amount--cents-superscript .andes-money-amount__fraction')
            if not price_el:
                continue
            price_str = price_el.get_text(strip=True)
            cents_el = card.select_one('.andes-money-amount--cents-superscript .andes-money-amount__cents')
            if cents_el:
                price_str += '.' + cents_el.get_text(strip=True)
            price = float(price_str.replace(',', '.'))
            
            # Image
            img_el = card.select_one('img.poly-component__picture')
            image_url = None
            if img_el:
                image_url = img_el.get('data-src') or img_el.get('src')
            
            # Supplier
            seller_el = card.select_one('span.poly-component__seller')
            supplier_name = None
            if seller_el:
                brand_span = seller_el.find('span')
                supplier_name = brand_span.get_text(strip=True) if brand_span else seller_el.get_text(strip=True).split(' por ')[0].strip()
            
            # Review
            review_el = card.select_one('span.poly-component__review-compacted')
            review_avg = None
            if review_el:
                try:
                    review_avg = float(review_el.get_text(strip=True).replace(',', '.'))
                except ValueError:
                    pass
            
            # Sales
            vendido_el = card.find(string=re.compile(r'MAIS VENDIDO', re.IGNORECASE))
            sales_text = 'MAIS VENDIDO' if vendido_el else None
            
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
        time.sleep(3)
        
        if insert_product(prod, category):
            inserted += 1
            prices.append(prod['price'])
            print(f'    INSERTED R${prod["price"]:.2f} hash={phash}', flush=True)
        else:
            skipped += 1
            print(f'    SKIPPED (exists)', flush=True)
    
    print(f'  Result: {inserted} inserted, {skipped} skipped', flush=True)
    if prices:
        print(f'  Price range: R${min(prices):.2f} - R${max(prices):.2f}', flush=True)
    return products


if __name__ == '__main__':
    print('Starting ML product extraction...', flush=True)
    
    process('home_organization', 'copo stanley quencher',
            'https://lista.mercadolivre.com.br/copo-stanley-quencher')
    
    process('sports', 'air tag rastreador',
            'https://lista.mercadolivre.com.br/air-tag-rastreador')
    
    process('sports', 'localizador gps',
            'https://lista.mercadolivre.com.br/localizador-gps')
    
    print('\nDone!', flush=True)
