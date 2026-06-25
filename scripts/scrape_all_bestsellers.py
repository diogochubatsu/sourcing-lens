#!/usr/bin/env python3
"""
scrape_all_bestsellers.py — Scrape best sellers for ALL categories across all marketplaces.
Maps our category_l1 to best sellers URLs for Amazon BR, Amazon US, and ML.
Saves results to data/bestsellers/ for later import.
"""
import json, re, urllib.request, ssl, time, os, sys

AUTH = open(os.path.join(os.path.dirname(__file__), '..', 'config', 'decodo_scraping.key')).read().strip()
API_URL = "https://scraper-api.decodo.com/v2/scrape"
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'bestsellers')
os.makedirs(OUT_DIR, exist_ok=True)

def fetch(url, timeout=90):
    payload = json.dumps({"url": url, "headless": "html", "proxy_pool": "premium", "locale": "pt-br"}).encode()
    req = urllib.request.Request(API_URL, data=payload, method='POST')
    req.add_header('Authorization', f'Basic {AUTH}')
    req.add_header('Content-Type', 'application/json')
    ctx = ssl._create_unverified_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return json.loads(r.read())['results'][0]['content']

def extract_amz_asins(html):
    return list(dict.fromkeys(re.findall(r'data-asin="([A-Z0-9]{10})"', html)))

def extract_amz_sales(html):
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

def extract_ml_sales(html):
    """Extract 'X vendidos' from ML best sellers."""
    products = {}
    # Find product links with MLB IDs
    mlb_ids = re.findall(r'MLB(\d{8,})', html)
    # Find sales mentions near MLB IDs
    sales_pattern = re.findall(r'(\d[\d,.]*)\s*vendidos', html, re.IGNORECASE)
    # Alternative: extract from structured data
    cards = re.findall(r'"permalink":"[^"]*?(MLB\d+)"[^}]*?"sold_quantity":(\d+)', html)
    for mlb_id, sales in cards:
        products[mlb_id] = int(sales)
    return products

# === CATEGORY MAPPINGS ===

# Amazon BR: category_l1 → best sellers slug
AMAZON_BR = {
    "Audio": "electronics",
    "Moda": "fashion",
    "Cozinha": "kitchen",
    "Pet Shop": "pet-products",
    "Health": "hpc",
    "Bebê": "baby-products",
    "Brinquedos": "toys",
    "Escritório": "office",
    "Jardim": "lawn-and-garden",
    "Automotivo": "automotive",
    "Musical": "musical-instruments",
    "Ferramentas": "hi",
    "Beleza": "beauty",
    "Esportes": "sports",
    "Casa": "home",
}

# Amazon US: category_l1 → best sellers slug
AMAZON_US = {
    "Audio": "electronics",
    "Moda": "fashion",
    "Cozinha": "kitchen",
    "Pet Shop": "pet-products",
    "Health": "hpc",
    "Bebê": "baby",
    "Brinquedos": "toys",
    "Escritório": "office",
    "Jardim": "lawn-and-garden",
    "Automotivo": "automotive",
    "Musical": "musical-instruments",
    "Ferramentas": "tools-and-home-improvement",
    "Beleza": "beauty",
    "Esportes": "sporting-goods",
    "Casa": "home-and-kitchen",
}

# ML: category_l1 → MLB ID (best sellers)
ML_CATS = {
    "Audio": "MLB3835",
    "Moda": "MLB1430",
    "Cozinha": "MLB1618",
    "Pet Shop": "MLB1071",
    "Health": "MLB264586",
    "Moda Intima": "MLB108786",
    "Bebê": "MLB1384",
    "Brinquedos": "MLB1132",
    "Praia": "MLB430391",
    "Escritório": "MLB1368",
    "Jardim": "MLB1621",
    "Automotivo": "MLB1743",
    "Musical": "MLB1182",
    "Ferramentas": "MLB263532",
    "Beleza": "MLB1246",
    "Esportes": "MLB1276",
    "Casa": "MLB1574",
    "Fotografia": "MLB1039",
    "Wearables": "MLB417704",
    "Tech": "MLB1000",
    "Iluminação": "MLB1582",
    "Bolsas": "MLB1457",
}

