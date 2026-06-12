"""Update ML Ferramentas best sellers sales data."""
import requests, json, base64, re, os, sys, time
from bs4 import BeautifulSoup

sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import _load_env, query, execute

_load_env()
user = os.environ.get('DECODO_USER', 'U0000421443')
pw = os.environ.get('DECODO_PASS', 'PW_1b54b0d65de3da2cc22ab4e5958944783')
auth_b64 = base64.b64encode(f'{user}:{pw}'.encode()).decode()

url = 'https://www.mercadolivre.com.br/mais-vendidos/MLB263532'
print(f'Scraping: {url}')
for attempt in range(3):
    resp = requests.post('https://scraper-api.decodo.com/v2/scrape', json={
        'url': url, 'headless': 'html', 'proxy_pool': 'premium', 'locale': 'pt-br',
        'wait_until': 'network_idle'
    }, headers={'Authorization': f'Basic {auth_b64}'}, timeout=120)
    data = resp.json()
    content = data['results'][0]['content']
    has_mlb = '/p/MLB' in content
    print(f'  Attempt {attempt+1}: len={len(content)}, MLB={has_mlb}')
    if has_mlb:
        break
    time.sleep(3)

soup = BeautifulSoup(content, 'html.parser')
updated = 0

for card in soup.select('[class*="andes-card"]'):
    link = card.select_one('a[href*="/p/MLB"]')
    if not link:
        continue
    href = link.get('href', '')
    m = re.search(r'/p/MLB(\d{8,})', href)
    if not m:
        continue
    mlb_id = m.group(1)
    platform_id = 'MLB' + mlb_id

    card_text = card.get_text()
    sales_m = re.search(r'([\d.,]+)\s*(mil|milhao|mi)?\s*vendidos', card_text, re.IGNORECASE)
    if not sales_m:
        continue

    num = float(sales_m.group(1).replace('.', '').replace(',', '.'))
    suffix = sales_m.group(2)
    if suffix:
        s = suffix.lower()
        if 'mil' in s:
            num *= 1000
        elif 'milh' in s:
            num *= 1000000
    sales_val = int(num)

    affected = execute(
        "UPDATE products SET sales_30d = %s WHERE platform = 'ml' AND platform_id = %s AND (sales_30d IS NULL OR sales_30d < %s)",
        (sales_val, platform_id, sales_val)
    )
    if affected > 0:
        print(f'  Updated {platform_id}: sales={sales_val}')
        updated += 1

print(f'\nTotal updated: {updated}')
