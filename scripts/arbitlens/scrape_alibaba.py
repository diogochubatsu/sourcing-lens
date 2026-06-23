#!/usr/bin/env python3
"""
Alibaba.com scraper — uses Rakumart BR proxy API to bypass Alibaba's Baxia CAPTCHA.
Direct m.alibaba.com scraping is blocked by CAPTCHA as of 2025.
"""
import json
import re
import sys
import os
import urllib.request
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schema import ArbitlensProduct, save_products, print_summary

RAKUMART_API = "https://lavel.rakumart.com.br/client/home/searchGoods"


def _parse_price(price_val):
    """Parse price value into (low, high). Accepts float or string."""
    if price_val is None:
        return None, None
    if isinstance(price_val, (int, float)):
        return float(price_val), None
    # String fallback
    nums = re.findall(r'[\d.]+', str(price_val))
    if not nums:
        return None, None
    price_low = float(nums[0])
    price_high = float(nums[1]) if len(nums) > 1 else None
    return price_low, price_high


def scrape_alibaba(query, page=1):
    """Scrape Alibaba products via Rakumart BR proxy API."""
    body = json.dumps({'q': query, 'type': 'alibaba', 'page': page}).encode()
    req = urllib.request.Request(RAKUMART_API, data=body, headers={
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        'Content-Type': 'application/json',
        'Origin': 'https://www.rakumart.com.br',
        'Referer': 'https://www.rakumart.com.br/commoditysearch',
    })

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"  Error calling Rakumart API: {e}", file=sys.stderr)
        return []

    items = data.get('data', {}).get('content', [])
    if not items:
        return []

    products = []
    for item in items:
        pid = str(item.get('iid', ''))
        title = item.get('title', '')
        if not title:
            continue

        price_low, price_high = _parse_price(item.get('price'))

        image = item.get('picurl', '')
        if image and not image.startswith('http'):
            image = 'https:' + image

        goods_link = item.get('goods_link', '')
        product_url = goods_link if goods_link else f"https://www.alibaba.com/product-detail/_{pid}.html"

        company = item.get('shopname', '') or ''
        sales = item.get('monthSold')
        if isinstance(sales, str):
            try:
                sales = int(float(sales))
            except (ValueError, TypeError):
                sales = 0
        elif not isinstance(sales, (int, float)):
            sales = None
        else:
            sales = int(sales)

        products.append(ArbitlensProduct(
            source_platform='alibaba',
            source_product_id=pid,
            source_url=product_url,
            product_name=title,
            price_low=price_low,
            price_high=price_high,
            price_currency='USD',
            seller_name=company,
            image_url=image,
            monthly_sales=sales,
            raw_data={
                'user_type': item.get('user_type'),
                'provcity': item.get('provcity'),
            } if item.get('user_type') else None,
        ))

    return products


if __name__ == '__main__':
    query = sys.argv[1] if len(sys.argv) > 1 else "wireless+lapel+microphone+type-c"
    print(f"Scraping Alibaba (via Rakumart proxy) for: {query}")
    products = scrape_alibaba(query)
    if products:
        os.makedirs(os.path.join(os.path.dirname(__file__), 'output'), exist_ok=True)
        outpath = os.path.join(os.path.dirname(__file__), 'output', 'alibaba_mic.json')
        save_products(products, outpath)
        print_summary(products, "Alibaba")
        print(f"\nSaved to: {outpath}")
    else:
        print("No products found!")
