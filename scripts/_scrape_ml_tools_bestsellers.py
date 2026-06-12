"""Scrape ML Ferramentas / MLB263532 best sellers page."""
import requests, json, base64, re, os, sys
from bs4 import BeautifulSoup

sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import _load_env, query, execute_returning

_load_env()
user = os.environ.get('DECODO_USER', 'U0000421443')
pw = os.environ.get('DECODO_PASS', 'PW_1b54b0d65de3da2cc22ab4e5958944783')
auth_b64 = base64.b64encode(f'{user}:{pw}'.encode()).decode()

# ML Ferramentas best sellers
url = 'https://www.mercadolivre.com.br/mais-vendidos/MLB263532'
print(f'Scraping: {url}')
for attempt in range(5):
    resp = requests.post('https://scraper-api.decodo.com/v2/scrape', json={
        'url': url, 'headless': 'html', 'proxy_pool': 'premium', 'locale': 'pt-br',
        'wait_until': 'network_idle'
    }, headers={'Authorization': f'Basic {auth_b64}'}, timeout=120)
    
    data = resp.json()
    content = data['results'][0]['content']
    print(f'  Attempt {attempt+1}: len={len(content)}, MLB={"/p/MLB" in content}, vendidos={"vendidos" in content}')
    
    if '/p/MLB' in content:
        break
    import time
    time.sleep(3)

soup = BeautifulSoup(content, 'html.parser')
products = []

for card in soup.select('[class*="andes-card"]') or soup.select('li[class*="ui-search-layout"]'):
    link = card.select_one('a[href*="/p/MLB"]')
    if not link:
        # Try parent
        link = card.find('a', href=re.compile(r'/p/MLB'))
    if not link:
        continue
    
    href = link.get('href', '')
    if isinstance(href, str):
        m = re.search(r'/p/MLB(\d{8,})', href)
        if not m:
            continue
        mlb_id = m.group(1)
    else:
        continue

    # Title
    title = link.get('title', '') or link.get_text(strip=True)
    if isinstance(title, str):
        title = title.strip()[:200]
    else:
        continue

    # Price
    price_el = card.select_one('[class*="money-amount__fraction"]')
    price_str = price_el.get_text(strip=True) if price_el else '0'
    if isinstance(price_str, str):
        try:
            price_val = float(price_str.replace('.', '').replace(',', '.'))
        except:
            price_val = 0.0
    else:
        price_val = 0.0

    # Image
    img = card.select_one('img')
    img_url = ''
    if img:
        img_url = img.get('data-src') or img.get('src', '')

    # Sales
    card_text = card.get_text()
    sales_m = re.search(r'([\d.,]+)\s*(mil|milhao|mi)?\s*vendidos', card_text, re.IGNORECASE)
    sales_val = None
    if sales_m:
        num = float(sales_m.group(1).replace('.', '').replace(',', '.'))
        suffix = sales_m.group(2)
        if suffix:
            s = suffix.lower()
            if 'mil' in s:
                num *= 1000
            elif 'milh' in s:
                num *= 1000000
        sales_val = int(num)

    full_url = href
    if isinstance(full_url, str) and not full_url.startswith('http'):
        full_url = 'https://www.mercadolivre.com.br' + full_url

    # Clean image URL
    if isinstance(img_url, str) and img_url.startswith('//'):
        img_url = 'https:' + img_url
    img_list = []
    if isinstance(img_url, str) and img_url.startswith('http'):
        img_list = [img_url]

    products.append({
        'platform_id': f'MLB{mlb_id}',
        'title': title,
        'price': price_val,
        'image_urls': img_list,
        'sales_30d': sales_val,
        'platform': 'ml',
        'category_l1': 'Ferramentas',
        'category_l2': 'Ferramentas',
        'category_l3': 'Ferramentas',
        'url': full_url,
    })

print(f'\nTotal: {len(products)}, with sales: {sum(1 for p in products if p["sales_30d"])}')
for p in products[:15]:
    print(f'  {p["platform_id"]:>15s} | R${p["price"]:>8.2f} | vend={str(p["sales_30d"]):>8s} | {p["title"][:50]}')

# Insert
inserted = 0
skipped = 0
for p in products:
    existing = query("SELECT id FROM products WHERE platform=%s AND platform_id=%s", (p['platform'], p['platform_id']))
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
        print(f'  Error {p["platform_id"]}: {e}')

print(f'\nInserted: {inserted}, Skipped: {skipped}')