# Amazon individual product pages (for sales data)
AMZ_INDIVIDUAL_PLATFORM = "amazon_br"  # or "amazon_us"

def scrape_amazon(platform, cats, delay=3):
    """Scrape Amazon best sellers + individual product pages."""
    results = {}
    for cat_name, slug in cats.items():
        print(f"\n{platform} / {cat_name} ({slug})...", flush=True)
        try:
            url = f"https://www.amazon.com.br/gp/bestsellers/{slug}" if platform == "amazon_br" else f"https://www.amazon.com/gp/bestsellers/{slug}"
            html = fetch(url)
            asins = extract_amz_asins(html)
            print(f"  {len(asins)} ASINs", flush=True)
            
            found = 0
            for i, asin in enumerate(asins[:30]):
                try:
                    base_url = "amazon.com.br" if platform == "amazon_br" else "amazon.com"
                    prod_html = fetch(f"https://{base_url}/dp/{asin}")
                    sales = extract_amz_sales(prod_html)
                    if sales:
                        results[asin] = sales
                        found += 1
                except Exception as e:
                    pass
                time.sleep(delay)
            print(f"  {found}/{min(len(asins),30)} with sales")
        except Exception as e:
            print(f"  FAILED: {e}")
        time.sleep(delay)
    return results

def scrape_ml(cats, delay=3):
    """Scrape ML best sellers."""
    results = {}
    for cat_name, mlb_id in cats.items():
        print(f"\nML / {cat_name} ({mlb_id})...", flush=True)
        try:
            url = f"https://www.mercadolivre.com.br/mais-vendidos/{mlb_id}"
            html = fetch(url)
            
            # Extract from poly-cards
            cards = re.findall(r'poly-card[^>]*>.*?</poly-card', html, re.DOTALL)
            if not cards:
                # Try alternative extraction
                cards = re.findall(r'class="poly-card[^"]*"[^>]*>(.*?)</div>\s*</div>\s*</div>', html, re.DOTALL)
            
            found = 0
            # Extract MLB IDs and sales from the page
            mlb_pattern = re.findall(r'(?:MLB-|/p/MLB)(\d{8,})', html)
            sales_pattern = re.findall(r'(\d[\d,.]*)\s*vendidos', html, re.IGNORECASE)
            
            # Try to match by position
            unique_mlbs = list(dict.fromkeys(mlb_pattern))
            for i, mlb_id_found in enumerate(unique_mlbs[:30]):
                # Try to find sales near this MLB ID
                idx = html.find(mlb_id_found)
                if idx > 0:
                    context = html[max(0,idx-500):idx+500]
                    sales_match = re.search(r'(\d[\d,.]*)\s*vendidos', context, re.IGNORECASE)
                    if sales_match:
                        sales_str = sales_match.group(1).replace('.', '').replace(',', '')
                        try:
                            results[f"ML{mlb_id_found}"] = int(sales_str)
                            found += 1
                        except:
                            pass
            print(f"  {found}/{min(len(unique_mlbs),30)} with sales")
        except Exception as e:
            print(f"  FAILED: {e}")
        time.sleep(delay)
    return results

if __name__ == "__main__":
    all_results = {}
    
    # Scrape Amazon BR
    print("=" * 60)
    print("AMAZON BR")
    print("=" * 60)
    amz_br = scrape_amazon("amazon_br", AMAZON_BR)
    all_results["amazon_br"] = amz_br
    
    # Scrape Amazon US
    print("\n" + "=" * 60)
    print("AMAZON US")
    print("=" * 60)
    amz_us = scrape_amazon("amazon_us", AMAZON_US)
    all_results["amazon_us"] = amz_us
    
    # Scrape ML
    print("\n" + "=" * 60)
    print("MERCADO LIVRE")
    print("=" * 60)
    ml = scrape_ml(ML_CATS)
    all_results["ml"] = ml
    
    # Save results
    for platform, data in all_results.items():
        out_path = os.path.join(OUT_DIR, f"{platform}_sales.json")
        with open(out_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\nSaved {len(data)} products → {out_path}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for platform, data in all_results.items():
        print(f"  {platform}: {len(data)} products with sales")
