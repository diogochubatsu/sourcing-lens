# ArbitLens — Data Source Matrix

> All options for product data, trend intelligence, and sourcing.
> Budget: $0/month (use free tiers, open-source, and existing infrastructure)

---

## 1. PRODUCT DATA SOURCES (where to get products + prices)

| Platform | API | Scraping | Free? | Data Available | Best Approach |
|----------|-----|----------|-------|----------------|---------------|
| **1688.com** | No public API | Firecrawl (proven) | Existing infra | Title, price, images, supplier, MOQ | 1688-intel scraping API (on hold) |
| **AliExpress** | No | Crawl4AI (partial) | Yes | Title, price, images, sold count, rating | Crawl4AI + stealth |
| **Amazon BR** | PA-API (limited) | requests+BS4 (works) | Yes | Title, price, ASIN, BSR, images, reviews | requests — already working |
| **Mercado Livre** | Official API ✓ | N/A | Yes, 5K req/day | Title, price, images, sales, reviews | API — already working |
| **Shopee BR** | Seller API (open.shopee.com) | Playwright/Selenium | API free | Title, price, images, sales, reviews, stock | API (needs seller account) or scrape |
| **Made-in-China** | No | Selenium/Apify | Yes | Title, price, MOQ, supplier info | Scraping (no sales data) |
| **DHgate** | Official API (open.dhgate.com) | Scraping | API free | Title, price, images, reviews, MOQ, supplier | API — easiest Chinese B2B |
| **Alibaba.com** | Official API | Scraping | API free tier | Title, price, MOQ, supplier, volume pricing | API + scraping |
| **TikTok Shop** | Official API (partner.tiktokshop.com) | Scraping (hard) | API free | Products, orders, reviews, analytics | API (needs approval) |

### Key Insight
DHgate has the easiest API access (free registration, Python SDK). Shopee has the richest data (sales counts). TikTok Shop API is free but requires partnership approval.

---

## 2. SPY TOOLS & PRODUCT RESEARCH PLATFORMS

| Tool | $/mo | FB Ads | TT Ads | TT Shop | AliExpress | Stores | API | Free Tier |
|------|------|--------|--------|---------|------------|--------|-----|-----------|
| **Winning Hunter** | $49+ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | Trial |
| **Minea** | $49+ | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ | Trial |
| **Ecomhunt** | $0-49 | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ | **YES** (free tier) |
| **Sell The Trend** | $30+ | ✓ | ✓ | ✓(Pro) | ✓ | ✓ | ✗ | Trial |
| **PiPiAds** | $49+ | ✓ | ✓ | ✓ | ✗ | ✗ | ✓ | Trial (500 credits) |
| **Kalodata** | $46+ | ✗ | ✗ | **YES** | ✗ | ✗ | ✓ | 7-day trial |

### Key Insight
Ecomhunt has a genuine free tier. Winning Hunter has the broadest coverage + API. Kalodata is the best for TikTok Shop specifically.

---

## 3. FREE TOOLS (no cost at all)

| Tool | What It Does | URL |
|------|-------------|-----|
| **Facebook Ad Library** | Search all active FB/IG ads by keyword, country | facebook.com/ads/library |
| **TikTok Creative Center** | Trending hashtags, top ads, creative inspiration | ads.tiktok.com/business/creativecenter |
| **Google Trends** | Search interest over time, compare products | trends.google.com |
| **AliExpress Dropshipping Center** | Product analytics, trending items | aliexpress.com/dropship |
| **Mercado Livre API** | Product search, bestsellers, prices | api.mercadolibre.com (free, 5K/day) |
| **TikTok Shop API** | Products, orders, reviews, analytics | partner.tiktokshop.com (free, needs approval) |
| **DHgate API** | Product search, prices, reviews | open.dhgate.com (free registration) |
| **Alibaba API** | Product search, supplier data | open.alibaba.com (free tier) |

---

## 4. TIKTOK SHOP — DETAILED OPTIONS

### Official API (FREE)
- Register at partner.tiktokshop.com
- Endpoints: products, orders, reviews, analytics, creator data
- Requires app approval + seller authorization
- **Best for:** reliable, structured data

### Kalodata ($46+/mo, 7-day free trial)
- 100M+ product records, 200M+ creator profiles
- 500 days historical data
- Trending product discovery
- **Best for:** deep TikTok Shop analytics

### PiPiAds ($49+/mo, trial available)
- TikTok ad spy (primary focus)
- TikTok Shop product rankings
- **Best for:** ad intelligence + trending products

### Open-Source Scrapers (GitHub)
- vooltex8egp/tiktok-shop-scraper (6★)
- 30 total TikTok Shop repos
- Low star counts, may need maintenance

---

## 5. RECOMMENDED STACK (all free)

### For MVP (wireless mic):
```
Supply side:     1688 API (on hold) + DHgate API (free) + AliExpress (Crawl4AI)
Demand side:     Mercado Livre API (free) + Amazon BR (requests) + Shopee (scrape)
Trend signal:    TikTok Creative Center (free) + Facebook Ad Library (free)
Matching:        SigLIP2 + pgvector (already working)
```

### For Scale (PI2+):
```
Add:             Shopee API + TikTok Shop API + Alibaba API
Add:             Winning Hunter API ($49/mo) for ad intelligence
Add:             Kalodata free trial for TikTok Shop deep data
```

---

## 6. WHAT TO DO NEXT

### Immediate ($0, can do now):
1. **DHgate API** — register at open.dhgate.com, search wireless mics
2. **TikTok Creative Center** — scrape trending product data
3. **Facebook Ad Library** — search wireless mic ads
4. **AliExpress Dropshipping Center** — trending product data

### When budget allows:
5. **Shopee API** — needs seller account
6. **TikTok Shop API** — needs partnership approval
7. **Winning Hunter** — $49/mo for full ad spy

### On hold:
8. 1688 scraping API — waiting for endpoint fix
9. MiMo web search — waiting for plugin activation
