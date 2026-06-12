# ARBITLENS
### See the arbitrage. Before everyone else.

---

> **One-liner:** Paste any product from any platform. See where it's cheaper, where it's trending, and what your margin would be. Confidence-scored. No BS.

---

## CURRENT STATUS (2026-05-27 — verified)

| Component | Status | Notes |
|-----------|--------|-------|
| Python env + deps | ✅ Done | .venv: torch 2.12.0+cpu, transformers, crawl4ai, browser-use, fastapi, pgvector, psycopg2, imagehash, pillow, playwright |
| config/.env | ✅ Done | Firecrawl API, DB creds, Decodo proxy, Xiaomi MiMo API |
| Project docs (README, SOUL, PROGRESS) | ✅ Done | Full spec with architecture, schema design, business model |
| Database schema (pgvector + SigLIP2 768-dim) | ✅ Done | migrations/001_initial_schema.sql — 4 tables, HNSW index, 16 import factors seeded |
| SigLIP2 model download | ⏳ Pending | Deps installed, model not yet downloaded |
| ML scraping scripts | ✅ Done | scripts/scrape_ml.py |
| 1688 scraping (Firecrawl) | ✅ Done | scripts/scrape_1688_firecrawl.py |
| AliExpress scraping (Crawl4AI) | ✅ Done | scripts/aliexpress_scraper_v3.py (3 iterations) |
| Amazon BR scraping (browser-use) | ✅ Done | scripts/aliexpress_scraper.py — 5 listings + 15 images scraped |
| Mercado Livre scraping (API) | ✅ Done | scripts/scrape_ml.py |
| Vector search + SigLIP2 matching | ✅ Done | scripts/matching.py + scripts/test_matching.py |
| Margin calculator + import factors | ✅ Done | scripts/margins.py + tests/test_margins.py |
| FastAPI backend (/search, /product) | ✅ Done | app/backend/ — main.py + 2 routers + 4 services |
| HTML frontend (search + product pages) | ✅ Done | app/frontend/ — index.html, style.css, app.js |
| End-to-end demo | ⏳ Pending | Needs SigLIP2 download + data loading into DB |

**Working:** DB schema applied, scrapers written (4 platforms), matching + margin code done, FastAPI backend built, HTML frontend built. 5 Amazon BR listings scraped with 15 product images.
**In progress:** SigLIP2 model download, loading scraped data into DB, wiring end-to-end.
**Next:** Download SigLIP2 → load scraped data into DB → compute embeddings → E2E test.

---

## THE PROBLEM

A product costs ¥18 ($2.50) on 1688. The same product sells for R$89 on Mercado Livre. That's a 75% margin opportunity. But:

- **You don't know it exists** unless you happen to browse 1688
- **You don't know it's trending** unless you check every marketplace daily
- **You don't know it's the same product** because titles are in Chinese, Portuguese, and English
- **You don't know the real margin** because shipping, taxes, and platform fees are hidden
- **You don't know if you're too late** because by the time you see "50,000 sold," 400 sellers are already on it

Dropshippers, importers, and ML sellers are flying blind. They react to what's already saturated instead of acting on what's emerging.

**ArbitLens fixes this.**

---

## WHAT THE USER SEES

