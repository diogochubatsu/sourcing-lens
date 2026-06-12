"""Fix data quality issues on ArbitLens DB.

P1: Re-scrape 150 NULL-price products from bluetooth_speaker and smartwatch (amazon_br + amazon_us)
P2: Fix tripod prices (check Amazon product pages)
P3: Log products without images/URLs
P4: Handle products without URL
"""
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.db import query, execute
from playwright.sync_api import sync_playwright

AMAZON_PAGES = [
    # (label, category, platform, url)
    ("amazon_br_bluetooth_speaker", "bluetooth_speaker", "amazon_br",
     "https://www.amazon.com.br/gp/bestsellers/electronics/16244069011"),
    ("amazon_br_smartwatch", "smartwatch", "amazon_br",
     "https://www.amazon.com.br/gp/bestsellers/electronics/16243897011"),
    ("amazon_us_bluetooth_speaker", "bluetooth_speaker", "amazon_us",
     "https://www.amazon.com/Best-Sellers-Portable-Speakers-Docks/zgbs/electronics/689637011"),
    ("amazon_us_smartwatch", "smartwatch", "amazon_us",
     "https://www.amazon.com/Best-Sellers-Smartwatches/zgbs/electronics/7939901011"),
]

EXTRACTION_JS = """
var items = [];
document.querySelectorAll('[data-asin]').forEach(function(el) {
    var asin = el.getAttribute('data-asin');
    if (asin && asin.length > 8) {
        var titleEl = el.querySelector('span[data-a-size]');
        var priceEl = el.querySelector('.a-price .a-offscreen');
        var imgEl = el.querySelector('img');
        items.push({
            asin: asin,
            title: titleEl ? titleEl.textContent.trim() : '',
            price: priceEl ? priceEl.textContent.trim() : '0',
            img: imgEl ? imgEl.src : ''
        });
    }
});
console.log(JSON.stringify(items.filter(i => i.price !== '0')));
"""

def parse_price(price_str):
    """Parse Amazon price string to float."""
    if not price_str or price_str == '0':
        return None
    price_str = price_str.replace('R$', '').replace('$', '').replace(',', '.').strip()
    try:
        price_str = price_str.replace(' ', '')
        if ',' in price_str:
            price_str = price_str.replace('.', '').replace(',', '.')
        return float(price_str)
    except (ValueError, TypeError):
        return None


def scrape_amazon_page(label, category, platform, url):
    """Navigate to Amazon best sellers page, extract products, fix DB."""
    print(f"\n{'='*60}")
    print(f"Scraping: {label}")
    print(f"URL: {url}")
    print(f"{'='*60}")

    existing = query(
        "SELECT id, platform_id, title FROM products WHERE category = %s AND platform = %s AND price IS NULL AND is_active = true",
        (category, platform)
    )
    existing_by_asin = {r['platform_id']: r for r in existing}
    print(f"Found {len(existing)} existing NULL-price products for {platform} {category}")

    if not existing_by_asin:
        print("No NULL-price products to fix for this page.")
        return {'scraped': 0, 'matched': 0, 'updated': 0}

    result = {'scraped': 0, 'matched': 0, 'updated': 0}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US" if "us" in platform else "pt-BR",
        )
        page = context.new_page()

        try:
            print(f"  Navigating...")
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(3000)
            try:
                page.wait_for_selector('[data-asin]', timeout=15000)
            except Exception:
                print("  WARNING: Could not find [data-asin] elements, trying to scroll")
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(3000)
                page.evaluate("window.scrollTo(0, 0)")
                page.wait_for_timeout(2000)

            items_json = page.evaluate(EXTRACTION_JS)
            items = json.loads(items_json) if items_json else []
            print(f"  Scraped {len(items)} products with prices from page")

            for item in items:
                asin = item['asin']
                price_val = parse_price(item['price'])
                img_url = item['img']

                if asin in existing_by_asin:
                    prod = existing_by_asin[asin]
                    result['matched'] += 1
                    if price_val and price_val > 0:
                        image_urls = [img_url] if img_url else None
                        execute(
                            "UPDATE products SET price = %s, image_urls = ARRAY[%s]::text[], last_updated = NOW() WHERE id = %s",
                            (price_val, img_url, prod['id'])
                        )
                        result['updated'] += 1
                        print(f"    UPDATED id={prod['id']} ASIN={asin}: ${price_val:.2f} - {item['title'][:50]}")
                    else:
                        print(f"    SKIPPED id={prod['id']} ASIN={asin}: price still 0")

            result['scraped'] = len(items)

        except Exception as e:
            print(f"  ERROR scraping {url}: {e}")
            result['error'] = str(e)
        finally:
            browser.close()

    unmatched = len(existing_by_asin) - result['matched']
    print(f"  Result: scraped={result['scraped']}, matched={result['matched']}, updated={result['updated']}, unmatched_in_db={unmatched}")
    return result


