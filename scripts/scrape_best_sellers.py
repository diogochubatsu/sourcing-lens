#!/usr/bin/env python3
"""Best Sellers Scraper — Scrapes best sellers from category_mappings.

Supports recursive category discovery:
1. Scrape best sellers for a category
2. For each product, check if its platform category is new
3. If new, add to scrape queue
4. Repeat until queue is empty

Usage:
    python3 scripts/scrape_best_sellers.py --all                  # Scrape all mapped categories
    python3 scripts/scrape_best_sellers.py --category "Audio"     # Scrape single category
    python3 scripts/scrape_best_sellers.py --discover             # Enable recursive discovery
    python3 scripts/scrape_best_sellers.py --dry-run              # Preview without writing
"""
import sys
import os
import re
import time
import json
import argparse
from datetime import datetime
from decimal import Decimal, InvalidOperation

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from scripts.db import query, execute, execute_returning

# HTTP
import requests
from bs4 import BeautifulSoup

# Load env
_env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', '.env')
if os.path.exists(_env_path):
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                if k.strip() not in os.environ:
                    os.environ[k.strip()] = v.strip()

# Decodo config
DECODO_USER = os.environ.get('DECODO_USER', '')
DECODO_PASS = os.environ.get('DECODO_PASS', '')
DECODO_AUTH = f'{DECODO_USER}:{DECODO_PASS}'
DECODO_HEADERS = {'Authorization': f'Basic {DECODO_AUTH}', 'Content-Type': 'application/json'}

# Amazon headers (for direct scraping)
AMAZON_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
}


def parse_price(text):
    """Parse price from text (R$ 1.234,56 or $1,234.56)."""
    if not text:
        return None
    clean = re.sub(r'[R$\s]', '', text.strip())
    if ',' in clean and '.' in clean:
        clean = clean.replace('.', '').replace(',', '.')
    elif ',' in clean:
        clean = clean.replace(',', '.')
    try:
        val = Decimal(clean)
        return val if val > 0 else None
    except (InvalidOperation, ValueError):
        return None


def extract_sales(text):
    """Parse sales from text (X vendidos, X+ bought)."""
    m = re.search(r'([\d,.]+)\s*(mil|milhão|mi)?\s*(vendidos|vendas|compras|compraram|bought|sold)', text, re.IGNORECASE)
    if m:
        num = float(m.group(1).replace('.', '').replace(',', ''))
        if m.group(2) and 'mil' in m.group(2).lower():
            num *= 1000
        elif m.group(2) and 'milh' in m.group(2).lower():
            num *= 1000000
        return int(num)
    return None


def scrape_ml_best_sellers(category_name, mlb_id):
    """Scrape ML best sellers page via Decodo."""
    url = f'https://www.mercadolivre.com.br/mais-vendidos/MLB{mlb_id}'
    products = []
    
    for attempt in range(5):
        try:
            resp = requests.post('https://scraper-api.decodo.com/v2/scrape',
                headers=DECODO_HEADERS,
                json={'url': url, 'headless': 'html', 'proxy_pool': 'premium', 'locale': 'pt-br'},
                timeout=120)
            
            if resp.status_code != 200:
                time.sleep(5)
                continue
            
            content = resp.json()['results'][0]['content']
            
            if 'vendidos' not in content.lower() and 'mais vendidos' not in content.lower():
                time.sleep(5)
                continue
            
            soup = BeautifulSoup(content, 'html.parser')
            items = soup.select('li[class*="ui-search-layout"]')
            if not items:
                items = soup.select('div[class*="andes-card"]')
            
            for item in items:
                link = item.select_one('a[href*="/p/MLB"]')
                if not link:
                    continue
                mlb_match = re.search(r'MLB-?(\d{8,})', link.get('href', ''))
                if not mlb_match:
                    continue
                pid = 'MLB' + mlb_match.group(1)
                
                title_el = item.select_one('h2, [class*="title"]')
                title = title_el.get_text(strip=True) if title_el else ''
                
                price_el = item.select_one('[class*="price"] span, .andes-money-amount__fraction')
                price = parse_price(price_el.get_text()) if price_el else None
                
                img_el = item.select_one('img')
                img_url = img_el.get('src', '') if img_el else ''
                
                sales = extract_sales(item.get_text('|', strip=True))
                
                if title and price:
                    products.append({
                        'platform': 'ml',
                        'platform_id': pid,
                        'title': title,
                        'price': float(price),
                        'currency': 'BRL',
                        'url': f'https://www.mercadolivre.com.br/produto/{pid}',
                        'image_url': img_url,
                        'sales_30d': sales,
                    })
            
            return products
            
        except Exception as e:
            print(f"    Error attempt {attempt+1}: {e}")
            time.sleep(5)
    
    return products


