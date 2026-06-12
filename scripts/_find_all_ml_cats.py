"""Find all ML best sellers category IDs for existing categories + new fashion categories."""
import requests, json, base64, re, os, sys
from bs4 import BeautifulSoup

sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import _load_env

_load_env()
user = os.environ.get('DECODO_USER', 'U0000421443')
pw = os.environ.get('DECODO_PASS', 'PW_1b54b0d65de3da2cc22ab4e5958944783')
auth_b64 = base64.b64encode(f'{user}:{pw}'.encode()).decode()

# Scrape the ML best sellers hub to find all category IDs
url = 'https://www.mercadolivre.com.br/mais-vendidos'
resp = requests.post('https://scraper-api.decodo.com/v2/scrape', json={
    'url': url, 'headless': 'html', 'proxy_pool': 'premium', 'locale': 'pt-br',
    'wait_until': 'network_idle'
}, headers={'Authorization': f'Basic {auth_b64}'}, timeout=120)
content = resp.json()['results'][0]['content']

soup = BeautifulSoup(content, 'html.parser')

# Find all best sellers category links
bs_links = soup.find_all('a', href=re.compile(r'/mais-vendidos/MLB'))
categories = {}
for a in bs_links:
    href = a.get('href', '')
    text = a.get_text(strip=True)
    if not isinstance(href, str) or not isinstance(text, str):
        continue
    m = re.search(r'MLB(\d+)', href)
    if m:
        cat_id = m.group(1)
        # Clean name
        name = text.replace('Ver mais', '').strip()
        categories[name] = cat_id

print('=== ML BEST SELLERS CATEGORIES FOUND ===')
for name, cat_id in sorted(categories.items()):
    print(f'  MLB{cat_id:>8s} — {name}')

# Check which categories match our existing ones
print('\n=== MATCHING EXISTING DB CATEGORIES ===')
existing = ['Acessórios Mobile', 'Audio', 'Casa', 'Esportes', 'Ferramentas', 
            'Fotografia', 'Iluminação', 'Praia', 'Wearables', 'Moda Íntima', 
            'Mochilas', 'Bolsas', 'Meias']
for name in existing:
    found = False
    for cat_name, cat_id in categories.items():
        cat_lower = cat_name.lower()
        name_lower = name.lower()
        if any(word in cat_lower for word in name_lower.split()):
            print(f'  {name:20s} → MLB{cat_id} ({cat_name})')
            found = True
            break
    if not found:
        print(f'  {name:20s} → NOT FOUND in ML hub')
