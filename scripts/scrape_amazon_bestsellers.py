#!/usr/bin/env python3
"""
Amazon Best Sellers Scraper — requests + BeautifulSoup (no browser).

Scrapes best sellers pages from amazon.com.br and amazon.com.
Extracts ASINs, titles, prices, images, reviews, BSR rank.
Calculates image_hash for matching engine.
Upserts into arbtbr.products table.

Usage:
    python3 scripts/scrape_amazon_bestsellers.py                  # both platforms
    python3 scripts/scrape_amazon_bestsellers.py --platform amazon_br
    python3 scripts/scrape_amazon_bestsellers.py --platform amazon_us
    python3 scripts/scrape_amazon_bestsellers.py --category microphones
    python3 scripts/scrape_amazon_bestsellers.py --dry-run        # no DB writes
    python3 scripts/scrape_amazon_bestsellers.py --use-su         # Decodo Site Unblocker fallback
    python3 scripts/scrape_amazon_bestsellers.py --delay 5 --max-requests 10  # gentle mode

Proxies (auto-loaded from config/decodo_*.key):
    - Residential BR (span5nxws5) — primary for amazon_br
    - US Residential (span5nxws5) — primary for amazon_us
    - Decodo Site Unblocker (U0000434457) — fallback for 503/429 blocks (opt-in: --use-su)
"""

import argparse
import hashlib
import json
import logging
import os
import re
import sys
import time
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urljoin

import ssl
import urllib.request as _ulib_request
import requests
from bs4 import BeautifulSoup

# Disable SSL verification globally for Decodo SU (uses self-signed cert)
ssl._create_default_https_context = ssl._create_unverified_context