def check_remaining_nulls():
    """Check remaining products with NULL price."""
    return query(
        "SELECT category, platform, COUNT(*) AS cnt FROM products WHERE price IS NULL AND is_active = true GROUP BY category, platform ORDER BY cnt DESC"
    )


def handle_p2_tripod():
    """P2: Check tripod NULL-price products."""
    print(f"\n{'='*60}")
    print("P2: Fixing tripod NULL prices")
    print(f"{'='*60}")

    rows = query(
        "SELECT id, platform, platform_id, title FROM products WHERE category = 'tripod' AND price IS NULL AND is_active = true ORDER BY id"
    )

    if not rows:
        print("No NULL-price tripods to fix.")
        return {'checked': 0, 'deactivated': 0}

    result = {'deactivated': 0, 'checked': len(rows)}

    amazon_br_tripods = [r for r in rows if r['platform'] == 'amazon_br']
    ml_tripods = [r for r in rows if r['platform'] == 'ml']

    print(f"  amazon_br tripods with NULL price: {len(amazon_br_tripods)}")
    print(f"  ml tripods with NULL price: {len(ml_tripods)}")

    if amazon_br_tripods:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                locale="pt-BR",
            )
            page = context.new_page()

            for prod in amazon_br_tripods:
                url = f"https://www.amazon.com.br/dp/{prod['platform_id']}"
                try:
                    print(f"  Checking {prod['platform']}:{prod['platform_id']}...")
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(3000)

                    price_el = page.query_selector('.a-price .a-offscreen')
                    title_el = page.query_selector('#productTitle')

                    if price_el:
                        price_text = price_el.text_content().strip()
                        price_val = parse_price(price_text)
                        if price_val and price_val > 0:
                            print(f"    -> Price found: {price_text} = {price_val}")
                            execute(
                                "UPDATE products SET price = %s, last_updated = NOW() WHERE id = %s",
                                (price_val, prod['id'])
                            )
                        else:
                            print(f"    -> Could not parse price: {price_text}")
                            execute("UPDATE products SET is_active = false, last_updated = NOW() WHERE id = %s", (prod['id'],))
                            result['deactivated'] += 1
                    else:
                        current_url = page.url
                        print(f"    -> No price element. URL: {current_url[:80]}")
                        execute("UPDATE products SET is_active = false, last_updated = NOW() WHERE id = %s", (prod['id'],))
                        result['deactivated'] += 1
                except Exception as e:
                    print(f"    -> Error: {e}")
                    execute("UPDATE products SET is_active = false, last_updated = NOW() WHERE id = %s", (prod['id'],))
                    result['deactivated'] += 1

            browser.close()

    for prod in ml_tripods:
        print(f"  Deactivating ML tripod id={prod['id']} (no ML scraper)")
        execute("UPDATE products SET is_active = false, last_updated = NOW() WHERE id = %s", (prod['id'],))
        result['deactivated'] += 1

    return result


