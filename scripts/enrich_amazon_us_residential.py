#!/usr/bin/env python3
"""
Enrich Amazon US sales_30d using Decodo Residential US proxy.

Pattern (Amazon US):
  "<p id='pqv-bought-in-last-month'>5K+ bought in past month</p>"
  "<p id='pqv-bought-in-last-month'>300+ bought in past week</p>"

Proxies (rotate 10001-10005):
  http://user-span5nxws5-continent-na:N_cCzf3txm12cn5HNj@gate.decodo.com:10001

Usage:
  .venv/bin/python3 scripts/enrich_amazon_us_residential.py --limit 90 --delay 8
"""
import argparse
import json
import os
import re
import sys
import time
import random
import urllib.parse
from datetime import datetime
from decimal import Decimal

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Add parent dir for DB
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import psycopg2
from psycopg2.extras import RealDictCursor

# Decodo US Residential proxy pool
PROXY_PORTS = [10001, 10002, 10003, 10004, 10005]
PROXY_USER = "user-span5nxws5-continent-na"
PROXY_PASS = "N_cCzf3txm12cn5HNj"
PROXY_HOST = "gate.decodo.com"

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "Cache-Control": "max-age=0",
}


def get_proxy():
    """Get random proxy from pool."""
    port = random.choice(PROXY_PORTS)
    return {
        "http": f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{port}",
        "https": f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{port}",
    }


def parse_sales_from_html(html):
    """Parse 'X bought in past Y' from Amazon US page.

    Patterns:
      5K+ bought in past month  → 5000
      300+ bought in past week  → 1200 (×4)
      1K bought in past month   → 1000
    """
    # Find the social proofing element
    m = re.search(
        r'<p[^>]*id=["\']pqv-bought-in-last-month["\'][^>]*>([^<]+)</p>',
        html,
        re.IGNORECASE,
    )
    if not m:
        return None
    text = m.group(1).strip()

    # Parse: "5K+ bought in past month" or "300+ bought in past week"
    m2 = re.match(
        r"([\d.]+)\s*([KkMmBb]?)\s*\+?\s+bought\s+in\s+past\s+(month|week|day)",
        text,
        re.IGNORECASE,
    )
    if not m2:
        return None

    num_str, suffix, period = m2.groups()
    num = float(num_str)

    # Multipliers
    mult = {"": 1, "K": 1_000, "k": 1_000, "M": 1_000_000, "m": 1_000_000,
            "B": 1_000_000_000, "b": 1_000_000_000}.get(suffix, 1)
    value = int(num * mult)

    # Normalize to monthly
    if period.lower() == "week":
        value = int(value * 4.3)  # weeks per month
    elif period.lower() == "day":
        value = int(value * 30)

    return value


def fetch_asin(asin, retries=3):
    """Fetch Amazon US /dp/ page via rotating residential proxies."""
    url = f"https://www.amazon.com/dp/{asin}"
    for attempt in range(retries):
        proxy = get_proxy()
        proxy_str = proxy["https"].split("@")[-1]
        try:
            r = requests.get(
                url,
                proxies=proxy,
                headers=HEADERS,
                timeout=30,
                verify=False,
            )
            if r.status_code == 200:
                sales = parse_sales_from_html(r.text)
                if sales is None:
                    print(f"     [debug {proxy_str}] got 200 but no pattern (size={len(r.text)})", file=sys.stderr)
                    # Save for inspection
                    with open("/tmp/_last_fetch.html", "w") as f:
                        f.write(r.text)
                    # Check for captcha
                    if "Robot Check" in r.text or "automated" in r.text.lower()[:5000]:
                        print(f"     [debug] CAPTCHA/bot detected", file=sys.stderr)
                    # Check if pqv is even in page
                    if "pqv-bought" in r.text:
                        # Look for variation
                        import re as _re
                        for _m in _re.finditer(r'pqv-bought[^<]{0,200}', r.text[:500000]):
                            print(f"     [debug pqv] {_m.group(0)[:200]}", file=sys.stderr)
                            break
                return sales, None
            elif r.status_code == 503:
                print(f"     [debug {proxy_str}] 503 rate-limit", file=sys.stderr)
                time.sleep(3 + attempt * 3)
                continue
            elif r.status_code == 404:
                return None, "404_not_found"
            else:
                print(f"     [debug {proxy_str}] HTTP {r.status_code}", file=sys.stderr)
                time.sleep(2)
                continue
        except Exception as e:
            print(f"     [debug {proxy_str}] exception: {e}", file=sys.stderr)
            time.sleep(2 + attempt * 2)
            continue
    return None, "max_retries"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--delay", type=float, default=8.0,
                   help="Delay between requests (seconds)")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    # Connect to DB
    # Use PGPASSFILE for auth
    conn = psycopg2.connect(
        host="localhost", dbname="arbtbr", user="hermes1688",
    )
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Get products needing enrichment
    cur.execute("""
        SELECT id, platform_id, title
        FROM products
        WHERE is_active = true
          AND platform = 'amazon_us'
          AND sales_30d IS NULL
        ORDER BY id
        LIMIT %s
    """, (args.limit,))
    products = cur.fetchall()
    print(f"Found {len(products)} products to enrich", file=sys.stderr)

    success = 0
    no_proof = 0
    failed = 0

    for i, prod in enumerate(products, 1):
        asin = prod["platform_id"]
        print(f"[{i}/{len(products)}] {asin}: {prod['title'][:50]}", file=sys.stderr)
        sales, err = fetch_asin(asin)
        if sales is not None:
            print(f"   ✅ sales_30d={sales}", file=sys.stderr)
            success += 1
            if not args.dry_run:
                cur.execute(
                    "UPDATE products SET sales_30d = %s, sales_30d_text = %s, last_updated = NOW() WHERE id = %s",
                    (sales, f"~{sales}/month", prod["id"]),
                )
                conn.commit()
        elif err == "404_not_found":
            print(f"   ⏭️  404 (skipping)", file=sys.stderr)
            failed += 1
        else:
            print(f"   ❌ {err}", file=sys.stderr)
            no_proof += 1

        # Rate limit
        if i < len(products):
            time.sleep(args.delay)

    cur.close()
    conn.close()

    print(f"\n=== SUMMARY ===", file=sys.stderr)
    print(f"Success: {success}", file=sys.stderr)
    print(f"No proof: {no_proof}", file=sys.stderr)
    print(f"Failed (404): {failed}", file=sys.stderr)


if __name__ == "__main__":
    main()
