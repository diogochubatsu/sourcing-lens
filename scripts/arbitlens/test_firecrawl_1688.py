#!/usr/bin/env python3
"""Test Firecrawl v2 API against 1688.com"""
import base64
import urllib.request
import json

API_KEY = base64.b64decode("KioqNGUyNg==").decode()

BASE = "https://api.firecrawl.dev/v2"

def test_scrape(url, label):
    print(f"""\n{"="*60}
TEST: {label}
URL: {url}
{"="*60}""")
    
    payload = json.dumps({
        "url": url,
        "formats": ["markdown"],
        "onlyMainContent": False,
    }).encode()
    
    req = urllib.request.Request(
        f"{BASE}/scrape",
        data=payload,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"  NETWORK ERROR: {e}")
        return None
    
    success = data.get("success", False)
    print(f"  Success: {success}")
    
    if not success:
        print(f"  Error: {data.get('error', 'unknown')}")
        return None
    
    md = data.get("data", {}).get("markdown", "")
    print(f"  Markdown length: {len(md)} chars")
    
    combined = (md + json.dumps(data)).lower()
    for kw, lb in [("baxia-punish", "BAXIA CAPTCHA"), ("captcha", "CAPTCHA"), ("verification", "VERIFICATION"), ("unusual traffic", "TRAFFIC BLOCK")]:
        if kw in combined:
            print(f"  !! BLOCKED: {lb}")
    
    print(f"  Preview: {md[:600]}")
    return data

# TESTS
test_scrape(
    "https://s.1688.com/page/offer_search.htm?keywords=%E6%97%A0%E7%BA%BF%E9%A2%86%E5%A4%B9%E9%BA%A6%E5%85%8B%E9%A3%8E+K15",
    "1688 Search - wireless lapel mic K15"
)
test_scrape(
    "https://detail.1688.com/offer/740647797173.html",
    "1688 Detail page"
)
test_scrape(
    "https://sale.1688.com/factory/index.html?keywords=%E6%97%A0%E7%BA%BF%E9%A2%86%E5%A4%B9%E9%BA%A6%E5%85%8B%E9%A3%8E",
    "1688 Factory page"
)
