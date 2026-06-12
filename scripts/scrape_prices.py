"""Re-scrape prices from individual Amazon product pages for NULL-price products."""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.db import query, execute
from playwright.sync_api import sync_playwright


def parse_price(price_str):
    if not price_str or price_str == '0':
        return None
    s = price_str.replace('R$', '').replace('$', '').replace(',', '.').strip()
    try:
        s = s.replace(' ', '')
        if ',' in s:
            s = s.replace('.', '').replace(',', '.')
        return float(s)
    except (ValueError, TypeError):
        return None


def scrape_product_page(page, asin, domain):
    """Scrape a single Amazon product page for price and image."""
    url = f"https://www.{domain}/dp/{asin}"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)

        # Price
        price_el = page.query_selector('.a-price .a-offscreen')
        price_text = price_el.text_content().strip() if price_el else None
        price_val = parse_price(price_text) if price_text else None

        # Image
        img_el = page.query_selector('#landingImage')
        img_url = img_el.get_attribute('src') if img_el else None

        # Title
        title_el = page.query_selector('#productTitle')
        title = title_el.text_content().strip() if title_el else None

        return {
            'price': price_val,
            'price_text': price_text,
            'img_url': img_url,
            'title': title,
            'url': url,
            'success': price_val is not None
        }
    except Exception as e:
        return {'success': False, 'error': str(e), 'url': url}


def main():
    print("=" * 60)
    print("P1: Re-scraping individual Amazon product pages for NULL-price products")
    print("=" * 60)

    # Get all NULL-price Amazon products
    rows = query(
        "SELECT id, platform, platform_id, category, title FROM products WHERE platform IN ('amazon_br', 'amazon_us') AND price IS NULL AND is_active = true ORDER BY category, platform"
    )
    print(f"Total NULL-price Amazon products to fix: {len(rows)}")

    if not rows:
        print("Nothing to fix.")
        return

    # Group by domain
    domain_map = {'amazon_br': 'amazon.com.br', 'amazon_us': 'amazon.com'}

    updated = 0
    failed = 0
    not_found = 0

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US",
        )
        page = context.new_page()

        for i, r in enumerate(rows):
            pid = r['id']
            platform = r['platform']
            asin = r['platform_id']
            domain = domain_map[platform]
            cat = r['category']
            title = str(r['title'])[:50] if r['title'] else '(no title)'

            print(f"  [{i+1}/{len(rows)}] {platform} {asin} ({cat}) - {title}...", end=' ')

            result = scrape_product_page(page, asin, domain)

            if result['success']:
                price = result['price']
                img_url = result['img_url']
                print(f"PRICE={price:.2f} IMG={str(img_url)[:40] if img_url else 'none'}")

                image_urls = [img_url] if img_url else None
                execute(
                    "UPDATE products SET price = %s, image_urls = ARRAY[%s]::text[], last_updated = NOW() WHERE id = %s",
                    (price, img_url, pid)
                )
                updated += 1
            elif 'not found' in str(result.get('error', '')).lower() or '404' in str(result.get('error', '')):
                print(f"NOT FOUND (404)")
                execute("UPDATE products SET is_active = false, last_updated = NOW() WHERE id = %s", (pid,))
                not_found += 1
            else:
                print(f"FAILED: {result.get('error', 'unknown')}")
                failed += 1

            # Be nice to Amazon
            if (i + 1) % 10 == 0:
                print(f"  --- checkpoint: {i+1}/{len(rows)} processed, sleeping 3s ---")
                page.wait_for_timeout(3000)

        browser.close()

    print(f"\nResults: updated={updated}, not_found(404)={not_found}, failed={failed}")
    print(f"Remaining NULL-price products:")

    remaining = query(
        "SELECT category, platform, COUNT(*) AS cnt FROM products WHERE price IS NULL AND is_active = true GROUP BY category, platform ORDER BY cnt DESC"
    )
    for r in remaining:
        print(f"  {r['category']:25} {r['platform']:12}: {r['cnt']}")


if __name__ == '__main__':
    main()