### Entry Point: Search

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│   ARBITLENS                                              │
│   ─────────                                              │
│                                                          │
│   ┌────────────────────────────────────────────────┐     │
│   │  Paste a URL, upload an image, or describe a   │     │
│   │  product...                            [SEARCH]│     │
│   └────────────────────────────────────────────────┘     │
│                                                          │
│   TRENDING NOW IN BRAZIL:                                │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │
│   │ Wireless│ │ Electric│ │  Mini   │ │Bluetooth│      │
│   │  Mic 🔥 │ │ Scrubber│ │Projector│ │ Earbuds │      │
│   │ R$88    │ │ R$149   │ │ R$299   │ │ R$79    │      │
│   └─────────┘ └─────────┘ └─────────┘ └─────────┘      │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Product Page (what they see after searching)

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  ← Back to search                                        │
│                                                          │
│  ┌─── PRODUCT ──────────────────────────────────────┐    │
│  │  Wireless Lapel Microphone Type-C                 │    │
│  │  Source: Mercado Livre - R$88                     │    │
│  │  [product image]                                  │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  ┌─── CROSS-PLATFORM PRICES ────────────────────────┐    │
│  │                                                   │    │
│  │  Platform          Price     Sales     Status     │    │
│  │  ───────────────────────────────────────────────  │    │
│  │  1688 (source)     ¥22 ($3)  MOQ 50    ✅ Active  │    │
│  │  AliExpress        $7.99     2,340 ord ✅ Active  │    │
│  │  Amazon BR         R$129     BSR #1,203✅ Active  │    │
│  │  Amazon USA        $15.99    BSR #4,521✅ Active  │    │
│  │  Mercado Livre     R$88      1,240 sold✅ Active  │    │
│  │  Shopee BR         R$79      890 sold  ✅ Active  │    │
│  │  TikTok Shop       $12.99    trending  🔥 Hot     │    │
│  │                                                   │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  ┌─── MARGIN ANALYSIS ──────────────────────────────┐    │
│  │                                                   │    │
│  │  Selling on        Cost (50u)   Price    Margin   │    │
│  │  ───────────────────────────────────────────────  │    │
│  │  Mercado Livre     R$25         R$88     72%     │    │
│  │  Amazon BR         R$25         R$129    81%     │    │
│  │  Shopee BR         R$25         R$79     68%     │    │
│  │  Amazon USA        $8.50        $15.99   47%     │    │
│  │                                                   │    │
│  │  * Cost = 1688 price × import factor + shipping   │    │
│  │  * Factor range: 1.6x-3.5x depending on quantity  │    │
│  │                                                   │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  ┌─── PROBABLE SOURCE MATCHES ──────────────────────┐    │
│  │                                                   │    │
│  │  98% ─ 1688: Shenzhen Coico Electronics           │    │
│  │        ¥22/unit, MOQ 50, 98.2% positive          │    │
│  │        [view listing]                             │    │
│  │                                                   │    │
│  │  92% ─ 1688: Guangzhou Audio Tech                 │    │
│  │        ¥18/unit, MOQ 200, 95.1% positive         │    │
│  │        [view listing]                             │    │
│  │                                                   │    │
│  │  87% ─ AliExpress: "Lapel Mic Wireless Type-C"    │    │
│  │        $7.99, 2,340 orders, 4.6★                  │    │
│  │        [view listing]                             │    │
│  │                                                   │    │
│  │  65% ─ 1688: Yiwu Direct Store                    │    │
│  │        ¥15/unit, MOQ 500, 92.3% positive         │    │
│  │        [view listing]                             │    │
│  │                                                   │    │
│  │  41% ─ AliExpress: "Mini Mic USB-C Phone"         │    │
│  │        $5.49, 180 orders, 4.2★                    │    │
│  │        [view listing]                             │    │
│  │                                                   │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  ┌─── MARKET PULSE ─────────────────────────────────┐    │
│  │                                                   │    │
│  │  Velocity:    🔥 Hot — trending up this month     │    │
│  │  Competition: 🟡 Medium — 12 sellers on ML        │    │
│  │  Window:      📅 ~3-6 months before saturation    │    │
│  │                                                   │    │
│  │  Trend sources:                                   │    │
│  │  • Mercado Livre: #3 in Games category            │    │
│  │  • TikTok Shop: Tech accessories trending         │    │
│  │  • Amazon BR: BSR climbing last 30 days           │    │
│  │                                                   │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  ┌─── AI ANALYSIS ──────────────────────────────────┐    │
│  │                                                   │    │
│  │  ⚡ VERDICT: Strong Opportunity                   │    │
│  │                                                   │    │
│  │  • 72% margin on ML with 50-unit order            │    │
│  │  • Content creation boom driving demand           │    │
│  │  • TikTok viral signal confirms trend             │    │
│  │  • Moderate competition — room for entry          │    │
│  │  • Recommended: Test with 50 units on ML          │    │
│  │  • Risk: Trend may peak in 3-4 months             │    │
│  │                                                   │    │
│  │  💡 TIP: The 92% match at ¥18/MOQ200 drops your   │    │
│  │  cost to R$18/unit, pushing margin to 79%.        │    │
│  │  Scale to 200 once you validate demand.           │    │
│  │                                                   │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  ┌─── ACTIONS ──────────────────────────────────────┐    │
│  │  [💾 Save to watchlist] [📤 Export PDF]            │    │
│  │  [🔔 Alert when price changes] [📊 Full report]   │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## VALUE DELIVERED (what users pay for)