# ── Logging ──────────────────────────────────────────────────────
LOG_DIR = Path("/mnt/ssd/arbitlens/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "amazon_bestsellers.log"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("amazon_bestsellers")

# ── Paths ────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
CATEGORY_FILE = SCRIPT_DIR / "category_ids.json"
IMAGE_DIR = Path("/mnt/ssd/arbitlens/data/images")
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

# ── Decodo Keys (gitignored) ──────────────────────────────────────
CONFIG_DIR = Path("/mnt/ssd/arbitlens/config")
DECODO_SU_KEY = CONFIG_DIR / "decodo_su.key"  # Site Unblocker U0000434457
DECODO_BR_KEY = CONFIG_DIR / "decodo_br.key"  # Residential BR
DECODO_US_KEY = CONFIG_DIR / "decodo_us.key"  # US Residential

# ── HTTP Config ──────────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

REQUEST_DELAY = 2.0  # seconds between requests to avoid rate limiting
MAX_RETRIES = 3
RETRY_DELAY = 5.0


# ── Helpers ──────────────────────────────────────────────────────

def load_categories() -> dict:
    """Load category_ids.json."""
    with open(CATEGORY_FILE) as f:
        return json.load(f)


# Track request count for rate limiting
_request_count = 0
_request_count_per_minute = []
MAX_REQUESTS_PER_MINUTE = 10  # gentle by default; override via --max-requests

def _wait_for_rate_limit():
    """Block until we are under MAX_REQUESTS_PER_MINUTE per minute."""
    global _request_count, _request_count_per_minute
    now = time.time()
    # Prune entries older than 60s
    _request_count_per_minute = [t for t in _request_count_per_minute if now - t < 60]
    if len(_request_count_per_minute) >= MAX_REQUESTS_PER_MINUTE:
        wait = 60 - (now - _request_count_per_minute[0]) + 0.5
        if wait > 0:
            log.info(f"Rate limit: sleeping {wait:.1f}s ({len(_request_count_per_minute)} requests in last 60s)")
            time.sleep(wait)
    _request_count_per_minute.append(time.time())
    _request_count += 1


def http_get(url: str, retries: int = MAX_RETRIES, use_su: bool = False) -> requests.Response | None:
    """GET with retries, delay, rate limit, and optional SU fallback.

    Args:
        url: Target URL
        retries: Max attempts
        use_su: If True, fall back to Decodo Site Unblocker on 503/429/block
    """
    for attempt in range(retries):
        try:
            _wait_for_rate_limit()
            time.sleep(REQUEST_DELAY)
            resp = requests.get(url, headers=HEADERS, timeout=30)
            if resp.status_code == 200:
                return resp
            if resp.status_code == 503:
                log.warning(f"503 on {url} (attempt {attempt+1}/{retries})")
                if use_su and attempt == retries - 1:  # last attempt, try SU
                    log.info(f"Falling back to Decodo Site Unblocker for {url}")
                    su_resp = http_get_su(url)
                    if su_resp:
                        return su_resp
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            if resp.status_code in (429, 403):  # rate limited or blocked
                log.warning(f"HTTP {resp.status_code} on {url} (attempt {attempt+1}/{retries})")
                if use_su:
                    log.info(f"Falling back to Decodo Site Unblocker for {url}")
                    su_resp = http_get_su(url)
                    if su_resp:
                        return su_resp
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            if resp.status_code == 404:
                return None  # don't retry 404
            log.warning(f"HTTP {resp.status_code} on {url} (attempt {attempt+1}/{retries})")
        except requests.RequestException as e:
            log.warning(f"Request error on {url} (attempt {attempt+1}/{retries}): {e}")
            time.sleep(RETRY_DELAY * (attempt + 1))
    log.error(f"Failed after {retries} attempts: {url}")
    return None


def http_get_su(url: str, timeout: int = 60) -> requests.Response | None:
    """Fetch URL via Decodo Site Unblocker (forward proxy on port 60000).

    Bypasses Amazon bot detection by:
    - Using a residential IP
    - Changing browser fingerprint via X-SU headers
    - Server-side JS rendering (X-SU-Headless: html)

    Returns a requests.Response-like object with .text, .status_code, .content.
    """
    if not DECODO_SU_KEY.exists():
        log.error(f"SU key not found: {DECODO_SU_KEY}")
        return None
    auth = DECODO_SU_KEY.read_text().strip()
    proxy = f"https://{auth}@unblock.decodo.com:60000"

    proxy_handler = _ulib_request.ProxyHandler({
        "http": proxy,
        "https": proxy,
    })
    opener = _ulib_request.build_opener(proxy_handler)

    req = _ulib_request.Request(url)
    # Copy our normal headers
    for k, v in HEADERS.items():
        req.add_header(k, v)
    # Add SU-specific headers for browser fingerprint + JS rendering
    req.add_header("X-SU-Locale", "pt-br" if "amazon.com.br" in url else "en-us")
    req.add_header("X-SU-Device-Type", "desktop")
    req.add_header("X-SU-Headless", "html")

    try:
        _wait_for_rate_limit()  # also rate limit SU calls
        with opener.open(req, timeout=timeout) as resp:
            body = resp.read()
            # Wrap in a requests.Response-like object
            r = requests.Response()
            r.status_code = resp.status
            r._content = body
            r.url = url
            r.headers = dict(resp.headers.items())
            r.encoding = "utf-8"
            return r
    except Exception as e:
        log.error(f"SU request failed for {url}: {e}")
        return None


def parse_price_br(text: str) -> Decimal | None:
    """Parse Brazilian price: 'R$ 1.234,56' or '1234,56' → Decimal."""
    if not text:
        return None
    # Remove currency symbols and whitespace
    clean = re.sub(r'[R$\s]', '', text.strip())
    # Handle thousands separator: 1.234,56 → 1234.56
    if ',' in clean and '.' in clean:
        clean = clean.replace('.', '').replace(',', '.')
    elif ',' in clean:
        clean = clean.replace(',', '.')
    try:
        val = Decimal(clean)
        return val if val > 0 else None
    except (InvalidOperation, ValueError):
        return None


def parse_price_us(text: str) -> Decimal | None:
    """Parse US price: '$1,234.56' or '1234.56' → Decimal."""
    if not text:
        return None
    clean = re.sub(r'[$\s]', '', text.strip())
    # Remove thousands separator
    if ',' in clean and '.' in clean:
        clean = clean.replace(',', '')
    elif ',' in clean and clean.count(',') == 1 and len(clean.split(',')[1]) == 2:
        clean = clean.replace(',', '.')
    else:
        clean = clean.replace(',', '')
    try:
        val = Decimal(clean)
        return val if val > 0 else None
    except (InvalidOperation, ValueError):
        return None


def compute_image_hash(image_url: str) -> str | None:
    """Download image and compute SHA-256 hash of content."""
    if not image_url:
        return None
    try:
        resp = requests.get(image_url, timeout=15, headers={
            "User-Agent": HEADERS["User-Agent"]
        })
        if resp.status_code == 200 and len(resp.content) > 100:
            return hashlib.sha256(resp.content).hexdigest()
    except Exception as e:
        log.warning(f"Image hash failed for {image_url}: {e}")
    return None


def download_image(image_url: str, platform: str, platform_id: str) -> str | None:
    """Download product image to local storage. Returns relative path."""
    if not image_url:
        return None
    subdir = IMAGE_DIR / platform
    subdir.mkdir(parents=True, exist_ok=True)
    local_path = subdir / f"{platform_id}.jpg"

    # Skip if already downloaded and valid
    if local_path.exists() and local_path.stat().st_size > 1000:
        return f"{platform}/{platform_id}.jpg"

    try:
        resp = requests.get(image_url, timeout=15, headers={
            "User-Agent": HEADERS["User-Agent"]
        })
        if resp.status_code == 200 and len(resp.content) > 100:
            local_path.write_bytes(resp.content)
            log.info(f"Downloaded image: {platform}/{platform_id}.jpg ({len(resp.content)} bytes)")
            return f"{platform}/{platform_id}.jpg"
    except Exception as e:
        log.warning(f"Image download failed for {platform_id}: {e}")
    return None


def clean_text(text: str) -> str:
    """Strip and normalize whitespace."""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text.strip())


