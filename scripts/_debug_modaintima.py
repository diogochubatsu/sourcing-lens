"""Re-scrape Moda Intima with correct selectors. Decodo works - I need to find the right selector."""
import requests, json, base64, re, os, sys
from bs4 import BeautifulSoup

sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import _load_env

_load_env()
user = os.environ.get('DECODO_USER', 'U0000421443')
pw = os.environ.get('DECODO_PASS', 'PW_1b54b0d65de3da2cc22ab4e5958944783')
auth_b64 = base64.b64encode(f'{user}:{pw}'.encode()).decode()

# MLB108786 - Moda Intima e Lingerie
url = 'https://www.mercadolivre.com.br/mais-vendidos/MLB108786'
resp = requests.post('https://scraper-api.decodo.com/v2/scrape', json={
    'url': url, 'headless': 'html', 'proxy_pool': 'premium', 'locale': 'pt-br',
}, headers={'Authorization': f'Basic {auth_b64}'}, timeout=120)

content = resp.json()['results'][0]['content']
soup = BeautifulSoup(content, 'html.parser')

# Check for MLB links - count them
mlb_links = soup.find_all('a', href=re.compile(r'/p/MLB\d{8,}'))
print(f'MLB product links found: {len(mlb_links)}')

# Try different card selectors
selectors = [
    '[class*="andes-card"]',
    '[class*="poly-card"]',
    '[class*="ui-search-layout"]',
    '[class*="item"]',
    '[class*="product"]',
    '[class*="card"]',
    'li',
    '[class*="grid"]',
]
for sel in selectors:
    els = soup.select(sel)
    has_mlb = sum(1 for e in els if e.find('a', href=re.compile(r'/p/MLB')))
    if has_mlb > 0:
        print(f'  Selector "{sel}": {len(els)} elements, {has_mlb} with MLB links')

# Show sample MLB links and their parent structure
print('\nFirst 5 MLB links:')
for a in mlb_links[:5]:
    href = a.get('href', '')
    title = a.get('title', '') or a.get_text(strip=True)[:80]
    print(f'  {href[:80]}')
    print(f'  Title: {title}')
    # Check price near this link
    parent = a.find_parent(['div', 'li', 'section'])
    if parent:
        price_el = parent.select_one('[class*="money-amount__fraction"]')
        price = price_el.get_text(strip=True) if price_el else 'N/A'
        img = parent.select_one('img')
        img_url = img.get('data-src') or img.get('src', '') if img else 'N/A'
        sales_m = re.search(r'([\d.,]+)\s*(mil|milhao|mi)?\s*vendidos', parent.get_text(), re.IGNORECASE)
        sales = sales_m.group(0) if sales_m else 'N/A'
        print(f'  Price: {price}, Img: {str(img_url)[:60]}, Sales: {sales}')
    print()

# Also check all unique parent classes/ids for structure analysis
print('\nParent classes of first 10 MLB links:')
for a in mlb_links[:10]:
    parent_tags = []
    p = a.parent
    for _ in range(5):
        if p:
            cls = p.get('class', [])
            tag = p.name
            if cls:
                parent_tags.append(f'{tag}.{".".join(cls[:2])}')
            else:
                parent_tags.append(tag)
            p = p.parent
        else:
            break
    print(f'  {" > ".join(reversed(parent_tags))}')