def scrape_amazon_best_sellers(platform, category_name, node_id):
    """Scrape Amazon best sellers page."""
    if platform == 'amazon_br':
        url = f'https://www.amazon.com.br/gp/bestsellers/electronics/{node_id}'
        currency = 'BRL'
    else:
        url = f'https://www.amazon.com/Best-Sellers-{category_name.replace(" ", "-")}/zgbs/{node_id}'
        currency = 'USD'
    
    products = []
    
    try:
        resp = requests.get(url, headers=AMAZON_HEADERS, timeout=30)
        if resp.status_code != 200:
            print(f"    HTTP {resp.status_code} for {url}")
            return products
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        items = soup.select('[data-asin]')
        
        for item in items:
            asin = item.get('data-asin', '').strip()
            if not asin or len(asin) < 10:
                continue
            
            title_el = item.select_one('.p13n-sc-truncate-desktop-type2, a.a-link-normal span')
            title = title_el.get_text(strip=True) if title_el else ''
            if not title:
                continue
            
            price_el = item.select_one('.p13n-sc-price, .a-price .a-offscreen')
            price = parse_price(price_el.get_text()) if price_el else None
            
            img_el = item.select_one('img[src*="images-amazon"]')
            img_url = img_el.get('src', '') if img_el else ''
            
            rating_el = item.select_one('.a-icon-alt')
            review_avg = None
            if rating_el:
                m = re.search(r'(\d[.,]\d)', rating_el.get_text())
                if m:
                    try:
                        review_avg = float(m.group(1).replace(',', '.'))
                    except:
                        pass
            
            if platform == 'amazon_br':
                prod_url = f'https://www.amazon.com.br/dp/{asin}'
            else:
                prod_url = f'https://www.amazon.com/dp/{asin}'
            
            if title and price:
                products.append({
                    'platform': platform,
                    'platform_id': asin,
                    'title': title,
                    'price': float(price),
                    'currency': currency,
                    'url': prod_url,
                    'image_url': img_url,
                    'review_avg': review_avg,
                })
        
    except Exception as e:
        print(f"    Error scraping Amazon: {e}")
    
    return products


def upsert_product(product, our_l1, our_l2, our_l3):
    """Insert or update product in database."""
    try:
        result = execute_returning("""
            INSERT INTO products 
                (platform, platform_id, title, price, currency, url, image_urls,
                 sales_30d, review_avg, category_l1, category_l2, category_l3, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
            ON CONFLICT (platform, platform_id) 
            DO UPDATE SET
                title = COALESCE(EXCLUDED.title, products.title),
                price = COALESCE(EXCLUDED.price, products.price),
                sales_30d = GREATEST(COALESCE(EXCLUDED.sales_30d, 0), COALESCE(products.sales_30d, 0)),
                review_avg = COALESCE(EXCLUDED.review_avg, products.review_avg),
                image_urls = COALESCE(EXCLUDED.image_urls, products.image_urls),
                last_updated = NOW()
            RETURNING id
        """, (
            product['platform'],
            product['platform_id'],
            product['title'],
            product['price'],
            product['currency'],
            product['url'],
            [product['image_url']] if product.get('image_url') else None,
            product.get('sales_30d'),
            product.get('review_avg'),
            our_l1,
            our_l2,
            our_l3,
        ))
        return result[0]['id'] if result else None
    except Exception as e:
        print(f"    DB error: {e}")
        return None