# ── Amazon BR Parser ─────────────────────────────────────────────

def parse_best_sellers_br(html: str, category_name: str) -> list[dict]:
    """Parse Amazon BR best sellers page HTML into product dicts."""
    soup = BeautifulSoup(html, "html.parser")
    products = []

    # Best sellers grid: each item is in a div with data-asin
    # Main container: zg-grid-general-faceout or similar
    items = soup.select('[data-asin]')
    if not items:
        # Fallback: try product cards
        items = soup.select('.zg-grid-general-faceout, .a-carousel-card, .p13n-sc-uncoverable-faceout')

    log.info(f"Found {len(items)} candidate items in BR best sellers HTML")

    for item in items:
        asin = item.get("data-asin", "").strip()
        if not asin or len(asin) < 10:
            continue

        # Title
        title_el = item.select_one(
            '.p13n-sc-truncate-desktop-type2, '
            '.a-link-normal .a-size-small, '
            '._cDEzb_p13n-sc-css-line-clamp-3_g3dy1, '
            '.a-link-normal span div, '
            'a.a-link-normal span'
        )
        title = clean_text(title_el.get_text()) if title_el else ""

        # Also try getting title from link title attribute
        if not title:
            link = item.select_one('a[href*="/dp/"]')
            if link:
                title = clean_text(link.get("title", ""))

        if not title:
            continue

        # Price
        price_el = item.select_one(
            '.p13n-sc-price, ._cDEzb_p13n-sc-price_3mJ9Z, '
            '.a-price .a-offscreen, .a-color-price'
        )
        price_text = clean_text(price_el.get_text()) if price_el else ""
        price = parse_price_br(price_text)

        # Image
        img_el = item.select_one('img[src*="images-amazon"], img[src*="media-amazon"]')
        image_url = ""
        if img_el:
            image_url = img_el.get("src", "")
            # Prefer higher-res if available
            srcset = img_el.get("srcset", "")
            if srcset:
                # Get the largest image from srcset
                sources = srcset.split(",")
                for source in reversed(sources):
                    parts = source.strip().split()
                    if parts and ("images-amazon" in parts[0] or "media-amazon" in parts[0]):
                        image_url = parts[0]
                        break

        # Rating
        rating_el = item.select_one('.a-icon-alt, [aria-label*="estrela"]')
        rating_text = clean_text(rating_el.get_text()) if rating_el else ""
        rating_match = re.search(r'(\d[.,]\d)', rating_text)
        review_avg = None
        if rating_match:
            try:
                review_avg = Decimal(rating_match.group(1).replace(',', '.'))
            except (InvalidOperation, ValueError):
                pass

        # Review count
        review_el = item.select_one('.a-size-small a[href*="customerReviews"]')
        review_count = 0
        if review_el:
            rev_text = clean_text(review_el.get_text()).replace('.', '').replace(',', '')
            rev_match = re.search(r'(\d+)', rev_text)
            if rev_match:
                review_count = int(rev_match.group(1))

        # BSR rank
        bsr_el = item.select_one('.zg-bdg-text')
        bsr_rank = None
        if bsr_el:
            bsr_text = clean_text(bsr_el.get_text()).replace('#', '').replace('.', '').replace(',', '')
            bsr_match = re.search(r'(\d+)', bsr_text)
            if bsr_match:
                bsr_rank = int(bsr_match.group(1))

        product = {
            "platform": "amazon_br",
            "platform_id": asin,
            "title": title,
            "price": price,
            "currency": "BRL",
            "url": f"https://www.amazon.com.br/dp/{asin}",
            "image_url": image_url,
            "review_avg": review_avg,
            "review_count": review_count,
            "bsr_rank": bsr_rank,
            "category": category_name,
        }
        products.append(product)

    return products


