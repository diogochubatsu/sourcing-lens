"""Test ML best sellers pages for categories and scrape sales data."""
import requests, json, base64, re, os, sys, time
from bs4 import BeautifulSoup

sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import _load_env, query, execute

_load_env()
user = os.environ.get('DECODO_USER', 'U0000421443')
pw = os.environ.get('DECODO_PASS', 'PW_1b54b0d65de3da2cc22ab4e5958944783')
auth_b64 = base64.b64encode(f'{user}:{pw}'.encode()).decode()

# Categories to test
cats_to_test = {
    'Audio': '3835',
    'Acessorios_Celular': '3813',
    'Smartwatches': '417704',
    'Calçados_Roupas_Bolsas': '1430',
    'Iluminacao': '438282',  # Under Eletrodomésticos, Pequenos Eletrodomésticos?
}

# First, check Calçados_Roupas_Bolsas more carefully
print('=== Testing Calçados, Roupas e Bolsas (MLB1430) ===')
url = 'https://www.mercadolivre.com.br/mais-vendidos/MLB1430'
resp = requests.post('https://scraper-api.decodo.com/v2/scrape', json={
    'url': url, 'headless': 'html', 'proxy_pool': 'premium', 'locale': 'pt-br',
    'wait_until': 'network_idle'
}, headers={'Authorization': f'Basic {auth_b64}'}, timeout=120)
content = resp.json()['results'][0]['content']
print(f'  Len: {len(content)}')

# Look for subcategory links
soup = BeautifulSoup(content, 'html.parser')
# Find ALL links
all_links = soup.find_all('a', href=True)
subcats = []
for a in all_links:
    href = a.get('href', '')
    text = a.get_text(strip=True)
    if isinstance(href, str) and isinstance(text, str) and len(text) > 3:
        if '/mais-vendidos/MLB' in href:
            m = re.search(r'MLB(\d+)', href)
            if m:
                subcats.append((m.group(1), text))
        elif '/c/' in href and 'calcado' in href.lower() or 'roupa' in href.lower() or 'bolsa' in href.lower():
            if text:
                subcats.append(('CAT:' + href, text))

# Also search for fashion-related text patterns
fashion_links = []
for a in all_links:
    href = a.get('href', '')
    text = a.get_text(strip=True)
    if isinstance(href, str) and isinstance(text, str) and len(text) > 2:
        t = text.lower()
        if any(w in t for w in ['calcado', 'roupa', 'bolsa', 'moda', 'intima', 'mochila', 'meia', 'acessorio']):
            fashion_links.append((href[:100], text))

print(f'  Subcategories found: {len(subcats)}')
for sid, sname in subcats[:20]:
    print(f'    MLB{sid:>8s} — {sname}')

print(f'\n  Fashion-related links: {len(fashion_links)}')
for href, text in fashion_links[:15]:
    print(f'    [{text[:40]}] -> {href[:80]}')

# Check for product data on the page
has_mlb = '/p/MLB' in content
has_sales = 'vendidos' in content
print(f'\n  Has products: {has_mlb}, Has sales: {has_sales}')

if has_mlb:
    # Extract products
    cards = soup.select('[class*="andes-card"]')
    products_found = 0
    for card in cards:
        link = card.select_one('a[href*="/p/MLB"]')
        if link:
            products_found += 1
            if products_found <= 3:
                href = link.get('href', '')
                title = link.get('title', '') or link.get_text(strip=True)
                card_text = card.get_text()
                sales_m = re.search(r'([\d.,]+)\s*(mil|milhao|mi)?\s*vendidos', card_text, re.IGNORECASE)
                sales = sales_m.group(0) if sales_m else 'No sales data'
                print(f'  Produto: {str(title)[:50]} | Vendas: {sales}')
    print(f'  Total products: {products_found}')
