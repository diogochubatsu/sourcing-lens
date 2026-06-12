#!/usr/bin/env python3
"""Scrape automotive tools from Mercado Livre via Decodo API."""
import os, sys, re, time, json, requests
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import imagehash

sys.path.insert(0, '/mnt/ssd/arbitlens')

# Load .env
env_path = '/mnt/ssd/arbitlens/config/.env'
for line in open(env_path):
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        if k not in os.environ:
            os.environ[k] = v

DECODO_USER = os.environ['DECODO_USER']
DECODO_PASS = os.environ['DECODO_PASS']
DECODO_API = 'https://scraper-api.decodo.com/v2/scrape'

from scripts.db import execute_returning

def fetch_ml_html(search_url):
    auth = (DECODO_USER, DECODO_PASS)
    payload = {'url': search_url, 'headless': 'html', 'proxy_pool': 'premium', 'locale': 'pt-br'}
    print(f'  Fetching: {search_url}')
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
        cards = soup.select('li.ui-search-layout__item')
    if not cards:
        cards = soup.select('[id^="searchResults"] li')
    
    products = []
    seen_wids = set()
    
    for card in cards:
        try:
            title_el = card.select_one('a.poly-component__title, .ui-search-item__group__element a, h2 a, a.ui-search-link')
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            href = str(title_el.get('href', ''))
            if not href:
                continue
            
            platform_id = extract_wid(href)
            if not platform_id or platform_id in seen_wids:
                continue
            seen_wids.add(platform_id)
            
            # Price
            price_el = card.select_one('.andes-money-amount__fraction')
            if not price_el:
                continue
            price_str = price_el.get_text(strip=True)
            cents_el = card.select_one('.andes-money-amount__cents')
            if cents_el:
                price_str += '.' + cents_el.get_text(strip=True)
            price = float(price_str.replace(',', '.'))
            
            # Image
            img_el = card.select_one('img[data-src], img[src*=http]')
            image_url = None
            if img_el:
                image_url = img_el.get('data-src') or img_el.get('src')
            
            # Supplier
            seller_el = card.select_one('span.poly-component__seller, .ui-search-result__seller')
            supplier_name = None
            if seller_el:
                brand_span = seller_el.find('span')
                supplier_name = brand_span.get_text(strip=True) if brand_span else seller_el.get_text(strip=True).split(' por ')[0].strip()
            
            # Review
            review_el = card.select_one('span.poly-component__review-compacted, .ui-search-reviews__rating')
            review_avg = None
            if review_el:
                try:
                    review_avg = float(review_el.get_text(strip=True).replace(',', '.'))
                except ValueError:
                    pass
            
            if not price:
                continue
            
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
                'review_avg': review_avg,
                'supplier_name': supplier_name,
                'is_active': True,
            })
        except Exception as e:
            print(f'    Parse error: {e}')
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
        print(f'    Image error: {e}')
        return None

def insert_product(prod, category):
    sql = """
        INSERT INTO products 
            (platform, platform_id, title, price, currency, url, image_urls, 
             review_avg, review_count, category, is_active, image_hash, supplier_name)
        VALUES 
            (%(platform)s, %(platform_id)s, %(title)s, %(price)s, %(currency)s, 
             %(url)s, %(image_urls)s, %(review_avg)s, %(review_count)s, 
             %(category)s, %(is_active)s, %(image_hash)s, %(supplier_name)s)
        ON CONFLICT (platform, platform_id) DO NOTHING
        RETURNING id
    """
    params = {**prod, 'category': category, 'review_count': None, 'image_hash': prod.get('phash')}
    try:
        result = execute_returning(sql, params)
        return len(result) > 0
    except Exception as e:
        print(f'    DB error: {e}')
        return False

def process(category, search_name, search_url):
    print(f'\n{"="*60}')
    print(f'{category} - {search_name}')
    print(f'{search_url}')
    print(f'{"="*60}')
    
    try:
        html = fetch_ml_html(search_url)
    except Exception as e:
        print(f'  FAIL: {e}')
        return 0, 0
    
    products = extract_products(html)
    print(f'  Found {len(products)} products')
    
    inserted = 0
    skipped = 0
    
    for i, prod in enumerate(products):
        print(f'  [{i+1}/{len(products)}] {prod["title"][:60]}...')
        
        phash = download_phash(prod['image_url'])
        prod['phash'] = phash
        
        if insert_product(prod, category):
            inserted += 1
            print(f'    INSERTED R${prod["price"]:.2f} hash={phash}')
        else:
            skipped += 1
            print(f'    SKIPPED (exists)')
        
        if i < len(products) - 1:
            time.sleep(2)
    
    print(f'  Result: {inserted} inserted, {skipped} skipped')
    return inserted, skipped

if __name__ == '__main__':
    print('Starting ML automotive tool extraction...')
    sys.stdout.flush()
    
    searches = [
        ('ferramentas automotivas', 'https://lista.mercadolivre.com.br/ferramentas-automotivas'),
        ('jogo de soquetes', 'https://lista.mercadolivre.com.br/jogo-de-soquetes'),
        ('kit ferramentas', 'https://lista.mercadolivre.com.br/kit-ferramentas'),
        ('chave combinada', 'https://lista.mercadolivre.com.br/chave-combinada'),
        ('alicate', 'https://lista.mercadolivre.com.br/alicate'),
        ('parafusadeira', 'https://lista.mercadolivre.com.br/parafusadeira'),
        ('furadeira impacto', 'https://lista.mercadolivre.com.br/furadeira-impacto'),
    ]
    
    total_ins = 0
    total_skp = 0
    
    for i, (name, url) in enumerate(searches):
        ins, skp = process('automotive_tool', name, url)
        total_ins += ins
        total_skp += skp
        if i < len(searches) - 1:
            print(f'\n  Waiting 6 seconds before next search...')
            time.sleep(6)
    
    print(f'\n{"="*60}')
    print(f'ML EXTRACTION COMPLETE')
    print(f'Total: {total_ins} inserted, {total_skp} skipped')
    print(f'{"="*60}')
    sys.stdout.flush()