def parse_product_page_br(html: str, product: dict) -> dict:
    """Enrich product data from individual Amazon BR product page."""
    soup = BeautifulSoup(html, "html.parser")

    # Price (more reliable from product page)
    price_el = soup.select_one(
        '#priceblock_ourprice, #priceblock_dealprice, '
        '.a-price .a-offscreen, #corePrice_feature_div .a-offscreen, '
        '#price_inside_buybox, .priceToPay .a-offscreen'
    )
    if price_el:
        price = parse_price_br(clean_text(price_el.get_text()))
        if price:
            product["price"] = price

    # Monthly sales (Amazon BR: "X vendidos nos últimos 30 dias" or "X bought in past month")
    sales_el = soup.select_one(
        '#social-proofing-faceout-title-tk_bought span, '
        '[data-feature-name="socialProofing"] span, '
        '.social-proofing-faceout-title-tk_bought'
    )
    if sales_el:
        sales_text = clean_text(sales_el.get_text())
        # "mais de 100 compraram no último mês" or "+100 bought in past month"
        sales_match = re.search(r'([\d.]+)\+?\s*(?:compraram|bought|vendidos)', sales_text, re.IGNORECASE)
        if sales_match:
            product["sales_30d"] = int(sales_match.group(1).replace('.', ''))

    # Review count from product page (more accurate)
    review_count_el = soup.select_one('#acrCustomerReviewText, #reviewsMedley .a-size-base')
    if review_count_el:
        rev_text = clean_text(review_count_el.get_text()).replace('.', '').replace(',', '')
        rev_match = re.search(r'(\d+)', rev_text)
        if rev_match:
            product["review_count"] = int(rev_match.group(1))

    # Rating from product page
    rating_el = soup.select_one('#acrPopover .a-icon-alt, [data-hook="rating-out-of-text"]')
    if rating_el:
        rating_text = clean_text(rating_el.get_text())
        rating_match = re.search(r'(\d[.,]\d)', rating_text)
        if rating_match:
            try:
                product["review_avg"] = Decimal(rating_match.group(1).replace(',', '.'))
            except (InvalidOperation, ValueError):
                pass

    # Better image from product page
    img_el = soup.select_one('#landingImage, #imgBlkFront, #main-image')
    if img_el:
        src = img_el.get("data-old-hires", "") or img_el.get("src", "")
        if src and "images-amazon" in src:
            product["image_url"] = src

    return product


