/usr/bin/bash: warning: setlocale: LC_ALL: cannot change locale (pt_BR.UTF-8)
# ArbitLens BR — Source Matrix

## Overview

This document tracks all data sources for the Brazil market intelligence platform.
Each source has a status, what worked, what didn't, lessons learned, and future plans.

**Last updated:** 2026-05-28
**Product:** Wireless Lapel Microphone (Type-C)
**Markets:** Brazil (ML, Amazon BR, Shopee, TikTok Shop, Facebook Ads)

---

## Amazon BR

### Status: ✅ WORKING — Best Sellers Data

### What We Did First (WRONG)
1. Searched for "microfone lapela sem fio" on Amazon
2. Scraped first page of search results (15 products)
3. Got ASINs but NO sales data from search results
4. Scraped 4 individual product pages for sales data
5. Showed all 15 products including those without sales data

**Result:** Missing the real best sellers. Showing products that weren't actually selling.

### What Works Now (CORRECT)
1. Go to Amazon Best Sellers page for the category
2. Use browser console to extract product data (ASINs, titles, prices, ratings, reviews)
3. Only show products with verified review counts (proxy for sales)
4. Sort by reviews (highest = most sales)

**Result:** Found the real market leaders:
- Boya Mini-14: 2,069 reviews, R$401
- Hollyland LARK A1: 1,372 reviews, R$370
- AGold Premium: 816 reviews, R$92.90

### Data Points Available
- ✅ Product title
- ✅ Price (R$)
- ✅ Rating (stars)
- ✅ Review count (proxy for sales)
- ✅ Product images
- ✅ Product URLs
- ⚠️ Sales volume ("X+ bought in past month") — need to scrape individual pages
- ❌ BSR (Best Seller Rank) — not visible on best sellers page
- ❌ Seller count — not visible on best sellers page

### Cost
- Decodo: ~$0.54 for 6 product page screenshots
- Browser console: FREE
- Total: ~$0.54

### Lessons Learned
1. **Search results ≠ Best Sellers** — Always use category best sellers pages
2. **Reviews = market validation** — Higher reviews = more sales
3. **Browser console is free** — Use it to extract data from rendered pages
4. **Don't show products without data** — Only show verified products
5. **Vision is UNRELIABLE for numbers** — Use regex on HTML, not vision on screenshots

### Future Plans
1. Scrape individual product pages for sales volume ("X+ bought in past month")
2. Get BSR (Best Seller Rank) from product detail pages
3. Track review velocity (new reviews = growing market)
4. Add more categories (not just "Microfones Externos para Gravador de Voz")
5. Monitor price changes over time

---

## Mercado Livre

### Status: ⚠️ PARTIAL — Screenshot Analysis

### What We Did First (WRONG)
1. Tried ML API directly — blocked from datacenter IP
2. Tried Crawl4AI — got login wall
3. Tried browser tool — blocked
4. Used Decodo PNG + vision analysis to extract product data

**Result:** Got product titles, prices, ratings, but NOT sales numbers. Vision analysis couldn't read exact sales figures.

### What Works Now (PARTIAL)
1. Use Decodo PNG to get ML search results page
2. Use vision analysis to extract product titles, prices, ratings, sellers
3. Use vision analysis to get individual product page data (sales, reviews)
4. Use Decodo PNG to get ML product pages for sales data

**Result:** Got 35 ML products with:
- Titles, prices, ratings, sellers
- 2 products with verified sales data (1,000+ sold each)
- 16 products with URLs to ML pages

### Data Points Available
- ✅ Product title
- ✅ Price (R$)
- ✅ Rating (stars)
- ✅ Seller name
- ✅ Product URLs (16/35)
- ⚠️ Sales volume — only 2 products verified (1,000+ sold each)
- ❌ Review count — not extracted from screenshots
- ❌ Product images — not available from screenshots

### Cost
- Decodo: ~$0.81 for ML screenshots and product pages
- Vision analysis: FREE
- Total: ~$0.81

### Lessons Learned
1. **ML blocks from datacenter IP** — Need Decodo or residential proxy
2. **Vision is for images, not numbers** — Can't extract exact sales figures from screenshots
3. **Screenshot analysis is cheap** — $0.007/product for ML data
4. **Need individual product pages** — Search results don't show sales data
5. **Never estimate** — If vision can't read numbers, say "data not available"

### Future Plans
1. Get more ML product URLs from user's browser sessions
2. Scrape individual ML product pages for sales data
3. Get review counts from product pages
4. Get product images from ML pages
5. Track price changes over time

---

## Facebook Ad Library

### Status: ✅ WORKING — Free from Browser

### What We Did First
1. Navigated to Facebook Ad Library in browser
2. Searched for "microfone lapela sem fio"
3. Extracted advertiser names, ad start dates, ad copy
4. Found ~74 active ads for wireless mics in Brazil

