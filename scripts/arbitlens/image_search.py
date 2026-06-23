#!/usr/bin/env python3
"""
arbitlens Image Search V2 — Rakumart BR image search pipeline.

Runs the full 3-step Rakumart image search. If the cross API is blocked
(anti-bot), falls back to text search on Rakumart BR.

Usage:
  python3 image_search.py /path/to/image.jpg
  python3 image_search.py https://example.com/product.jpg
"""
import base64
import hashlib
import hmac
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scrape_rakumart_br import search_rakumart_br


def _product_dict(p):
    """Convert ArbitlensProduct to flat dict."""
    return {
        'platform': getattr(p, 'source_platform', 'rakumart-1688'),
        'product_name': (getattr(p, 'product_name', '') or '')[:120],
        'price_low': getattr(p, 'price_low', None),
        'price_high': getattr(p, 'price_high', None),
        'price_currency': getattr(p, 'price_currency', 'BRL'),
        'price_brl': round((getattr(p, 'price_low', 0) or 0), 2) if getattr(p, 'price_low', None) else None,
        'image_url': getattr(p, 'image_url', ''),
        'product_url': getattr(p, 'source_url', ''),
        'seller_name': getattr(p, 'seller_name', '') or '',
        'monthly_sales': getattr(p, 'monthly_sales', None),
    }


TOKEN_URL = 'https://lavel.rakumart.com.br/api/client/getUploadToken'
CROSS_URL = 'https://api-landingpage.rakumart.cn/api/cross'
OSS_ENDPOINT = 'rakumartbr.oss-us-east-1.aliyuncs.com'


def get_upload_token(timeout=60):
    """Step 1: Get STS credentials from Rakumart BR."""
    req = urllib.request.Request(
        TOKEN_URL, data=b'{}',
        headers={'Content-Type': 'application/json', 'Origin': 'https://www.rakumart.com.br'}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read())
    if not data.get('success'):
        raise Exception(f"Token failed: {data.get('msg', 'unknown')}")
    return data['data']


def _sign_oss(method, path, headers, ak_id, ak_secret, token):
    """Sign OSS request with STS credentials."""
    cm = headers.get('Content-MD5', '')
    ct = headers.get('Content-Type', '')
    dt = headers.get('Date', '')
    coh = f'x-oss-security-token:{token}\n' if token else ''
    cr = f'/rakumartbr{path}'
    s = f'{method}\n{cm}\n{ct}\n{dt}\n{coh}{cr}'
    sig = base64.b64encode(hmac.new(ak_secret.encode(), s.encode(), hashlib.sha1).digest()).decode()
    return sig


def upload_to_oss(image_data, ak_id, ak_secret, token, timeout=60):
    """Step 2: Upload image to Alibaba OSS."""
    if image_data[:4] == b'\x89PNG':
        ct, ext = 'image/png', '.png'
    elif image_data[:2] == b'\xff\xd8':
        ct, ext = 'image/jpeg', '.jpg'
    elif image_data[:4] == b'RIFF':
        ct, ext = 'image/webp', '.webp'
    else:
        ct, ext = 'image/jpeg', '.jpg'

    now = datetime.utcnow()
    ts = str(int(time.time() * 1000))
    ospath = f'/dest/{now.year}/{now.strftime("%m")}/{ts}{ext}'
    date_str = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

    headers = {'Content-Type': ct, 'Date': date_str, 'x-oss-security-token': token}
    sig = _sign_oss('PUT', ospath, headers, ak_id, ak_secret, token)
    headers['Authorization'] = f'OSS {ak_id}:{sig}'
    headers['Content-Length'] = str(len(image_data))

    url = f'https://{OSS_ENDPOINT}{ospath}'
    req = urllib.request.Request(url, data=image_data, headers=headers, method='PUT')
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if resp.status != 200:
            raise Exception(f"OSS upload failed: HTTP {resp.status}")
    return url


def cross_search(image_data, timeout=60):
    """Search by image via cross API. Sends base64-encoded image."""
    import base64 as _b64
    b64_data = _b64.b64encode(image_data).decode('ascii')
    payload = urllib.parse.urlencode({
        'uploadImageParam': json.dumps({'imageBase64': b64_data}, ensure_ascii=False)
    }).encode()
    req = urllib.request.Request(
        CROSS_URL, data=payload,
        headers={
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://www.rakumart.com.br',
            'Referer': 'https://www.rakumart.com.br/',
        }
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def image_search(image_path_or_url, timeout=60):
    """Full image search pipeline with fallback to text search."""
    is_url = image_path_or_url.startswith(('http://', 'https://'))

    if is_url:
        req = urllib.request.Request(image_path_or_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            image_data = resp.read()
    else:
        with open(image_path_or_url, 'rb') as f:
            image_data = f.read()

    # Steps 1-3: Rakumart image search pipeline
    products = []
    search_type = 'text_fallback'
    oss_url = None
    image_result_id = None

    try:
        print(f"  Searching by image (base64)...", file=sys.stderr)
        cross = cross_search(image_data, timeout)

        if cross.get('success') and cross.get('data'):
            result_id = cross['data'].get('result') if isinstance(cross['data'], dict) else None
            if result_id:
                image_result_id = str(result_id)
                # Try to get products using result ID as search
                try:
                    rakumart_products = search_rakumart_br(image_result_id, source='1688')
                    if rakumart_products:
                        products = [_product_dict(p) for p in rakumart_products[:30]]
                        search_type = 'rakumart_image'
                        print(f"  Found {len(products)} products via image search", file=sys.stderr)
                except Exception as e:
                    print(f"  Image result fetch error: {e}", file=sys.stderr)

    except Exception as e:
        print(f"  Image pipeline error: {e}", file=sys.stderr)

    # Fallback: None — image search unavailable server-side
    # We don't guess what product this is. User should use text search instead.
    if not products:
        print(f"  Image search unavailable from this server (cross API blocked).", file=sys.stderr)
        print(f"  Use text search for this category instead.", file=sys.stderr)
        search_type = 'unavailable'

    return {
        'query_image': image_path_or_url,
        'products': products,
        'total_products': len(products),
        'search_type': search_type,
        'oss_url': oss_url,
        'image_result_id': image_result_id,
    }


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 image_search.py <image_path_or_url>")
        sys.exit(1)

    img = sys.argv[1]
    t = int(sys.argv[2]) if len(sys.argv) > 2 else 120

    start = time.time()
    result = image_search(img, t)
    elapsed = int((time.time() - start) * 1000)

    out = {
        'query_image': result['query_image'],
        'products': result['products'],
        'total_products': result['total_products'],
        'search_type': result['search_type'],
        'search_time_ms': elapsed,
    }

    print(json.dumps(out, ensure_ascii=False, indent=2))