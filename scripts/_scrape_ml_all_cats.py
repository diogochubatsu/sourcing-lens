"""Test and scrape ML best sellers for fashion and other categories."""
import requests, json, base64, re, os, sys, time
from bs4 import BeautifulSoup

sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import _load_env, query, execute_returning, execute

_load_env()
user = os.environ.get('DECODO_USER', 'U0000421443')
pw = os.environ.get('DECODO_PASS', 'PW_1b54b0d65de3da2cc22ab4e5958944783')
auth_b64 = base64.b64encode(f'{user}:{pw}'.encode()).decode()

def scrape_ml_bestsellers(cat_id, cat_name, category_l1):
    url = f'https://www.mercadolivre.com.br/mais-vendidos/MLB{cat_id}'
    print(f'\n=== {cat_name} (MLB{cat_id}) ===')
    for attempt in range(3):
        resp = requests.post('https://scraper-api.decodo.com/v2/scrape', json={
            'url': url, 'headless': 'html', 'proxy_pool': 'premium', 'locale': 'pt-br',
        }, headers={'Authorization': f'Basic {auth_b64}'}, timeout=120)
        content = resp.json()['results'][0]['content']
        has_mlb = '/p/MLB' in content
        has_sales = 'vendidos' in content
        print(f'  Attempt {attempt+1}: len={len(content)}, MLB={has_mlb}, vendidos={has_sales}')
        if has_mlb:
            break
        time.sleep(3)
    if not has_mlb:
        print('  No product cards found')
        return []
    soup = BeautifulSoup(content, 'html.parser')
    products = []
    for card in soup.select('[class*="andes-card"]'):
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
        if not full_url.startswith('http'):
            full_url = 'https://www.mercadolivre.com.br' + full_url
        img_list = [img_url] if img_url and img_url.startswith('http') else []
        products.append({
            'platform_id': 'MLB' + mlb_id,
            'title': title.strip(),
            'price': price_val,
            'image_urls': img_list,
            'sales_30d': sales_val,
            'platform': 'ml',
            'category_l1': category_l1,
            'category_l2': category_l1,
            'category_l3': category_l1,
            'url': full_url,
        })
    print(f'  Extracted: {len(products)}, with sales: {sum(1 for p in products if p["sales_30d"])}')
    for p in products[:5]:
        pid = p['platform_id'][3:]
        print(f'    MLB{pid:>10s} | R${p["price"]:>8.2f} | vend={str(p["sales_30d"]):>8s} | {p["title"][:50]}')
    return products

def insert_products(products):
    inserted, skipped = 0, 0
    for p in products:
        existing = query("SELECT id FROM products WHERE platform='ml' AND platform_id=%s", (p['platform_id'],))
        if existing:
            if p['sales_30d']:
                execute(
                    "UPDATE products SET sales_30d = %s WHERE platform='ml' AND platform_id=%s AND (sales_30d IS NULL OR sales_30d < %s)",
                    (p['sales_30d'], p['platform_id'], p['sales_30d'])
                )
                skipped += 1
            continue
        try:
            execute_returning(
                """INSERT INTO products (platform, platform_id, title, price, image_urls, sales_30d,
                 category_l1, category_l2, category_l3, url, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, true) RETURNING id""",
                (p['platform'], p['platform_id'], p['title'], p['price'], p['image_urls'],
                 p['sales_30d'], p['category_l1'], p['category_l2'], p['category_l3'], p['url'])
            )
            inserted += 1
        except Exception as e:
            pid = p['platform_id']
            print(f'    Error {pid}: {e}')
    return inserted, skipped

categories = [
    ('108786', 'Moda Intima e Lingerie', 'Moda Intima'),
    ('1457', 'Malas e Bolsas', 'Bolsas'),
    ('430391', 'Moda Praia', 'Praia'),
    ('1451', 'Acessorios de Moda', 'Moda'),
    ('3835', 'Audio', 'Audio'),
    ('3813', 'Acessorios para Celulares', 'Acessorios Mobile'),
    ('417704', 'Smartwatches e Acessorios', 'Wearables'),
]

total_new = 0
total_upd = 0
for cat_id, name, cat_l1 in categories:
    products = scrape_ml_bestsellers(cat_id, name, cat_l1)
    if products:
        new, upd = insert_products(products)
        total_new += new
        total_upd += upd
        print(f'  New: {new}, Updated: {upd}')
    time.sleep(2)

print(f'\n=== SUMMARY ===')
print(f'Total new: {total_new}')
print(f'Total updated: {total_upd}')
