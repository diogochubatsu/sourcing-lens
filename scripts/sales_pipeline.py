#!/usr/bin/env python3
"""Sales Data Pipeline — extract sales from ML (Decodo retry) and Amazon (browser).

Usage:
    python3 scripts/sales_pipeline.py --platform ml       # ML only
    python3 scripts/sales_pipeline.py --platform amazon   # Amazon only
    python3 scripts/sales_pipeline.py --category microfone  # Single category
"""
import sys, re, time, json, os
sys.path.insert(0, '.')
from scripts.db import query, execute

# Load env for Decodo credentials
_env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', '.env')
if os.path.exists(_env_path):
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                if k.strip() not in os.environ:
                    os.environ[k.strip()] = v.strip()

_decodo_user = os.environ.get('DECODO_USER', '')
_decodo_pass = os.environ.get('DECODO_PASS', '')
DECODO_AUTH = f'{_decodo_user}:{_decodo_pass}'
DECODO_HEADERS = {'Authorization': f'Basic {DECODO_AUTH}', 'Content-Type': 'application/json'}

def extract_sales(text):
    """Parse 'X vendidos' or 'X mil vendidos' from text."""
    m = re.search(r'([\d,.]+)\s*(mil|milhão|mi)?\s*(vendidos|vendas|compras|compraram)', text, re.IGNORECASE)
    if m:
        num = float(m.group(1).replace('.', ''))
        if m.group(2) and 'mil' in m.group(2).lower(): num *= 1000
        elif m.group(2) and 'milh' in m.group(2).lower(): num *= 1000000
        return int(num)
    return None

def ml_best_sellers(category, mlb_id):
    """Extract sales from ML best sellers page via Decodo HTML with retry."""
    import requests
    from bs4 import BeautifulSoup
    
    url = f'https://www.mercadolivre.com.br/mais-vendidos/MLB{mlb_id}'
    
    for attempt in range(5):
        resp = requests.post('https://scraper-api.decodo.com/v2/scrape',
            headers=DECODO_HEADERS,
            json={'url': url, 'headless': 'html', 'proxy_pool': 'premium', 'locale': 'pt-br'},
            timeout=120)
        
        if resp.status_code != 200:
            time.sleep(5)
            continue
        
        content = resp.json()['results'][0]['content']
        
        # Check if we got rendered content
        if 'vendidos' not in content.lower():
            time.sleep(5)
            continue
        
        soup = BeautifulSoup(content, 'html.parser')
        items = soup.select('li[class*="ui-search-layout"]')
        if not items:
            items = soup.select('div[class*="andes-card"]')
        
        updated = 0
        for item in items:
            link = item.select_one('a[href*="/p/MLB"]')
            if not link: continue
            mlb_match = re.search(r'MLB-?(\d{8,})', link.get('href', ''))
            if not mlb_match: continue
            pid = 'MLB' + mlb_match.group(1)
            
            sales = extract_sales(item.get_text('|', strip=True))
            if sales:
                r = execute("UPDATE products SET sales_30d = %s WHERE platform='ml' AND platform_id=%s AND (sales_30d IS NULL OR sales_30d < %s)", (sales, pid, sales))
                if r and hasattr(r, 'rowcount') and r.rowcount and r.rowcount > 0:
                    updated += 1
        
        if updated > 0:
            return updated
    
    return 0

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--platform', choices=['ml', 'amazon'])
    parser.add_argument('--category')
    args = parser.parse_args()
    
    # ML categories with best sellers pages
    ml_cats = [
        ('Audio', 'MLB3835'),
        ('Ferramentas', 'MLB263532'),
        ('Esportes', 'MLB1276'),
        ('Acessórios Mobile', 'MLB3813'),
        ('Wearables', 'MLB417704'),
        ('Casa', 'MLB1574'),
        ('Praia', 'MLB1132'),
        ('Fotografia', 'MLB1039'),
        ('Iluminação', 'MLB430378'),
        ('Moda', 'MLB1430'),
    ]
    
    total = 0
    for cat, mlb_id in ml_cats:
        if args.category and args.category != cat:
            continue
        if args.platform and args.platform != 'ml':
            continue
        
        print(f'ML {cat}...', flush=True)
        updated = ml_best_sellers(cat, mlb_id)
        print(f'  Updated: {updated}', flush=True)
        total += updated
        time.sleep(6)
    
    print(f'\nTotal updated: {total}')