def handle_p3_p4():
    """P3: Log products without image_hash. P4: Fix or deactivate products without URL."""
    print(f"\n{'='*60}")
    print("P3: Products without image_hash")
    print(f"{'='*60}")

    rows = query(
        "SELECT id, category, platform, platform_id, image_urls, url FROM products WHERE (image_hash IS NULL OR image_hash = '') AND is_active = true ORDER BY category, platform"
    )

    print(f"Total products without image_hash: {len(rows)}")
    for r in rows:
        has_img_urls = r['image_urls'] is not None and len(r['image_urls']) > 0 and r['image_urls'][0] != ''
        has_url = r['url'] is not None and r['url'] != ''
        print(f"  id={r['id']:>4}, {r['category']:20} {r['platform']:10} pid={r['platform_id']:20} has_img={has_img_urls} has_url={has_url}")
        print(f"    -> CANNOT FIX — no image URLs available to compute hash")

    print(f"\n{'='*60}")
    print("P4: Products without URL")
    print(f"{'='*60}")

    rows = query(
        "SELECT id, category, platform, platform_id, url FROM products WHERE (url IS NULL OR url = '') AND is_active = true ORDER BY id"
    )

    print(f"Total products without URL: {len(rows)}")
    deactivated_count = 0
    fixed_count = 0

    for r in rows:
        platform = r['platform']
        pid = r['platform_id']
        new_url = None
        if platform in ('amazon_br', 'amazon_us'):
            domain = "amazon.com.br" if platform == 'amazon_br' else "amazon.com"
            new_url = f"https://www.{domain}/dp/{pid}"
        elif platform == 'ml':
            ml_id = pid.replace('MLB', '')
            new_url = f"https://www.mercadolivre.com.br/p/MLB{ml_id}" if ml_id.isdigit() else None

        if new_url:
            execute("UPDATE products SET url = %s, last_updated = NOW() WHERE id = %s", (new_url, r['id']))
            print(f"  FIXED id={r['id']:>4}, {r['category']:20} {platform:10} -> {new_url}")
            fixed_count += 1
        else:
            execute("UPDATE products SET is_active = false, last_updated = NOW() WHERE id = %s", (r['id'],))
            print(f"  DEACTIVATED id={r['id']:>4}, {r['category']:20} {platform:10} (cannot reconstruct URL)")
            deactivated_count += 1

    return {'fixed': fixed_count, 'deactivated': deactivated_count}


def main():
    results = {}

    # P1: Re-scrape Amazon best sellers pages
    print("\n*** P1: Re-scraping Amazon best sellers pages ***")
    p1_results = {}
    for label, category, platform, url in AMAZON_PAGES:
        res = scrape_amazon_page(label, category, platform, url)
        p1_results[label] = res
    results['p1'] = p1_results

    # Check remaining NULL prices
    print(f"\n{'='*60}")
    print("Remaining NULL-price products after P1:")
    print(f"{'='*60}")
    remaining = check_remaining_nulls()
    for r in remaining:
        print(f"  {r['category']:25} {r['platform']:12}: {r['cnt']}")

    # P2: Handle tripod NULL prices
    results['p2'] = handle_p2_tripod()

    # P3: Log products without image_hash
    # P4: Fix products without URL
    results['p3_p4'] = handle_p3_p4()

    # Final summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")

    total_updated = sum(r.get('updated', 0) for r in p1_results.values())
    for label, res in p1_results.items():
        print(f"  P1-{label}: scraped={res.get('scraped',0)}, matched={res.get('matched',0)}, updated={res.get('updated',0)}")
    print(f"  P1 total updated: {total_updated}")

    print(f"  P2 tripod: checked={results['p2']['checked']}, deactivated={results['p2']['deactivated']}")
    print(f"  P3: logged products without image_hash (CANNOT FIX)")
    print(f"  P4: URL fixed={results['p3_p4']['fixed']}, deactivated={results['p3_p4']['deactivated']}")

    # Final quality stats
    print(f"\n{'='*60}")
    print("FINAL QUALITY STATS")
    print(f"{'='*60}")
    for cat_q in ['bluetooth_speaker', 'smartwatch', 'tripod']:
        for plat_q in ['amazon_br', 'amazon_us', 'ml']:
            r = query(
                "SELECT COUNT(*) AS cnt, COUNT(*) FILTER (WHERE price IS NULL) AS null_price, COUNT(*) FILTER (WHERE price = 0) AS zero_price, COUNT(*) FILTER (WHERE price > 0) AS has_price FROM products WHERE category = %s AND platform = %s AND is_active = true",
                (cat_q, plat_q)
            )
            rr = r[0]
            print(f"  {plat_q:12} {cat_q:20}: total={rr['cnt']:3}, null_price={rr['null_price']:3}, zero_price={rr['zero_price']:3}, has_price={rr['has_price']:3}")

    rows_all = query(
        "SELECT COUNT(*) AS total, COUNT(*) FILTER (WHERE price IS NULL) AS null_p, COUNT(*) FILTER (WHERE price = 0) AS zero_p, COUNT(*) FILTER (WHERE is_active = false) AS inact, COUNT(*) FILTER (WHERE image_hash IS NULL OR image_hash = '') AS no_hash, COUNT(*) FILTER (WHERE url IS NULL OR url = '') AS no_url FROM products"
    )
    rr = rows_all[0]
    print(f"\n  GLOBAL: total={rr['total']}, null_price={rr['null_p']}, zero_price={rr['zero_p']}, inactive={rr['inact']}, no_hash={rr['no_hash']}, no_url={rr['no_url']}")

    return results


if __name__ == '__main__':
    main()
