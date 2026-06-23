#!/usr/bin/env python3
"""
Rakumart.com.br scraper — Brazilian 1688/Taobao/Alibaba proxy.
3 data sources, no auth needed. BRL prices.

KEY FINDING: 1688/Taobao tabs use form-encoded data, not JSON!
"""
import json
import sys
import os
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schema import ArbitlensProduct, save_products, print_summary
from cn_pt_dict import translate_if_chinese


def search_rakumart_br(query, source='1688', page=1):
    """Search Rakumart BR across 3 sources."""
    if source == 'alibaba':
        url = "https://lavel.rakumart.com.br/client/home/searchGoods"
        body = json.dumps({'q': query, 'type': 'alibaba', 'page': page}).encode()
        content_type = 'application/json'
    else:
        url = "https://api.rakumart.com.br/index.php?mod=inc&act=ordersysPc&str=searchGoods"
        body = f"q={query.replace(' ', '+')}&type={source}&filter=&sort=&priceStart=&priceEnd=&snId=&page={page}".encode()
        content_type = 'application/x-www-form-urlencoded'

    req = urllib.request.Request(url, data=body, headers={
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': content_type,
        'Origin': 'https://www.rakumart.com.br',
        'Referer': 'https://www.rakumart.com.br/commoditysearch',
    })

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"  Error ({source}): {e}")
        return []

    items = data.get('data', {}).get('content', [])
    products = []

    for item in items:
        title = item.get('title', '')
        # Translate Taobao titles from Chinese to Portuguese
        if source == 'taobao':
            title = translate_if_chinese(title)
        price = item.get('price')
        if isinstance(price, str):
            import re
            nums = re.findall(r'[\d.]+', price)
            price = float(nums[0]) if nums else None

        image = item.get('picurl', '')
        if image and not image.startswith('http'):
            image = 'https:' + image

        rep = item.get('repurchaseRate')
        rep_str = f"{rep}%" if rep and str(rep) != '0' else ''

        iid = str(item.get('iid', ''))
        goods_link = item.get('goods_link', '')
        product_url = goods_link if goods_link else f"https://www.rakumart.com.br/product/{iid}"

        # Extract new fields
        title_cn = item.get('titleC', '')
        top_cat_id = item.get('topCategoryId', [None])[0] if item.get('topCategoryId') else None
        second_cat_id = item.get('secondCategoryId', [None])[0] if item.get('secondCategoryId') else None
        third_cat_id = item.get('thirdCategoryId', [None])[0] if item.get('thirdCategoryId') else None
        trade_score = float(item.get('tradeScore', 0) or 0) or None
        seller_identities = item.get('sellerIdentities', [])
        shop_info = item.get('shopInfo', {})
        shop_address = shop_info.get('address', '') if isinstance(shop_info, dict) else ''
        create_date = item.get('createDate')
        modify_date = item.get('modifyDate')

        products.append(ArbitlensProduct(
            source_platform=f'rakumart-{source}',
            source_product_id=iid,
            source_url=product_url,
            product_name=title,
            price_low=price,
            price_currency='BRL',
            seller_name=item.get('shopname', '') or '',
            image_url=image,
            monthly_sales=item.get('monthSold'),
            raw_data={
                'source': source,
                'repurchase_rate': rep_str,
                'user_type': item.get('user_type'),
                'provcity': item.get('provcity'),
                'title_cn': title_cn,
                'top_category_id': top_cat_id,
                'second_category_id': second_cat_id,
                'third_category_id': third_cat_id,
                'trade_score': trade_score,
                'seller_identities': seller_identities,
                'shop_address': shop_address,
                'create_date': create_date,
                'modify_date': modify_date,
            },
        ))

    return products


if __name__ == '__main__':
    query = sys.argv[1] if len(sys.argv) > 1 else 'microfone lapela'
    source = sys.argv[2] if len(sys.argv) > 2 else '1688'

    print(f"Scraping Rakumart BR ({source}): '{query}'")
    products = search_rakumart_br(query, source=source)

    if products:
        os.makedirs(os.path.join(os.path.dirname(__file__), 'output'), exist_ok=True)
        outpath = os.path.join(os.path.dirname(__file__), 'output', f'rakumart_br_{source}.json')
        save_products(products, outpath)
        print_summary(products, f"Rakumart BR ({source})")
        print(f"\nSaved to: {outpath}")

        with_sales = [p for p in products if p.monthly_sales and p.monthly_sales > 0]
        if with_sales:
            print(f"\nTop by sales:")
            for p in sorted(with_sales, key=lambda x: x.monthly_sales, reverse=True)[:5]:
                rep = p.raw_data.get('repurchase_rate', '?') if p.raw_data else '?'
                print(f"  {p.monthly_sales:>5}/mo | rep:{rep:>6} | R${p.price_low:.2f} | {p.product_name[:50]}")
    else:
        print("No products found!")
