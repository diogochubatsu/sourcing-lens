"""Scrape new subcategories + try PNG for failed cats."""
import requests, json, base64, re, os, sys, time
from bs4 import BeautifulSoup
sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import _load_env, query, execute_returning, execute

_load_env()
user = os.environ.get('DECODO_USER', 'U0000421443')
pw = os.environ.get('DECODO_PASS', 'PW_1b54b0d65de3da2cc22ab4e5958944783')
auth_b64 = base64.b64encode(f'{user}:{pw}'.encode()).decode()

def scrape_cat(cat_id, cat_name, category_l1, headless='html'):
    url = 'https://www.mercadolivre.com.br/mais-vendidos/MLB' + cat_id
    print(f'\n=== {cat_name} (MLB{cat_id}) [{headless}] ===')
    for attempt in range(5):
        resp = requests.post('https://scraper-api.decodo.com/v2/scrape', json={
            'url': url, 'headless': headless, 'proxy_pool': 'premium', 'locale': 'pt-br',
        }, headers={'Authorization': f'Basic {auth_b64}'}, timeout=120)
        data = resp.json()
        if headless == 'png':
            # PNG mode returns base64 image, not HTML
            print(f'  Attempt {attempt+1}: PNG returned (can inspect via vision)')
            return []  # Skip vision parsing for now
        c = data['results'][0]['content']
        has_p = '/p/MLB' in c
        print(f'  Attempt {attempt+1}: len={len(c)}, MLB={has_p}')
        if has_p:
            break
        time.sleep(2)
    if not has_p:
        print('  Failed')
        return []
    
    soup = BeautifulSoup(c, 'html.parser')
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
        ps = str(price_el.get_text(strip=True)) if price_el else '0'
        try:
            pv = float(ps.replace('.', '').replace(',', '.'))
        except:
            pv = 0.0
        img = card.select_one('img')
        iu = ''
        if img:
            iu = str(img.get('data-src') or img.get('src', ''))
            if iu.startswith('//'):
                iu = 'https:' + iu
        ct = card.get_text()
        sm = re.search(r'([\d.,]+)\s*(mil|milhao|mi)?\s*vendidos', ct, re.IGNORECASE)
        sv = None
        if sm:
            n = float(sm.group(1).replace('.', '').replace(',', '.'))
            suffix = sm.group(2)
            if suffix:
                s = suffix.lower()
                if 'mil' in s: n *= 1000
                elif 'milh' in s: n *= 1000000
            sv = int(n)
        fu = href
        if not fu.startswith('http'):
            fu = 'https://www.mercadolivre.com.br' + fu
        il = [iu] if iu and iu.startswith('http') else []
        products.append({
            'pid': 'MLB' + mlb_id, 'title': title.strip(), 'price': pv,
            'imgs': il, 'sales': sv, 'plat': 'ml',
            'cat': category_l1, 'url': fu,
        })
    print(f'  Got {len(products)}, with sales={sum(1 for p in products if p["sales"])}')
    for p in products[:5]:
        print(f'    {p["pid"][3:]:>10s} | R${p["price"]:>8.2f} | vend={str(p["sales"]):>8s} | {p["title"][:50]}')
    return products

# New subcategories found
cats = [
    ('3127', 'Mochilas', 'Mochilas'),
    ('7022', 'Bolsas', 'Bolsas'),
    ('432017', 'Bagagem', 'Bolsas'),
    ('28108', 'Carteiras', 'Moda'),
]

all_new = 0
for cat_id, name, cat_l1 in cats:
    prods = scrape_cat(cat_id, name, cat_l1)
    new = 0
    for p in prods:
        existing = query("SELECT id FROM products WHERE platform='ml' AND platform_id=%s", (p['pid'],))
        if existing:
            continue
        try:
            execute_returning(
                "INSERT INTO products (platform,platform_id,title,price,image_urls,sales_30d,category_l1,category_l2,category_l3,url,is_active) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,true) RETURNING id",
                (p['plat'], p['pid'], p['title'], p['price'], p['imgs'], p['sales'], p['cat'], p['cat'], p['cat'], p['url'])
            )
            new += 1
        except Exception as e:
            pass
    print(f'  New: {new}')
    all_new += new
    time.sleep(2)

# Now try PNG mode for Moda Intima
print('\n=== Trying PNG mode for Moda Intima ===')
url = 'https://www.mercadolivre.com.br/mais-vendidos/MLB108786'
resp = requests.post('https://scraper-api.decodo.com/v2/scrape', json={
    'url': url, 'headless': 'png', 'proxy_pool': 'premium', 'locale': 'pt-br',
}, headers={'Authorization': f'Basic {auth_b64}'}, timeout=120)
data = resp.json()
if data.get('results'):
    img_b64 = data['results'][0].get('content', '')[:100]
    print(f'PNG result: {len(img_b64)} chars of base64')

print(f'\nTotal new products: {all_new}')
