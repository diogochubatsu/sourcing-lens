#!/usr/bin/env python3
"""
1688.com Direct Scraper — Uses Decodo Site Unblocker + Playwright.

Scrapes 1688.com directly with residential proxy and headless browser
to bypass CAPTCHA and render JavaScript.

Usage:
  python3 scrape_1688_direct.py "microfone bluetooth" 30
"""
import json
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schema import ArbitlensProduct, save_products, print_summary

# Decodo Site Unblocker credentials
DECODO_USER = os.environ.get('SU_USER')
DECODO_PASS = os.environ.get('SU_PASS')
DECODO_HOST = 'unblock.decodo.com'
DECODO_PORT = '60000'


def scrape_1688_direct(query, limit=30):
    """Scrape 1688 search results using Playwright + Decodo proxy."""
    from playwright.sync_api import sync_playwright
    
    proxy_url = f"http://{DECODO_USER}:{DECODO_PASS}@{DECODO_HOST}:{DECODO_PORT}"
    
    products = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            proxy={"server": proxy_url}
        )
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            locale='zh-CN',
        )
        page = context.new_page()
        
        try:
            # Navigate to 1688 search
            encoded_query = query.replace(' ', '+')
            url = f'https://s.1688.com/selloffer/offer_search.htm?keywords={encoded_query}'
            page.goto(url, timeout=60000, wait_until='networkidle')
            
            # Wait for products to load
            page.wait_for_selector('.sm-offer-item, .offer-list-row', timeout=30000)
            
            # Extract products
            items = page.query_selector_all('.sm-offer-item, .offer-list-row')
            
            for item in items[:limit]:
                try:
                    # Title
                    title_el = item.query_selector('.title, .offer-title, a[title]')
                    title = title_el.get_attribute('title') or title_el.inner_text() if title_el else ''
                    
                    # Price
                    price_el = item.query_selector('.price, .sm-offer-priceNum')
                    price_text = price_el.inner_text() if price_el else ''
                    price_match = re.search(r'[\d.]+', price_text)
                    price = float(price_match.group()) if price_match else None
                    
                    # Image
                    img_el = item.query_selector('img')
                    image = img_el.get_attribute('src') if img_el else None
                    if image and not image.startswith('http'):
                        image = 'https:' + image
                    
                    # Link
                    link_el = item.query_selector('a[href*="detail.1688.com"]')
                    link = link_el.get_attribute('href') if link_el else None
                    if link and not link.startswith('http'):
                        link = 'https:' + link
                    
                    if title and len(title) > 5:
                        products.append(ArbitlensProduct(
                            source_platform='1688-direct',
                            source_product_id=link.split('/')[-1].split('.html')[0] if link else str(len(products)),
                            source_url=link or '',
                            product_name=title[:200],
                            price_low=price,
                            price_currency='CNY',
                            image_url=image or '',
                        ))
                except Exception:
                    continue
        
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
        
        finally:
            browser.close()
    
    return products


if __name__ == '__main__':
    query = sys.argv[1] if len(sys.argv) > 1 else 'microfone bluetooth'
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    print(f"Scraping 1688 Direct via Decodo + Playwright: '{query}'")
    products = scrape_1688_direct(query, limit)
    
    if products:
        os.makedirs(os.path.join(os.path.dirname(__file__), 'output'), exist_ok=True)
        outpath = os.path.join(os.path.dirname(__file__), 'output', '1688_direct.json')
        save_products(products, outpath)
        print_summary(products, "1688 Direct")
        print(f"\nSaved to: {outpath}")
    else:
        print("No products found!")