| Value | Description | Who cares |
|-------|-------------|-----------|
| **Cross-platform price comparison** | Same product, 7 platforms, one view | Everyone |
| **Confidence-scored matching** | "98% this is the same product" — not false certainty | Everyone |
| **Real margin calculation** | After shipping, taxes, platform fees | Dropshippers, importers |
| **Trending signal** | Is this product hot right now or already dead? | Everyone |
| **Velocity tracking** | Getting hotter or cooling down? | Advanced sellers |
| **Multiple source options** | 5 possible suppliers ranked by confidence + price | Smart buyers |
| **Competition count** | How many sellers are already on this? | Everyone |
| **AI verdict** | "Should I sell this? Yes/No/Why" | Beginners, lazy pros |

---

## VALUE HYPOTHESIS

### We believe:

1. **Brazilian e-commerce sellers (ML, Shopee, Amazon BR) don't have a tool that shows them where to source trending products from China.** They manually browse 1688, AliExpress, or buy from intermediaries who mark up 200-400%.

2. **The biggest information asymmetry in cross-border e-commerce is: "What product is trending in Brazil that I can source cheaply from China?"** This gap is worth money.

3. **Confidence scores are better than exact matches.** Users don't trust tools that say "THIS is the product" and sometimes get it wrong. Showing ranked probabilities is more honest and more useful.

4. **The user's own judgment + our data beats any automated system.** We're not replacing the seller's brain. We're giving them superpowers.

5. **A tool that saves 4 hours of research per product and finds 1-2 hidden opportunities per week is worth $50-100/month to a serious seller.**

### We will test this by:

1. Show the wireless mic product page to 5 ML sellers
2. Ask: "Would you use this? Would you pay for this? What's missing?"
3. If 3+ say yes → build it
4. If they say "but I need X" → add X
5. If they say "meh" → pivot

---

## ARCHITECTURE

### How it works (technical)

```
USER INPUT
    │
    ▼
┌─────────────────────────┐
│   IDENTIFY PRODUCT      │
│   • URL → scrape that   │
│     platform            │
│   • Image → SigLIP2 embed│
│   • Text → search       │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│   VECTOR SEARCH         │
│   (pgvector)            │
│                         │
│   Search each platform  │
│   index for similar     │
│   products:             │
│   • 1688 embeddings     │
│   • AliExpress embeds   │
│   • Amazon embeds       │
│   • ML embeds           │
│   • Shopee embeds       │
│   • TikTok embeds       │
│                         │
│   Returns: top-K per    │
│   platform with cosine  │
│   similarity scores     │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│   ENRICH                │
│                         │
│   For each match:       │
│   • Scrape current      │
│     price               │
│   • Calculate margin    │
│     (import factor)     │
│   • Check sales         │
│     velocity            │
│   • Count competition   │
│   • Fetch trend signal  │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│   PRESENT               │
│                         │
│   Product page with:    │
│   • Price table          │
│   • Margin analysis      │
│   • Confidence-ranked   │
│     matches              │
│   • Market pulse         │
│   • AI verdict           │
└─────────────────────────┘
```

### Tech Stack

