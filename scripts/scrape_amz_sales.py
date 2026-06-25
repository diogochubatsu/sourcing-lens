#!/usr/bin/env python3
"""Scrape Amazon BR best sellers for sales data via Decodo."""
import json, re, urllib.request, ssl, time, os

auth = open(os.path.join(os.path.dirname(__file__), '..', 'config', 'decodo_scraping.key')).read().strip()
api_url = "https://scraper-api.decodo.com/v2/scrape"

CATS = {
    "Audio": "electronics", "Moda": "fashion", "Home": "home",
    "Pet": "pet-products", "Kitchen": "kitchen", "Sports": "sports",
    "Health": "hpc", "Beauty": "beauty", "Toys": "toys",
    "Baby": "baby-products", "Tools": "hi",
}

def fetch(url):
    payload = json.dumps({"url": url, "headless": "html", "proxy_pool": "premium", "locale": "pt-br"}).encode()
    req = urllib.request.Request(api_url, data=payload, method='POST')
    req.add_header('Authorization', f'Basic {auth}')
    req.add_header('Content-Type', 'application/json')
    ctx = ssl._create_unverified_context()
    with urllib.request.urlopen(req, timeout=90, context=ctx) as r:
        return json.loads(r.read())['results'][0]['content']

def extract_sales(html):
    html = html.replace('&nbsp;', ' ')
    m = re.search(r'Mais de ([\d,.]+)\s*(mil|milhão|mi)?\s*compras?\s*no\s*mês\s*passado', html, re.IGNORECASE)
    if m:
        num_str = m.group(1).replace('.', '').replace(',', '.')
        mult = m.group(2) if m.lastindex and m.lastindex >= 2 else None
        num = float(num_str)
        if mult:
            if mult.lower() in ('mil', 'k'): num *= 1000
            elif mult.lower() in ('milhão', 'mi'): num *= 1000000
        return int(num)
    return None

all_products = {}
for name, slug in CATS.items():
    print(f"\n{name} ({slug})...", flush=True)
    try:
        bs_html = fetch(f"https://www.amazon.com.br/gp/bestsellers/{slug}")
        asins = list(dict.fromkeys(re.findall(r'data-asin="([A-Z0-9]{10})"', bs_html)))
        print(f"  {len(asins)} ASINs", flush=True)
        
        cat_found = 0
        for i, asin in enumerate(asins[:30]):
            try:
                prod_html = fetch(f"https://www.amazon.com.br/dp/{asin}")
                sales = extract_sales(prod_html)
                if sales:
                    all_products[asin] = sales
                    cat_found += 1
            except:
                pass
            time.sleep(2)
        
        print(f"  {cat_found}/{min(len(asins),30)} with sales")
    except Exception as e:
        print(f"  FAILED: {e}")
    time.sleep(3)

out_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'bestsellers')
os.makedirs(out_dir, exist_ok=True)
out = os.path.join(out_dir, 'amz_br_sales.json')
with open(out, 'w') as f:
    json.dump(all_products, f, indent=2)
print(f"\nTotal: {len(all_products)} Amazon BR products → {out}")
