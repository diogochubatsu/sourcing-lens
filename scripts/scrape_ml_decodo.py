
"""
Auth loaded from config/decodo_scraping.key (one line, base64).
"""
import os
import sys
import json
import time
import re
import html as html_lib
import urllib.request
import hashlib

sys.path.insert(0, '/mnt/ssd/arbitlens')
from scripts.db import get_conn

DECODO_ENDPOINT = 'https://scraper-api.decodo.com/v2/scrape'
AUTH_FILE = '/mnt/ssd/arbitlens/config/decodo_scraping.key'


def load_auth():
    """Load Decodo auth from secrets file."""
    if os.path.exists(AUTH_FILE):
        with open(AUTH_FILE) as f:
            return f.read().strip()
    return os.environ.get('DECODO_API_AUTH', '')


ML_CATEGORIES = {
    'Beleza': 'MLB1246',
    'Brinquedos': 'MLB1132',
    'Bebe': 'MLB1384',
}


def fetch_ml_page(category_id, retries=2):
    """Fetch a ML best-sellers page using Decodo Scraping API."""
    auth = load_auth()
    url = f"https://www.mercadolivre.com.br/mais-vendidos/{category_id}"

    for attempt in range(retries + 1):
        try:
            payload = json.dumps({
                "url": url,
                "headless": "html",
                "locale": "pt-br"
            }).encode()

            req = urllib.request.Request(DECODO_ENDPOINT, data=payload, method='POST')
            req.add_header('Authorization', f'Basic {auth}')
            req.add_header('Content-Type', 'application/json')

            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read().decode('utf-8', errors='replace')
                data = json.loads(body)
                if 'results' in data and data['results']:
                    return data['results'][0].get('content', '')
                return ''
        except Exception as e:
            print(f"  Attempt {attempt+1}: ERROR {e}")
            if attempt < retries:
                time.sleep(2)
    return ''


def parse_ml_products(html, max_products=30):
    """Parse products from ML mais-vendidos HTML."""
    products = []
    product_ids = list(set(re.findall(r'"product_id":"(MLB\d+)"', html)))

    for pid in product_ids[:max_products]:
        product = extract_product(html, pid)
        if product:
            products.append(product)

    return products


def extract_product(html, product_id):
    """Extract details for a single product."""
    pos = html.find(f'"product_id":"{product_id}"')
    if pos < 0:
        return None

    start = max(0, pos - 200)
    end = min(len(html), pos + 3000)
    block = html[start:end]

    title = ''
    tm = re.search(r'"title":\{"text":"([^"]+)"', block)
    if tm:
        title = html_lib.unescape(tm.group(1))

    price = 0.0
    pm = re.search(r'"current_price":\{"value":([\d.]+)', block)
    if not pm:
        pm = re.search(r'"price":\{[^}]*?"value":([\d.]+)', block)
    if pm:
        try:
            price = float(pm.group(1))
        except:
            pass

    url = f"https://www.mercadolivre.com.br/p/{product_id}"
    um = re.search(r'"url":"((?:https?://)?www\.mercadolivre\.com\.br[^"]+)"', block)
    if um:
        url_raw = um.group(1).replace('\\u002F', '/')
        if not url_raw.startswith('http'):
            url_raw = 'https://' + url_raw
        url = url_raw

    # Image - extract picture_id and construct ML CDN URL
    image_url = None
    pm2 = re.search(r'"pictures":\{"scale":"[^"]+","pictures":\[\{"id":"([^"]+)"', block)
    if pm2:
        pic_id = pm2.group(1)
        image_url = "https://http2.mlstatic.com/D_Q_NP_2X_" + pic_id + "-AB.webp"

    if not title:
        return None

    return {
        'platform_id': product_id,
        'title': title,
        'price': price,
        'currency': 'BRL',
        'url': url,
        'image_url': image_url,
    }


def upsert_ml_product(product, category_l1):
    """Insert or update a ML product."""
    image_hash = hashlib.sha256(
        (product.get('image_url') or product.get('url', '')).encode()
    ).hexdigest()

    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id FROM products WHERE platform = 'ml' AND platform_id = %s",
                (product['platform_id'],)
            )
            existing = cur.fetchone()

            if existing:
                cur.execute("""
                    UPDATE products SET
                        title = %s, price = %s, currency = %s, url = %s,
                        category_l1 = %s, image_urls = %s,
                        image_hash = COALESCE(%s, image_hash),
                        last_updated = NOW()
                    WHERE platform = 'ml' AND platform_id = %s
                """, (
                    product['title'], product['price'], product['currency'],
                    product['url'], category_l1,
                    [product['image_url']] if product['image_url'] else None,
                    image_hash,
                    product['platform_id']
                ))
                action = "updated"
            else:
                cur.execute("""
                    INSERT INTO products (
                        platform, platform_id, title, price, currency, url,
                        category_l1, image_urls, image_hash, is_active
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, true)
                """, (
                    'ml', product['platform_id'], product['title'],
                    product['price'], product['currency'], product['url'],
                    category_l1,
                    [product['image_url']] if product['image_url'] else None,
                    image_hash
                ))
                action = "inserted"
            conn.commit()
            cur.close()
            return action
    except Exception as e:
        print(f"  DB error: {e}")
        return "error"


def scrape_category(category_name, category_id):
    """Scrape ML best-sellers for a category."""
    print(f"\n{'='*60}")
    print(f"Scraping {category_name} ({category_id})")
    print(f"{'='*60}")

    html = fetch_ml_page(category_id)
    if not html:
        print(f"  FAILED to fetch page")
        return {"category": category_name, "scraped": 0, "inserted": 0, "errors": 1}

    print(f"  Page size: {len(html):,} bytes")

    products = parse_ml_products(html, max_products=30)
    print(f"  Parsed {len(products)} products")

    if not products:
        with open(f'/tmp/ml_clean_{category_id}.html', 'w') as f:
            f.write(html)
        print(f"  Saved clean HTML for debug")
        return {"category": category_name, "scraped": 0, "inserted": 0, "errors": 1}

    for p in products[:3]:
        print(f"  {p['platform_id']} | R${p['price']:.2f} | {p['title'][:50]}")

    inserted = updated = errors = 0
    for p in products:
        result = upsert_ml_product(p, category_name)
        if result == "inserted":
            inserted += 1
        elif result == "updated":
            updated += 1
        else:
            errors += 1

    print(f"  Result: {inserted} inserted, {updated} updated, {errors} errors")
    return {
        "category": category_name,
        "scraped": len(products),
        "inserted": inserted,
        "updated": updated,
        "errors": errors
    }


if __name__ == '__main__':
    print("ML Best-Sellers Scraper (Decodo Scraping API)")
    print("=" * 60)

    results = []
    for cat_name, cat_id in ML_CATEGORIES.items():
        result = scrape_category(cat_name, cat_id)
        results.append(result)
        time.sleep(1)

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    total_ins = total_upd = total_err = 0
    for r in results:
        print(f"  {r['category']}: {r.get('inserted', 0)} inserted, {r.get('updated', 0)} updated, {r.get('errors', 0)} errors")
        total_ins += r.get('inserted', 0)
        total_upd += r.get('updated', 0)
        total_err += r.get('errors', 0)
    print(f"\n  TOTAL: {total_ins} inserted, {total_upd} updated, {total_err} errors")