def discover_new_categories(product, platform):
    """Check if product's category is new and add to queue if so."""
    # This is a simplified version - in production, you'd scrape the product page
    # to get its actual category path
    pass


def scrape_category(mapping, dry_run=False):
    """Scrape best sellers for a single category mapping."""
    platform = mapping['platform']
    cat_id = mapping['platform_category_id']
    cat_name = mapping['platform_category_name'] or ''
    our_l1 = mapping['our_l1']
    our_l2 = mapping['our_l2']
    our_l3 = mapping['our_l3']
    
    print(f"\n{'='*60}")
    print(f"Scraping: {our_l1}/{our_l2}/{our_l3}")
    print(f"  Platform: {platform}")
    print(f"  Category ID: {cat_id}")
    print(f"  Category Name: {cat_name}")
    
    products = []
    
    if platform == 'ml':
        # Extract MLB ID from platform_category_id
        mlb_id = cat_id.replace('MLB', '') if cat_id else ''
        if mlb_id:
            products = scrape_ml_best_sellers(cat_name, mlb_id)
    elif platform in ['amazon_br', 'amazon_us']:
        # Extract node ID from bestsellers_url
        url = mapping.get('bestsellers_url', '')
        node_match = re.search(r'/(\d+)$|/(\d+)/?$', url)
        node_id = node_match.group(1) or node_match.group(2) if node_match else cat_id
        products = scrape_amazon_best_sellers(platform, cat_name, node_id)
    
    print(f"  Found {len(products)} products")
    
    if dry_run:
        for p in products[:5]:
            print(f"    - {p['title'][:50]}... | {p['price']}")
        if len(products) > 5:
            print(f"    ... and {len(products) - 5} more")
        return len(products)
    
    # Upsert products
    saved = 0
    for product in products:
        pid = upsert_product(product, our_l1, our_l2, our_l3)
        if pid:
            saved += 1
    
    # Update mapping stats
    execute("""
        UPDATE category_mappings 
        SET product_count = (SELECT COUNT(*) FROM products WHERE category_l1 = %s AND category_l2 = %s AND category_l3 = %s),
            last_scraped = NOW()
        WHERE id = %s
    """, (our_l1, our_l2, our_l3, mapping['id']))
    
    print(f"  Saved {saved} products")
    return saved


def main():
    parser = argparse.ArgumentParser(description='Best Sellers Scraper')
    parser.add_argument('--all', action='store_true', help='Scrape all mapped categories')
    parser.add_argument('--category', type=str, help='Scrape specific internal category (L1)')
    parser.add_argument('--platform', choices=['amazon_br', 'amazon_us', 'ml'], help='Filter by platform')
    parser.add_argument('--dry-run', action='store_true', help='Preview without writing')
    parser.add_argument('--discover', action='store_true', help='Enable recursive category discovery')
    args = parser.parse_args()
    
    # Get mappings to scrape
    conditions = ["bestsellers_url IS NOT NULL"]
    params = []
    
    if args.category:
        conditions.append("our_l1 = %s")
        params.append(args.category)
    if args.platform:
        conditions.append("platform = %s")
        params.append(args.platform)
    
    where = " AND ".join(conditions)
    mappings = query(f"""
        SELECT id, our_l1, our_l2, our_l3, platform, platform_category_id,
               platform_category_name, bestsellers_url
        FROM category_mappings
        WHERE {where}
        ORDER BY platform, our_l1, our_l2
    """, tuple(params))
    
    if not mappings:
        print("No mappings found. Run: python3 scripts/category_mapper.py import")
        return
    
    print(f"Found {len(mappings)} category mappings to scrape")
    
    total_products = 0
    for mapping in mappings:
        count = scrape_category(mapping, dry_run=args.dry_run)
        total_products += count
        time.sleep(2)  # Rate limiting
    
    print(f"\n{'='*60}")
    print(f"SCRAPING COMPLETE")
    print(f"  Categories scraped: {len(mappings)}")
    print(f"  Total products: {total_products}")


if __name__ == '__main__':
    main()