# ── Amazon US Parser ─────────────────────────────────────────────

def parse_best_sellers_us(html: str, category_name: str) -> list[dict]:
    """Parse Amazon US best sellers page HTML into product dicts."""
    soup = BeautifulSoup(html, "html.parser")
    products = []

    items = soup.select('[data-asin]')
    if not items:
        items = soup.select('.zg-grid-general-faceout, .a-carousel-card, .p13n-sc-uncoverable-faceout')

    log.info(f"Found {len(items)} candidate items in US best sellers HTML")

    for item in items:
        asin = item.get("data-asin", "").strip()
        if not asin or len(asin) < 10:
            continue

        # Title
        title_el = item.select_one(
            '.p13n-sc-truncate-desktop-type2, '
            '._cDEzb_p13n-sc-css-line-clamp-3_g3dy1, '
            '.a-link-normal span div, '
            'a.a-link-normal span'
        )
        title = clean_text(title_el.get_text()) if title_el else ""

        if not title:
            link = item.select_one('a[href*="/dp/"]')
            if link:
                title = clean_text(link.get("title", ""))

        if not title:
            continue

        # Price
        price_el = item.select_one(
            '.p13n-sc-price, ._cDEzb_p13n-sc-price_3mJ9Z, '
            '.a-price .a-offscreen, .a-color-price'
        )
        price_text = clean_text(price_el.get_text()) if price_el else ""
        price = parse_price_us(price_text)

        # Image
        img_el = item.select_one('img[src*="images-amazon"], img[src*="media-amazon"]')
        image_url = ""
        if img_el:
            image_url = img_el.get("src", "")
            srcset = img_el.get("srcset", "")
            if srcset:
                sources = srcset.split(",")
                for source in reversed(sources):
                    parts = source.strip().split()
                    if parts and ("images-amazon" in parts[0] or "media-amazon" in parts[0]):
                        image_url = parts[0]
                        break

        # Rating
        rating_el = item.select_one('.a-icon-alt')
        rating_text = clean_text(rating_el.get_text()) if rating_el else ""
        rating_match = re.search(r'(\d\.\d)', rating_text)
        review_avg = None
        if rating_match:
            try:
                review_avg = Decimal(rating_match.group(1))
            except (InvalidOperation, ValueError):
                pass

        # Review count
        review_el = item.select_one('.a-size-small a[href*="customerReviews"]')
        review_count = 0
        if review_el:
            rev_text = clean_text(review_el.get_text()).replace(',', '')
            rev_match = re.search(r'(\d+)', rev_text)
            if rev_match:
                review_count = int(rev_match.group(1))

        # BSR rank
        bsr_el = item.select_one('.zg-bdg-text')
        bsr_rank = None
        if bsr_el:
            bsr_text = clean_text(bsr_el.get_text()).replace('#', '').replace(',', '')
            bsr_match = re.search(r'(\d+)', bsr_text)
            if bsr_match:
                bsr_rank = int(bsr_match.group(1))

        product = {
            "platform": "amazon_us",
            "platform_id": asin,
            "title": title,
            "price": price,
            "currency": "USD",
            "url": f"https://www.amazon.com/dp/{asin}",
            "image_url": image_url,
            "review_avg": review_avg,
            "review_count": review_count,
            "bsr_rank": bsr_rank,
            "category": category_name,
        }
        products.append(product)

    return products