**Result:** Got market intelligence on who's advertising, how long they've been running ads, and what they're promoting.

### What Works Now
1. Navigate to FB Ad Library in browser (FREE)
2. Search for product keywords
3. Extract advertiser names, ad dates, ad copy
4. Identify top advertisers and products

**Result:** Found key advertisers:
- Quality Import (Hollyland official) — 27+ days running
- Bigcell Distribuidora — 21+ days running
- + 72 more advertisers

### Data Points Available
- ✅ Advertiser name
- ✅ Ad start date
- ✅ Ad copy/text
- ✅ Ad platform (FB + IG)
- ✅ Ad type (video, image, carousel)
- ⚠️ Product being advertised — need to extract from ad copy
- ❌ Ad spend — not available from Ad Library
- ❌ Sales data — not available from Ad Library

### Cost
- Browser: FREE
- Total: $0

### Lessons Learned
1. **FB Ad Library is free** — No API key, no proxy needed
2. **Ad duration = market validation** — 27+ days running = profitable product
3. **WhatsApp CTA = direct sales** — Most ads use WhatsApp for orders
4. **Video ads dominate** — Premium products use video ads
5. **Official stores advertise** — Quality Import = Hollyland official

### Future Plans
1. Scrape more ads for wireless mics
2. Extract product names from ad copy
3. Track ad duration as market signal
4. Monitor new advertisers entering the market
5. Cross-reference with ML/Amazon products

---

## Amazon US

### Status: ⚠️ LIMITED — Few Products

### What We Did First
1. Tried to scrape Amazon US search results — blocked from datacenter IP
2. Used Decodo to get search results page
3. Extracted 4 products from HTML

**Result:** Only 4 products with limited data (no reviews, no sales).

### What Works Now
1. Use Decodo to get Amazon US search results
2. Extract product titles, prices, ASINs
3. Add to database with URLs

**Result:** 4 products in database:
- USB C Lavalier Microphone: $21.99
- Labstandard Wireless Lavalier: $8.99
- Mini Mic Pro: $24.99
- Wireless Lavalier Microphone: $8.71

### Data Points Available
- ✅ Product title
- ✅ Price (USD)
- ✅ Product URL
- ❌ Review count — not extracted
- ❌ Sales volume — not extracted
- ❌ Rating — not extracted

### Cost
- Decodo: ~$0.09 for 1 request
- Total: ~$0.09

### Lessons Learned
1. **Amazon US blocks from datacenter IP** — Need Decodo or proxy
2. **Different market** — US prices are much lower ($8-$25 vs R$34-R$780)
3. **Not our focus** — Brazil market is primary, US is secondary
4. **Limited data** — Only 4 products, not enough for analysis

### Future Plans
1. Scrape Amazon US Best Sellers page (same approach as BR)
2. Get review counts and ratings
3. Compare US vs BR prices for same products
4. Track US market trends

---

## Shopee

### Status: ❌ BLOCKED — Needs Proxy

### What We Did First
1. Tried to navigate to Shopee search page — blocked
2. Tried to search for Shopee products on Bing — no results
3. Tried to use Decodo — not available for Shopee

**Result:** No data available from Shopee.

### What Works Now
- Nothing — blocked from datacenter IP

### Data Points Available
- ❌ All data — blocked

### Cost
- $0 (no successful requests)

### Lessons Learned
1. **Shopee blocks from datacenter IP** — Need residential proxy
2. **Not a priority** — ML and Amazon BR are primary markets
3. **Many ML sellers also on Shopee** — Could cross-reference later

### Future Plans
1. Get residential proxy or use Decodo for Shopee
2. Scrape Shopee search results for wireless mics
3. Cross-reference with ML sellers (same sellers on both platforms)
4. Track Shopee prices vs ML prices

---

## TikTok Shop

### Status: ❌ BLOCKED — Needs Proxy

### What We Did First
1. Tried to navigate to TikTok Shop — blocked
2. Tried TikTok Creative Center — blocked
3. Tried to search for TikTok products on Google — blocked

**Result:** No data available from TikTok Shop.

### What Works Now
- Nothing — blocked from datacenter IP

### Data Points Available
- ❌ All data — blocked

### Cost
- $0 (no successful requests)

### Lessons Learned
1. **TikTok Shop blocks from datacenter IP** — Need residential proxy
2. **Important market** — TikTok Shop is growing fast in Brazil
3. **Need paid tools** — Kalodata ($46/mo) for TikTok Shop data

### Future Plans
1. Get residential proxy or use Decodo for TikTok
2. Scrape TikTok Shop product listings
3. Get sales data from TikTok Shop
4. Track TikTok Shop trends

---

## AliExpress

