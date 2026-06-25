#!/usr/bin/env python3
"""scrape_ml_bestsellers.py — Scrape all ML best sellers categories via Decodo."""
import json, re, urllib.request, ssl, time, os

AUTH_FILE = os.path.join(os.path.dirname(__file__), '..', 'config', 'decodo_scraping.key')
AUTH = open(AUTH_FILE).read().strip()
URL = "https://scraper-api.decodo.com/v2/scrape"

ML_CATS = {
    "Audio": "MLB3835", "Tech": "MLB1000", "Sports": "MLB1276",
    "Health": "MLB1246", "Home": "MLB1574", "Pet": "MLB1071",
    "Tools": "MLB263532", "Photography": "MLB1039", "Acessórios Mobile": "MLB3813",
    "Wearables": "MLB417704", "Bolsas": "MLB1457", "Moda": "MLB1430",
    "Bebê": "MLB1384", "Brinquedos": "MLB1132", "Iluminação": "MLB430378",
}

def scrape(url):
    payload = json.dumps({"url": url, "headless": "html", "proxy_pool": "premium", "locale": "pt-br"}).encode()
    req = urllib.request.Request(URL, data=payload, method='POST')
    req.add_header('Authorization', f'Basic {AUTH}')
    req.add_header('Content-Type', 'application/json')
    ctx = ssl._create_unverified_context()
    with urllib.request.urlopen(req, timeout=90, context=ctx) as r:
        return json.loads(r.read())['results'][0]['content']

def extract(html):
    products = {}
    for mid in set(re.findall(r'MLB[-]?(\d{8,})', html)):
        fid = f'MLB{mid}'
        pos = html.find(fid)
        if pos < 0: continue
        block = html[max(0,pos-500):pos+3000]
        m = re.search(r'([\d,.]+)\s*(mil|milhão|mi|k|M)?\s*(?:produtos?\s+)?vendidos', block, re.IGNORECASE)
        if m:
            num = float(m.group(1).replace('.','').replace(',','.'))
            mult = m.group(2)
            if mult:
                if mult.lower() in ('mil','k'): num *= 1000
                elif mult.lower() in ('milhão','mi','m'): num *= 1000000
            if int(num) > 0 and fid not in products:
                products[fid] = int(num)
    return products

all_products = {}
for name, mid in ML_CATS.items():
    print(f'{name} ({mid})...', end=' ', flush=True)
    try:
        html = scrape(f'https://www.mercadolivre.com.br/mais-vendidos/{mid}')
        p = extract(html)
        all_products.update(p)
        print(f'{len(p)} products')
    except Exception as e:
        print(f'FAILED: {e}')
    time.sleep(3)

out = os.path.join(os.path.dirname(__file__), '..', 'data', 'bestsellers', 'ml_all_decodo.json')
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, 'w') as f:
    json.dump(all_products, f, indent=2)
print(f'\nTotal: {len(all_products)} unique ML products → {out}')