def parse_product_page_us(html: str, product: dict) -> dict:
    """Enrich product data from individual Amazon US product page."""
    soup = BeautifulSoup(html, "html.parser")

    # Price
    price_el = soup.select_one(
        '#priceblock_ourprice, #priceblock_dealprice, '
        '.a-price .a-offscreen, #corePrice_feature_div .a-offscreen, '
        '#price_inside_buybox, .priceToPay .a-offscreen'
    )
    if price_el:
        price = parse_price_us(clean_text(price_el.get_text()))
        if price:
            product["price"] = price

    # Monthly sales
    sales_el = soup.select_one(
        '#social-proofing-faceout-title-tk_bought span, '
        '[data-feature-name="socialProofing"] span'
    )
    if sales_el:
        sales_text = clean_text(sales_el.get_text())
        sales_match = re.search(r'([\d,]+)\+?\s*(?:bought|sold)', sales_text, re.IGNORECASE)
        if sales_match:
            product["sales_30d"] = int(sales_match.group(1).replace(',', ''))

    # Review count
    review_count_el = soup.select_one('#acrCustomerReviewText')
    if review_count_el:
        rev_text = clean_text(review_count_el.get_text()).replace(',', '')
        rev_match = re.search(r'(\d+)', rev_text)
        if rev_match:
            product["review_count"] = int(rev_match.group(1))

    # Rating
    rating_el = soup.select_one('#acrPopover .a-icon-alt')
    if rating_el:
        rating_text = clean_text(rating_el.get_text())
        rating_match = re.search(r'(\d\.\d)', rating_text)
        if rating_match:
            try:
                product["review_avg"] = Decimal(rating_match.group(1))
            except (InvalidOperation, ValueError):
                pass

    # Better image
    img_el = soup.select_one('#landingImage, #imgBlkFront')
    if img_el:
        src = img_el.get("data-old-hires", "") or img_el.get("src", "")
        if src and "images-amazon" in src:
            product["image_url"] = src

    return product


# ── Database ─────────────────────────────────────────────────────