```
FRONTEND:     Plain HTML/JS (vanilla, no framework)        ✅ Done (app/frontend/)
BACKEND:      Python (FastAPI)                              ✅ Done (app/backend/)
DATABASE:     PostgreSQL + pgvector                         ✅ Schema applied, HNSW indexed
EMBEDDINGS:   SigLIP2 (768-dim, upgraded from CLIP 512)    ⏳ Deps ready, model pending download
SCRAPING:     Firecrawl (1688), Crawl4AI (AliExpress),     ✅ Scripts written (4 platforms)
              requests+BeautifulSoup (Amazon, ML API)       ✅ 5 Amazon BR listings scraped
IMAGE HASH:   imagehash (pHash for fast exact duplicates)   ✅ Installed + code written
CACHE:        Redis (for scraping rate limits)              ❌ Not started
HOSTING:      Current server (10.109.160.3)
```

**NOTE:** All Python deps installed in .venv. DB schema applied with HNSW index. Scrapers, matching, margins, backend, and frontend code all written. SigLIP2 model download + data loading into DB are the remaining blockers for E2E.

### Database Schema

```sql
-- Products from ALL platforms (see migrations/001_create_arbitlens_schema.sql)
CREATE TABLE arbitlens_products (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(20) NOT NULL,        -- '1688', 'aliexpress', 'amazon_br', etc.
    platform_id VARCHAR(100) NOT NULL,     -- offer_id, ASIN, item_id, etc.
    title TEXT NOT NULL,
    title_translated TEXT,                 -- English translation
    price DECIMAL(10,2),
    currency VARCHAR(5),
    url TEXT,
    image_urls TEXT[],                     -- all product images
    image_embedding VECTOR(768),           -- SigLIP2 embedding of main image
    image_hash VARCHAR(64),               -- pHash for fast dedup
    supplier_name VARCHAR(200),
    moq INTEGER,
    sales_total INTEGER,
    sales_30d INTEGER,
    review_count INTEGER,
    review_avg DECIMAL(3,2),
    category VARCHAR(100),
    bsr_rank INTEGER,                     -- Amazon Best Seller Rank
    is_active BOOLEAN DEFAULT TRUE,
    first_seen TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW(),
    UNIQUE(platform, platform_id)
);

-- Similarity scores between products (precomputed + cached)
CREATE TABLE arbitlens_matches (
    id SERIAL PRIMARY KEY,
    product_a_id INTEGER REFERENCES arbitlens_products(id),
    product_b_id INTEGER REFERENCES arbitlens_products(id),
    confidence DECIMAL(5,4),              -- 0.0 to 1.0
    match_method VARCHAR(20),             -- 'siglip2', 'phash', 'title', 'combined'
    user_verified BOOLEAN,                -- user confirmed match
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(product_a_id, product_b_id)
);

-- Import cost factors (quantity-based)
CREATE TABLE arbitlens_import_factors (
    id SERIAL PRIMARY KEY,
    country VARCHAR(5) NOT NULL,          -- 'BR', 'US'
    quantity_min INTEGER,
    quantity_max INTEGER,
    factor DECIMAL(4,2),                  -- e.g., 3.50 for Brazil 1-50 units
    notes TEXT
);

-- User watchlists
CREATE TABLE arbitlens_watchlists (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    product_id INTEGER REFERENCES arbitlens_products(id),
    alert_price_change BOOLEAN DEFAULT TRUE,
    alert_velocity_change BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## MVP SCOPE

### The Product: Wireless Lapel Microphone (Type-C)

**Why this product:**
- #1 trending category on Mercado Livre (4 of top 15 in Games)
- Content creation boom in Brazil
- Cheap on 1688 (Shenzhen electronics, $2-5/unit)
- Massive margin (R$88 on ML vs $3 source = 72%+ margin)
- Simple product, clear specs
- Small and light (cheap shipping)
- Also trending on TikTok Shop

### MVP Steps

```
WEEK 1: THE DATA                              ← Scrapers done, data partially loaded
  ├─ [x] Python env + all deps installed (.venv)
  ├─ [x] config/.env with API keys + DB creds
  ├─ [x] Database schema (pgvector + SigLIP2 HNSW index)
  ├─ [x] ML scraping scripts (scripts/scrape_ml.py)
  ├─ [~] Scrape 20 wireless mic listings from 1688 (script exists)
  ├─ [~] Scrape 20 wireless mic listings from AliExpress (script exists, v3)
  ├─ [x] Scrape wireless mic listings from Amazon BR (5 listings + 15 images)
  ├─ [~] Scrape wireless mic listings from Mercado Livre (script exists)
  ├─ [ ] Compute SigLIP2 embeddings for all product images
  └─ [ ] Store everything in PostgreSQL + pgvector

