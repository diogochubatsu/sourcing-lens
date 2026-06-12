"""Scrape ML fashion category page for products."""
import requests, base64, json, re, os, sys, time
from bs4 import BeautifulSoup
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import _load_env, query, execute_returning, execute

_load_env()
user = 'U0000421443'
pw = 'PW_1b54b0d65de3da2cc22ab4e5958944783'
auth = base64.b64encode(f'{user}:{pw}'.encode()).decode()

url = 'https://www.mercadolivre.com.br/c/calcados-roupas-e-bolsas'
print(f'Scraping: {url}')
resp = requests.post('https://scraper-api.decodo.com/v2/scrape', json={
    'url': url, 'headless': 'html', 'proxy_pool': 'premium', 'locale': 'pt-br',
    'wait_until': 'network_idle'
}, headers={'Authorization': f'Basic {auth}'}, timeout=120)
content = resp.json()['results'][0]['content']
soup = BeautifulSoup(content, 'html.parser')

def classify_fashion(title):
    t = title.lower()
    if any(w in t for w in ['meia', 'meias']):
        return 'Meias'
    if any(w in t for w in ['cueca', 'calcinha', 'suti', 'boxer', 'body', 'lingerie', 'moda intima', 'soutien']):
        return 'Moda Intima'
    if any(w in t for w in ['mochila']):
        return 'Mochilas'
    if any(w in t for w in ['bolsa', 'mala']):
        return 'Bolsas'
    if any(w in t for w in ['relogio', 'pulseira']):
        return 'Moda'
    if any(w in t for w in ['calcado', 'tenis', 'sapato', 'chinelo', 'sandalia', 'havaianas']):
        return 'Moda'
    if any(w in t for w in ['camiseta', 'camisa', 'blusa', 'calc', 'vestido', 'short', 'bermuda', 'jaqueta', 'casaco']):
        return 'Moda'
    return 'Moda'

# Find product cards - try multiple selectors
products = []
for selector in ['[class*="andes-card"]', '[class*="poly-card"]', '[class*="poly-component"]']:
    cards = soup.select(selector)
    for card in cards:
        link = card.select_one('a[href*="/p/MLB"]')
        if not link:
            continue
        href = str(link.get('href', ''))
        m = re.search(r'/p/MLB(\d{8,})', href)
        if not m:
            continue
        mlb_id = m.group(1)
        
        title = str(link.get('title', '') or link.get_text(strip=True))[:200]
        price_el = card.select_one('[class*="money-amount__fraction"]')
        price_str = str(price_el.get_text(strip=True)) if price_el else '0'
        try:
            price_val = float(price_str.replace('.', '').replace(',', '.'))
        except:
            price_val = 0.0
        img = card.select_one('img')
        img_url = ''
        if img:
            img_url = str(img.get('data-src') or img.get('src', ''))
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
        
        full_url = href
        if not full_url.startswith('http'):
            full_url = 'https://www.mercadolivre.com.br' + full_url
        
        img_list = [img_url] if img_url and img_url.startswith('http') else []
        cat = classify_fashion(title)
        
        products.append({
            'pid': 'MLB' + mlb_id,
            'title': title.strip(),
            'price': price_val,
            'imgs': img_list,
            'sales': None,
            'plat': 'ml',
            'cat': cat,
            'url': full_url,
        })

print(f'Total products: {len(products)}')
cats_count = {}
for p in products:
    cats_count[p['cat']] = cats_count.get(p['cat'], 0) + 1
for c, n in sorted(cats_count.items()):
    print(f'  {c}: {n}')

# Insert
inserted = 0
skipped = 0
for p in products:
    existing = query("SELECT id FROM products WHERE platform='ml' AND platform_id=%s", (p['pid'],))
    if existing:
        skipped += 1
        continue
    try:
        execute_returning(
            "INSERT INTO products (platform,platform_id,title,price,image_urls,sales_30d,category_l1,category_l2,category_l3,url,is_active) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,true) RETURNING id",
            (p['plat'], p['pid'], p['title'], p['price'], p['imgs'], p['sales'], p['cat'], p['cat'], p['cat'], p['url'])
        )
        inserted += 1
    except Exception as e:
        pass

print(f'Inserted: {inserted}, Skipped: {skipped}')