def upsert_product(product: dict, dry_run: bool = False) -> bool:
    """Insert or update product in arbtbr.products. Returns True if written."""
    sys.path.insert(0, str(SCRIPT_DIR))
    from db import get_conn

    # Compute image hash and download local copy
    image_hash = compute_image_hash(product.get("image_url", ""))
    local_image = download_image(
        product.get("image_url", ""),
        product["platform"],
        product["platform_id"]
    )

    if dry_run:
        log.info(f"[DRY RUN] Would upsert: {product['platform_id']} - {product['title'][:60]}...")
        log.info(f"  Price: {product.get('price')} {product.get('currency')}, BSR: {product.get('bsr_rank')}, "
                 f"Image hash: {image_hash[:12] if image_hash else 'None'}...")
        return True

    try:
        with get_conn() as conn:
            cur = conn.cursor()

            # Check if product exists
            cur.execute(
                "SELECT id FROM products WHERE platform = %s AND platform_id = %s",
                (product["platform"], product["platform_id"])
            )
            existing = cur.fetchone()

            if existing:
                # Update existing product
                cur.execute("""
                    UPDATE products SET
                        title = COALESCE(%s, title),
                        price = COALESCE(%s, price),
                        currency = COALESCE(%s, currency),
                        url = COALESCE(%s, url),
                        image_urls = CASE WHEN %s IS NOT NULL THEN ARRAY[%s]::text[] ELSE image_urls END,
                        image_hash = COALESCE(%s, image_hash),
                        review_count = COALESCE(%s, review_count),
                        review_avg = COALESCE(%s, review_avg),
                        bsr_rank = COALESCE(%s, bsr_rank),
                        sales_30d = COALESCE(%s, sales_30d),
                        category = COALESCE(%s, category),
                        last_updated = NOW()
                    WHERE platform = %s AND platform_id = %s
                """, (
                    product.get("title"),
                    product.get("price"),
                    product.get("currency"),
                    product.get("url"),
                    local_image, local_image,
                    image_hash,
                    product.get("review_count"),
                    product.get("review_avg"),
                    product.get("bsr_rank"),
                    product.get("sales_30d"),
                    product.get("category"),
                    product["platform"],
                    product["platform_id"],
                ))
                log.info(f"Updated: {product['platform_id']} - {product['title'][:50]}...")
            else:
                # Insert new product
                img_arr = [local_image] if local_image else None
                cur.execute("""
                    INSERT INTO products (
                        platform, platform_id, title, price, currency, url,
                        image_urls, image_hash,
                        review_count, review_avg, bsr_rank, sales_30d,
                        category, supplier_name, raw_data
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    product["platform"],
                    product["platform_id"],
                    product.get("title"),
                    product.get("price"),
                    product.get("currency", "BRL" if product["platform"] == "amazon_br" else "USD"),
                    product.get("url"),
                    img_arr,
                    image_hash,
                    product.get("review_count", 0),
                    product.get("review_avg"),
                    product.get("bsr_rank"),
                    product.get("sales_30d"),
                    product.get("category"),
                    "Amazon BR" if product["platform"] == "amazon_br" else "Amazon US",
                    json.dumps({
                        "scraped_at": datetime.now().isoformat(),
                        "source": "bestsellers_scraper",
                    }),
                ))
                log.info(f"Inserted: {product['platform_id']} - {product['title'][:50]}...")

            conn.commit()
            cur.close()
            return True
    except Exception as e:
        log.error(f"DB error for {product['platform_id']}: {e}")
        return False


# ── Main Scraping Logic ──────────────────────────────────────────

def scrape_platform(platform: str, categories: dict, category_filter: str = None,
                    dry_run: bool = False, enrich: bool = True, use_su: bool = False) -> dict:
    """Scrape best sellers for a platform. Returns stats dict."""
    platform_data = categories.get(platform, {})
    if not platform_data:
        log.error(f"No categories found for platform: {platform}")
        return {"platform": platform, "scraped": 0, "inserted": 0, "errors": 0}

    platform_dir = IMAGE_DIR / platform
    platform_dir.mkdir(parents=True, exist_ok=True)

    total_scraped = 0
    total_inserted = 0
    total_errors = 0

    for cat_name, cat_info in platform_data.items():
        if category_filter and cat_name != category_filter:
            continue

        url = cat_info.get("bestsellers_url", "")
        if not url:
            log.warning(f"No bestsellers_url for {platform}/{cat_name}")
            continue

        log.info(f"=" * 60)
        log.info(f"Scraping {platform} / {cat_name}: {url}")
        log.info(f"=" * 60)

        resp = http_get(url, use_su=use_su)
        if not resp:
            log.error(f"Failed to fetch best sellers page for {cat_name}")
            total_errors += 1
            continue

        # Parse based on platform
        if platform == "amazon_br":
            products = parse_best_sellers_br(resp.text, cat_name)
        else:
            products = parse_best_sellers_us(resp.text, cat_name)

        log.info(f"Parsed {len(products)} products from {cat_name} best sellers")

        if not products:
            # Save HTML for debugging
            debug_path = LOG_DIR / f"debug_{platform}_{cat_name}.html"
            debug_path.write_text(resp.text[:50000])
            log.warning(f"No products found. Saved HTML snippet to {debug_path}")
            total_errors += 1
            continue

        # Enrich each product with detail page data
        for i, product in enumerate(products):
            if enrich and i < 10:  # Only enrich top 10 per category (cost control)
                detail_url = product["url"]
                log.info(f"  [{i+1}/{len(products)}] Enriching {product['platform_id']}...")
                detail_resp = http_get(detail_url, use_su=use_su)
                if detail_resp:
                    if platform == "amazon_br":
                        product = parse_product_page_br(detail_resp.text, product)
                    else:
                        product = parse_product_page_us(detail_resp.text, product)

            # Upsert to DB
            ok = upsert_product(product, dry_run=dry_run)
            if ok:
                total_inserted += 1
            else:
                total_errors += 1

        total_scraped += len(products)

    return {
        "platform": platform,
        "scraped": total_scraped,
        "inserted": total_inserted,
        "errors": total_errors,
    }


def main():
    parser = argparse.ArgumentParser(description="Amazon Best Sellers Scraper")
    parser.add_argument("--platform", choices=["amazon_br", "amazon_us"], default=None,
                        help="Scrape only this platform (default: both)")
    parser.add_argument("--category", default=None,
                        help="Scrape only this category (e.g., microphones, headphones)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Parse and log but don't write to DB")
    parser.add_argument("--no-enrich", action="store_true",
                        help="Skip detail page enrichment (faster, less data)")
    parser.add_argument("--max-per-category", type=int, default=50,
                        help="Max products to process per category (default: 50)")
    parser.add_argument("--use-su", action="store_true",
                        help="Fall back to Decodo Site Unblocker on 503/429/block (opt-in)")
    parser.add_argument("--delay", type=float, default=None,
                        help="Override REQUEST_DELAY (seconds between requests)")
    parser.add_argument("--max-requests", type=int, default=None,
                        help="Override MAX_REQUESTS_PER_MINUTE (default: 10, gentle)")
    args = parser.parse_args()

    # Apply overrides
    global REQUEST_DELAY, MAX_REQUESTS_PER_MINUTE
    if args.delay is not None:
        REQUEST_DELAY = args.delay
        log.info(f"Delay override: {REQUEST_DELAY}s")
    if args.max_requests is not None:
        MAX_REQUESTS_PER_MINUTE = args.max_requests
        log.info(f"Rate limit override: {MAX_REQUESTS_PER_MINUTE} req/min")

    log.info("=" * 60)
    log.info("Amazon Best Sellers Scraper — starting")
    log.info(f"Platform: {args.platform or 'all'}")
    log.info(f"Category: {args.category or 'all'}")
    log.info(f"Dry run: {args.dry_run}")
    log.info(f"Enrich: {not args.no_enrich}")
    log.info(f"SU fallback: {'ON' if args.use_su else 'OFF'}")
    log.info(f"Delay: {REQUEST_DELAY}s | Rate limit: {MAX_REQUESTS_PER_MINUTE} req/min")
    log.info("=" * 60)

    categories = load_categories()
    platforms = [args.platform] if args.platform else ["amazon_br", "amazon_us"]
    all_stats = []

    for platform in platforms:
        stats = scrape_platform(
            platform=platform,
            categories=categories,
            category_filter=args.category,
            dry_run=args.dry_run,
            use_su=args.use_su,
            enrich=not args.no_enrich,
        )
        all_stats.append(stats)

    # Summary
    log.info("")
    log.info("=" * 60)
    log.info("SCRAPING COMPLETE")
    log.info("=" * 60)
    for stats in all_stats:
        log.info(f"  {stats['platform']}: {stats['scraped']} scraped, "
                 f"{stats['inserted']} inserted, {stats['errors']} errors")

    total_scraped = sum(s["scraped"] for s in all_stats)
    total_inserted = sum(s["inserted"] for s in all_stats)
    total_errors = sum(s["errors"] for s in all_stats)
    log.info(f"  TOTAL: {total_scraped} scraped, {total_inserted} inserted, {total_errors} errors")
    log.info("=" * 60)

    # Write summary JSON
    summary = {
        "scraped_at": datetime.now().isoformat(),
        "dry_run": args.dry_run,
        "stats": all_stats,
        "totals": {
            "scraped": total_scraped,
            "inserted": total_inserted,
            "errors": total_errors,
        },
    }
    summary_path = Path("/mnt/ssd/arbitlens/data/last_bestsellers_scrape.json")
    summary_path.write_text(json.dumps(summary, indent=2, default=str))
    log.info(f"Summary saved to {summary_path}")


if __name__ == "__main__":
    main()
