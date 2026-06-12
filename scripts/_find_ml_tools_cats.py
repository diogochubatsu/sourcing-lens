"""Find ML best sellers category IDs for Ferramentas."""
import requests, json, base64, re, os, sys
from bs4 import BeautifulSoup

sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import _load_env

_load_env()
user = os.environ.get('DECODO_USER', 'U0000421443')
pw = os.environ.get('DECODO_PASS', 'PW_1b54b0d65de3da2cc22ab4e5958944783')
auth_b64 = base64.b64encode(f'{user}:{pw}'.encode()).decode()

# 1. First try the ML best sellers hub
url = 'https://www.mercadolivre.com.br/mais-vendidos'
print(f'1. Best sellers hub: {url}')
resp = requests.post('https://scraper-api.decodo.com/v2/scrape', json={
    'url': url, 'headless': 'html', 'proxy_pool': 'premium', 'locale': 'pt-br',
    'wait_until': 'network_idle'
}, headers={'Authorization': f'Basic {auth_b64}'}, timeout=120)
data = resp.json()
content = data['results'][0]['content']
print(f'   Len: {len(content)}, MLB: {"/p/MLB" in content}')

# Find best sellers category links
soup = BeautifulSoup(content, 'html.parser')
bs_links = soup.find_all('a', href=re.compile(r'/mais-vendidos/MLB'))
print(f'\nBest sellers category links: {len(bs_links)}')
found_ferramentas = False
for a in bs_links:
    href = a.get('href', '')
    text = a.get_text(strip=True)[:80]
    if not text or not href:
        continue
    if 'ferrament' in text.lower() or 'ferrament' in href.lower():
        print(f'  >>> [{text}] -> {href}')
        found_ferramentas = True
    elif len(bs_links) < 30:
        print(f'  [{text}] -> {href}')

if not found_ferramentas:
    print('\nFerramentas not found in best sellers hub. Searching entire page...')
    all_links = soup.find_all('a')
    for a in all_links:
        text = a.get_text(strip=True)
        href = a.get('href', '')
        if 'ferrament' in text.lower() or 'ferrament' in href.lower():
            print(f'  [{text[:60]}] -> {href[:150]}')

# 2. Try different MLB category IDs for tools
print('\n\n2. Trying known MLB category IDs for Ferramentas...')
# Common tool category IDs
tool_cats = ['1132', '5722', '1512', '4122', '1041388']
for cat_id in tool_cats:
    url = f'https://www.mercadolivre.com.br/mais-vendidos/MLB{cat_id}'
    try:
        resp = requests.post('https://scraper-api.decodo.com/v2/scrape', json={
            'url': url, 'headless': 'html', 'proxy_pool': 'premium', 'locale': 'pt-br',
        }, headers={'Authorization': f'Basic {auth_b64}'}, timeout=60)
        data = resp.json()
        content = data['results'][0]['content']
        has_mlb = '/p/MLB' in content
        has_sales = 'vendidos' in content
        print(f'  MLB{cat_id}: len={len(content)}, has_mlb={has_mlb}, has_sales={has_sales}')
    except Exception as e:
        print(f'  MLB{cat_id}: ERROR {e}')