### Status: ❌ REMOVED — Not Our Scope

### What We Did First (WRONG)
1. Scraped AliExpress search results for wireless mics
2. Got 20 products with prices
3. Added to database

**Result:** AliExpress is Chinese supplier side — NOT our scope.

### What Works Now
- N/A — removed from database

### Data Points Available
- N/A — removed

### Cost
- $0 (scraping was free)

### Lessons Learned
1. **AliExpress is Chinese side** — 1688-intel team handles this
2. **Not our scope** — We focus on sales side (ML, Amazon BR/US, Shopee, TikTok)
3. **Removed from database** — Don't mix supplier data with sales data

### Future Plans
- None — AliExpress is not our responsibility

---

## Summary Table

| Source | Status | Products | Cost | Priority |
|--------|--------|----------|------|----------|
| Amazon BR | ✅ Working | 20 | $0.54 | HIGH |
| Mercado Livre | ⚠️ Partial | 35 | $0.81 | HIGH |
| Facebook Ads | ✅ Working | 74 ads | $0 | MEDIUM |
| Amazon US | ⚠️ Limited | 4 | $0.09 | LOW |
| Shopee | ❌ Blocked | 0 | $0 | MEDIUM |
| TikTok Shop | ❌ Blocked | 0 | $0 | HIGH |
| AliExpress | ❌ Removed | 0 | $0 | N/A |

**Total cost:** ~$1.44
**Total products:** 55
**Total ads:** 74

---

## Key Lessons Learned (All Sources)

1. **Search results ≠ Best Sellers** — Always use category best sellers pages
2. **Vision is for images, not numbers** — Use browser console for data extraction
3. **Never estimate** — If data not available, say "not available"
4. **Data first, insights second** — Let the data tell the story
5. **Reviews = market validation** — Higher reviews = more sales
6. **Ad duration = market signal** — Longer ads = profitable products
7. **Browser console is free** — Use it to extract data from rendered pages
8. **Decodo is expensive** — Use sparingly, only when needed
9. **Never touch Chinese side** — 1688-intel team handles AliExpress, 1688, etc.
10. **Always verify from source** — Don't trust screenshots for numbers

---

## Critical Lesson: Vision Analysis is UNRELIABLE for Numbers

### What Happened
Used vision analysis to extract sales data from ML product screenshots. Vision gave WRONG numbers:

| Product | Vision Said | Reality | Error |
|---------|-------------|---------|-------|
| MyMotors | 1,000+ sold | 10,000+ sold | 10x undercount |
| Hollyland | 1,000+ sold | 100+ sold | 10x overcount |
| MyMotors reviews | 523 | 5,112 | 10x undercount |
| MyMotors price | R$79.97 | R$70.77 | Wrong |

### Why It Happened
1. Vision analysis is designed for IMAGES, not TEXT/NUMBERS
2. Screenshots have compressed text that's hard to read
3. Vision "hallucinates" numbers when it can't read them clearly
4. No way to verify vision output without checking source

### The Fix
1. **NEVER trust vision for numbers** — only for images
2. **Use regex on HTML** to extract numbers from web pages
3. **If HTML doesn't have data (JS-rendered), use PNG + vision BUT verify carefully**
4. **Always cross-check** vision output against other sources
5. **If unsure, say "data not available"** — don't estimate

### Impact
- Dashboard showed wrong sales numbers for 2 days
- Users saw 1,000+ sold when it was actually 10,000+ (MyMotors)
- Users saw 1,000+ sold when it was actually 100+ (Hollyland)
- Trust in data was compromised

### Prevention
1. Always extract numbers from HTML first (regex)
2. If HTML doesn't have data, use PNG + vision BUT:
   - Be very specific about what you're looking for
   - Ask for EXACT numbers, not estimates
   - Cross-check against other sources
3. If still unsure, mark as "unverified" in the dashboard

---

## How to Find Category IDs (Scalable Approach)

### For Mercado Livre
1. Get any product page in the category (use Decodo HTML)
2. Search HTML for `mais-vendidos/MLB\d+` pattern
3. Extract the MLB ID (e.g., MLB270243 for microphones)
4. Use `https://www.mercadolivre.com.br/mais-vendidos/MLB270243` for best sellers

### For Amazon BR
1. Navigate to any product in the category
2. Find the "Best Sellers" link in the breadcrumb or navigation
3. Extract the category ID from the URL
4. Use `https://www.amazon.com.br/gp/bestsellers/CATEGORY_ID` for best sellers

### Scalability
- Amazon: FREE — browser console works for any category
- ML: $0.09 per category (Decodo) — but ONE request gets ALL best sellers
- Can be done for ANY product category, not just microphones

### Categories We Can Track
- Wireless microphones (MLB270243)
- Any other category on ML/Amazon
- Just need to find the category ID first

