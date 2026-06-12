"""Extract products from ML Ferramentas category page using Decodo."""
import requests, json, base64, re, os, sys
from bs4 import BeautifulSoup

sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import _load_env, query, execute_returning

_load_env()
user = os.environ.get('DECODO_USER', 'U0000421443')
pw = os.environ.get('DECODO_PASS', 'PW_1b54b0d65de3da2cc22ab4e5958944783')
auth_b64 = base64.b64encode(f'{user}:{pw}'.encode()).decode()

url = 'https://www.mercadolivre.com.br/c/ferramentas'
print(f'Scraping: {url}')
resp = requests.post('https://scraper-api.decodo.com/v2/scrape', json={
    'url': url, 'headless': 'html', 'proxy_pool': 'premium', 'locale': 'pt-br',
    'wait_until': 'network_idle'
}, headers={'Authorization': f'Basic {auth_b64}'}, timeout=120)

if resp.status_code != 200:
    print(f'Error: {resp.status_code} - {resp.text[:200]}')
    sys.exit(1)

data = resp.json()
if not data.get('results'):
    print(f'No results: {json.dumps(data)[:300]}')
    sys.exit(1)

content = data['results'][0]['content']
print(f'Content length: {len(content)}')

soup = BeautifulSoup(content, 'html.parser')
products = []

for card in soup.select('[class*="andes-card"]'):
    link = card.select_one('a[href*="/p/MLB"]')
    if not link:
        continue
    href = link.get('href', '')
    m = re.search(r'/p/MLB(\d{8,})', href)
    if not m:
        continue
    mlb_id = m.group(1)

    # Title
    title = link.get('title', '') or link.get_text(strip=True)
    title = title.strip()[:200]

    # Price
    price_el = card.select_one('[class*="money-amount__fraction"]')
    price_str = price_el.get_text(strip=True) if price_el else '0'
    try:
        price_val = float(price_str.replace('.', '').replace(',', '.'))
    except:
        price_val = 0.0

    # Image
    img = card.select_one('img')
    img_url = ''
    if img:
        img_url = img.get('data-src') or img.get('src', '')
        if isinstance(img_url, str) and img_url.startswith('//'):
            img_url = 'https:' + img_url
        if not isinstance(img_url, str):
            img_url = ''

    # Sales
    sales_text = ''
    for el in card.find_all(['span', 'p', 'div']):
        txt = el.get_text(strip=True)
        if 'vendido' in txt.lower():
            sales_text = txt
            break

    sales_val = None
    sales_m = re.search(r'([\d.,]+)\s*(mil|milhao|mi)?\s*vendidos', sales_text, re.IGNORECASE)
    if sales_m:
        num = float(sales_m.group(1).replace('.', '').replace(',', '.'))
        suffix = sales_m.group(2)
        if suffix and 'mil' in suffix.lower():
            num *= 1000
        elif suffix and 'milh' in suffix.lower():
            num *= 1000000
        sales_val = int(num)

    full_url = href
    if isinstance(href, str) and not href.startswith('http'):
        full_url = 'https://www.mercadolivre.com.br' + href

    products.append({
        'platform_id': f'MLB{mlb_id}',
        'title': title,
        'price': price_val,
        'image_urls': [img_url] if img_url and isinstance(img_url, str) else [],
        'sales_30d': sales_val,
        'platform': 'ml',
        'category_l1': 'Ferramentas',
        'category_l2': 'Ferramentas',
        'category_l3': 'Ferramentas',
        'url': full_url,
    })

print(f'\nTotal products extracted: {len(products)}')
with_sales = sum(1 for p in products if p['sales_30d'])
with_img = sum(1 for p in products if p['image_urls'] and len(p['image_urls']) > 0 and 'http' in str(p['image_urls'][0]))
print(f'With sales data: {with_sales}')
print(f'With image: {with_img}')

for p in products[:10]:
    print(f'  {p["platform_id"]:>15s} | R${p["price"]:>8.2f} | vend={str(p["sales_30d"]):>8s} | {p["title"][:50]}')

# Insert into DB (skip duplicates)
inserted = 0
skipped = 0
for p in products:
    if not p['platform_id'] or not p['title']:
        continue
    existing = query(
        "SELECT id FROM products WHERE platform=%s AND platform_id=%s",
        (p['platform'], p['platform_id'])
    )
    if existing:
        skipped += 1
        continue
    try:
        execute_returning(
            """INSERT INTO products 
            (platform, platform_id, title, price, image_urls, sales_30d, 
             category_l1, category_l2, category_l3, url, is_active)
            VALUES (%(platform)s, %(platform_id)s, %(title)s, %(price)s, %(image_urls)s, 
                    %(sales_30d)s, %(category_l1)s, %(category_l2)s, %(category_l3)s, 
                    %(url)s, true)
            RETURNING id""",
            p
        )
        inserted += 1
    except Exception as e:
        print(f'  Error inserting {p["platform_id"]}: {e}')

print(f'\nInserted: {inserted}, Skipped (existing): {skipped}')