WEEK 2: THE MATCHING
  ├─ [x] Build vector search: given a product image, find similar (scripts/matching.py)
  ├─ [ ] Test confidence scores on the 70 products
  ├─ [ ] Tune: which threshold gives best results?
  ├─ [ ] Build the price comparison table
  ├─ [x] Build the margin calculator (scripts/margins.py + tests)
  └─ [ ] Build the market pulse (velocity from sales data)

WEEK 3: THE PAGE                              ← Frontend built, needs backend wiring
  ├─ [x] Simple web page: search bar + product page (app/frontend/)
  ├─ [ ] Wire up: search → vector DB → results → display
  ├─ [ ] Show: prices, margins, confidence matches, pulse
  ├─ [ ] Test with 5 real ML sellers
  └─ [ ] Iterate based on feedback

WEEK 4: THE POLISH
  ├─ [ ] Add AI verdict (simple rules, not LLM yet)
  ├─ [ ] Add export (PDF or shareable link)
  ├─ [ ] Add basic auth (login page)
  └─ [ ] Launch to 10 beta users
```

### MVP Success Criteria

| Metric | Target | Why |
|--------|--------|-----|
| Matching accuracy | >70% correct in top 3 results | Users must find the right product |
| Price data freshness | <24 hours old | Stale prices are useless |
| Margin calculation | Within 20% of reality | Good enough for decision-making |
| User feedback | 3/5 testers say "I'd use this" | Validates the concept |
| Time saved | >30 min per product vs manual | Justifies paying for the tool |

---

## BUSINESS MODEL

### Phase 1: Self-use (Month 1-2)
Use ArbitLens yourself. Find products. Source from 1688. Sell on ML/Amazon.
**Revenue:** From arbitrage itself.
**Cost:** Server + scraping APIs (~$100/mo)

### Phase 2: Consulting (Month 2-3)
Show the tool to your mentees and seller network.
"Give me a product, I'll find you the source and calculate your margin."
**Revenue:** R$50-100 per product analysis.
**Cost:** Your time.

### Phase 3: SaaS (Month 4+)
Self-serve tool. Login, search, get results.
**Revenue:** R$149-299/month subscription.
**Target:** 50 paying users = R$7,500-15,000/mo

### Pricing

```
FREE:     5 searches/month, basic results
BASIC:    R$149/mo — 100 searches, full product page
PRO:      R$299/mo — Unlimited searches, alerts, AI analysis, API access
TEAM:     R$699/mo — 5 seats, priority data, custom reports
```

---

## COMPETITIVE LANDSCAPE

| Tool | What they do | What they DON'T do | ArbitLens advantage |
|------|-------------|-------------------|-------------------|
| **Winning Hunter** | TikTok/FB ad spy | No sourcing, no 1688, no margin calc | We connect demand to supply |
| **Minea** | All-in-one product research | No confidence scores, no 1688 | Honest matching + Chinese sourcing |
| **AliShark** | AliExpress tracking | No Brazil focus, no ML | Brazil-first, local pricing |
| **Ecomhunt** | Daily curated picks | No search, no matching | User-driven, not curated |
| **Importa Simples** | Import cost calculator | No product discovery | Discovery + calculation combined |
| **Manual 1688 browsing** | Find suppliers yourself | Hours of work, no cross-platform | Instant, automated |

**ArbitLens is the only tool that:**
1. Starts from WHAT'S TRENDING (not from 1688)
2. Shows CONFIDENCE SCORES (not false exact matches)
3. Calculates REAL MARGINS (not just price comparison)
4. Focuses on BRAZIL (not US-centric)

---

## GOALS & TIMELINE

### Month 1: Prove it works
- [~] MVP live with wireless mic as test product ← Backend+frontend built, SigLIP2 + data loading pending
- [ ] 5 ML sellers test it and give feedback
- [ ] Matching accuracy >70%
- [ ] Margin calculation within 20% of reality

### Month 2: Expand products
- [ ] 100 products indexed across 5 platforms
- [ ] Add electric scrubber, mini projector, earbuds
- [ ] Add velocity tracking (7-day sales delta)
- [ ] 10 paying beta users

### Month 3: Scale
- [ ] 1,000 products indexed
- [ ] Automated daily scraping pipeline
- [ ] Alert system (price changes, new trends)
- [ ] 30 paying users

### Month 6: Business
- [ ] 10,000+ products indexed
- [ ] Full platform with login, billing, API
- [ ] 100+ paying users
- [ ] R$15,000+/mo revenue

---

## RISKS & MITIGATIONS

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Image matching accuracy too low | Users lose trust | Combine CLIP + pHash + title. Show confidence. Let users correct. |
| 1688 blocks our scraping | No source data | Firecrawl + Apify fallback + proxy rotation |
| Mercado Livre API changes | No trend data | Scraping fallback + cached data |
| Someone copies the idea | Competition | Speed + Brazil focus + community moat |
| Users won't pay | No revenue | Prove value with free tier, then gate features |
| Import factor too inaccurate | Bad margins | Let users input their own factor. Start with range. |

---

## APPENDIX: PRODUCT URL PATTERNS

```
1688:           https://detail.1688.com/offer/{id}.html
AliExpress:     https://www.aliexpress.com/item/{id}.html
Amazon BR:      https://www.amazon.com.br/dp/{asin}
Amazon USA:     https://www.amazon.com/dp/{asin}
Mercado Livre:  https://www.mercadolivre.com.br/produto/{id}
Shopee BR:      https://shopee.com.br/product/{shop_id}/{item_id}
TikTok Shop:    https://shop.tiktok.com/view/product/{id}
```

---

## APPENDIX: FIRST PRODUCT DATA

### Wireless Lapel Microphone — Source Keywords

```
1688:       无线领夹麦克风 Type-C
AliExpress: wireless lapel microphone type-c
Amazon BR:  microfone lapela sem fio tipo c
ML:         microfone lapela sem fio tipo-c
TikTok:     wireless mic for phone
```

### Known Listings (from ML Best Sellers)

```
Hollyland Lark M2 Duo Combo      R$898   (premium, pro content creators)
Microfone MICGEEK Tipo-C Duplo   R$88    (budget, high volume)
Microfone Nixzen Tipo-C Duplo    R$89    (budget, high volume)
Microfone Kaidi Tipo-C           R$539   (mid-range)
```

### Estimated 1688 Source Prices

```
Budget mic (similar to MICGEEK/Nixzen):    ¥15-25 ($2-3.50)
Mid-range (similar to Kaidi):              ¥50-80 ($7-11)
Premium (similar to Hollyland):            ¥150-250 ($21-35)
```

### Estimated Margins (at 50 units, Brazil import factor 3.5x)

```
Budget:   Cost R$25, Sell R$88,  Margin 72%
Mid:      Cost R$70, Sell R$539, Margin 87%
Premium:  Cost R$175, Sell R$898, Margin 80%
```

---

*Created: May 26, 2026*
*Authors: Hermes + User*
*Status: PLANNING → MVP*
*Next: Build the wireless mic data pipeline*
