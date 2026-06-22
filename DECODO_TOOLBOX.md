# Decodo API Toolbox — Test Results

## Status Summary

| Service | Status | Endpoint | Notes |
|---------|--------|----------|-------|
| **Scraping API** (U0000420946) | ✅ Working | `https://scraper-api.decodo.com/v2/scrape` | JSON REST API, fast, returns 500KB pages |
| **Site Unblocker** (U0000434457) | ✅ Working | `https://unblock.decodo.com:60000` (forward proxy) | Bypasses ML + Amazon bot detection, needs `ssl._create_unverified_context` |
| **Residential BR** (span5nxws5) | ✅ Working | `https://br.decodo.com:10001` | Brazilian IP (Marco, CE — Voo Telecom) |
| **US Residential** (span5nxws5) | ✅ Working | `https://us.decodo.com:10001` | US IP (Chicago — Comcast) |
| **ISP Static** (sp2idylm9q) | ✅ Working | `https://isp.decodo.com:10001` | AU IP (Canberra — Lumen) |
| **Mobile** (spraglxgvk) | ❌ 407 auth fail | `https://gate.decodo.com:10001` | Wrong password or no mobile plan |
| **Firecrawl v2** (both keys) | ✅ Working | `https://api.firecrawl.dev/v2/scrape` | Use v2 endpoint, not v0/v1 |
| **Firecrawl v0/v1** | ❌ Invalid | — | Use v2 |

## Detailed Findings

### Scraping API (U0000420946) — RECOMMENDED
- **Endpoint**: `https://scraper-api.decodo.com/v2/scrape`
- **Auth**: HTTP Basic, header `Authorization: Basic <base64(user:pass)>`
- **Request body**: `{"url": "https://...", "headless": "html", "locale": "pt-br"}`
- **Response**: `{"results": [{"content": "<html>", "status_code": 200, ...}]}`
- **Use case**: ML scraping, complex JS pages
- **Tested**: ML best-sellers (MLB1246) returns 552KB, 19 products parsed

### Site Unblocker (U0000434457) — POWERFUL
- **Endpoint**: `https://unblock.decodo.com:60000` (FORWARD PROXY, not REST API)
- **Auth**: HTTP Basic via proxy URL `https://user:pass@host:port`
- **Optional headers**:
  - `X-SU-Locale`: `pt-br`, `en-us`, etc.
  - `X-SU-Device-Type`: `desktop` or `mobile`
  - `X-SU-Headless`: `html` (server renders JS)
- **Tested**: 
  - `ip.decodo.com` → 200 OK, 792 bytes, real residential IP (ASN 64286)
  - With `X-SU-Headless: html` → changes to Edge 122.0
  - ML best-sellers → 200 OK, 549KB, 19 products parsed in 12.3s
  - Amazon BR `/gp/bestsellers/beauty` → 200 OK, 670KB, 50 ASINs in 28.1s
- **Caveat**: Self-signed SSL cert — Python needs `ssl._create_unverified_context()`. curl needs `-k`.
- **Use case**: Bypass ML + Amazon bot detection, full pages with browser fingerprint

### Mobile Proxy (spraglxgvk) — FAILING
- **Endpoint**: `gate.decodo.com:10001` (also tested 10000, 8000, 9000, 10002, 60000)
- **Auth given**: `spraglxgvk:Vd6qj0tqxk4B5Qg+dT`
- **Result**: 407 Proxy Authentication Required on ALL ports/hosts
- **Possible causes**:
  - Wrong password (Decodo might have rotated it)
  - Account doesn't have mobile plan
  - Account suspended
- **Action needed**: Verify mobile plan is active in Decodo dashboard

## Working Python Code Patterns

### Scraping API (used in `scripts/scrape_ml_decodo.py`)
```python
import urllib.request, json, base64

auth = base64.b64encode(f"{user}:{pass}".encode()).decode()
req = urllib.request.Request(
    "https://scraper-api.decodo.com/v2/scrape",
    data=json.dumps({"url": url, "headless": "html", "locale": "pt-br"}).encode(),
    method='POST'
)
req.add_header('Authorization', f'Basic {auth}')
req.add_header('Content-Type', 'application/json')
with urllib.request.urlopen(req, timeout=60) as r:
    data = json.loads(r.read())
    html = data['results'][0]['content']
```

### Site Unblocker (forward proxy)
```python
import ssl, urllib.request

# Disable SSL verification (SU uses self-signed cert)
ssl._create_default_https_context = ssl._create_unverified_context

proxy = f"https://{user}:{pass}@unblock.decodo.com:60000"
h = urllib.request.ProxyHandler({'http': proxy, 'https': proxy})
o = urllib.request.build_opener(h)
r = urllib.request.Request("https://target.com/page")
r.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36')
r.add_header('X-SU-Locale', 'pt-br')
r.add_header('X-SU-Headless', 'html')
r.add_header('X-SU-Device-Type', 'desktop')
with o.open(r, timeout=60) as resp:
    html = resp.read().decode('utf-8')
```

## Key Files (gitignored)
- `config/decodo_scraping.key` — Scraping API auth (U0000420946)
- `config/decodo_su.key` — Site Unblocker auth (U0000434457)
- `config/decodo_br.key` — Residential BR (span5nxws5)
- `config/decodo_isp.key` — ISP static (sp2idylm9q)
- `config/decodo_us.key` — US residential (span5nxws5)
- `config/decodo_mobile.key` — Mobile (spraglxgvk) — not working, see above
