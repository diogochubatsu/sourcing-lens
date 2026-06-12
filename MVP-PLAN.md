# arbt.ly — MVP Plan (Value First)

## The Promise
"Show me what's selling in Brazil RIGHT NOW, how fast, at what price, 
and who's winning — so I can decide if I should enter this market."

---

## PHASE 1: REAL SALES DATA (Value = What's Hot)

### 1.1 Amazon BR Product Details
**Why:** BSR (Best Seller Rank), review count, sales estimates
**How:** Scrape individual product pages for the 15 ASINs we have
**Data to extract:**
- BSR rank (position in category)
- Review count + average rating
- "X+ bought in past month" (Amazon shows this)
- Seller count (competition)
- Product listing date (how long on market)
- A+ content presence (professional seller?)

**Script:** `scripts/scrape_amazon_details.py`
**Output:** Update products table with sales data

### 1.2 Mercado Livre — The #1 Platform in Brazil
**Why:** ML is where Brazilians actually buy. Amazon BR is secondary.
**How:** Options to explore:
- ML API (was blocked, try different endpoint or user-agent)
- Browser-use with stealth (already proven on Amazon BR)
- Google Shopping → ML listings with prices
- Manual seed data (first 10-20 products from our research)

**Data to extract:**
- Product title, price, images
- Sales count ("X vendidos")
- Reputation score (ML seller rating)
- Listing date
- Free shipping flag
- Full/Classic listing type (affects visibility)

**Script:** `scripts/scrape_ml.py`
**Output:** New products in DB with platform='ml'

### 1.3 Facebook Ad Library — Trend Signal
**Why:** 500+ active wireless mic ads in Brazil. Proven sellers = long-running ads.
**How:** Already proven in earlier session — facebook.com/ads/library works
**Data to extract:**
- Advertiser name
- Product being advertised
- Ad start date (longer = more profitable)
- Ad platform (FB, IG, etc.)
- Estimated ad spend tier

**Script:** `scripts/scrape_fb_ads.py`
**Output:** New table: fb_ads (advertiser, product, start_date, platform)

---

## PHASE 2: CROSS-PLATFORM INTELLIGENCE (Value = Competition Map)

### 2.1 Price Comparison
**For each product, show:**
- Price on ML vs Amazon BR
- Price distribution across sellers
- Price trend (if we have historical data)

### 2.2 Competition Density
**For each product category, show:**
- Number of sellers on ML
- Number of sellers on Amazon BR
- Review concentration (do top 3 dominate?)
- New entrants in last 30 days

### 2.3 Sales Velocity Estimates
**Calculate:**
- "X+ bought in past month" from Amazon
- Review velocity (reviews per month = proxy for sales)
- BSR rank changes (if we track over time)

---

## PHASE 3: AI INSIGHTS (Value = So What?)

### 3.1 Market Summary
- "15 products tracked across 2 platforms"
- "Average price R$82, sweet spot R$80-100"
- "Dual mics dominate (80%), noise cancellation expected (60%)"

### 3.2 Opportunity Signals
- "Product X has 500+ sales/month but only 3 sellers = opportunity"
- "Price gap between ML and Amazon = channel opportunity"
- "Product Y has 4.8 stars but only 50 reviews = early market"

### 3.3 Risk Signals
- "Product Z has 200+ sellers = saturated"
- "Price race to bottom in budget segment"
- "Brand dominance in premium (BOYA has 30% of R$100+ market)"

---

## PHASE 4: DASHBOARD (Value = See It)

### Layout (top to bottom):
1. **Stats Bar** — products tracked, platforms, price range, avg
2. **🔥 Trending Now** — top 5 by sales velocity, with real numbers
3. **📋 All Products** — cards with image, price, sales, rating, competition
4. **📊 Market Analysis** — price distribution, features, segments
5. **💡 AI Insights** — opportunities, risks, recommendations

### Data on Each Product Card:
- Product image
- Platform (ML / Amazon BR)
- Price in BRL
- Sales count / velocity
- Rating + review count
- Seller count (competition)
- Date first seen
- BSR rank (Amazon) / Reputation (ML)

---

## EXECUTION ORDER (Value First)

### Sprint 1: Amazon BR Sales Data (TODAY)
1. Scrape 15 Amazon BR product pages for BSR, reviews, sales
2. Update DB with real sales numbers
3. Update dashboard to show sales data on cards
4. **VALUE DELIVERED:** "This mic sells 500+/month at R$85 with 4.6 stars"

### Sprint 2: Mercado Livre (NEXT)
1. Solve ML scraping (browser-use or manual seed)
2. Get 15-20 ML products with sales data
3. Add ML products to dashboard
4. **VALUE DELIVERED:** "Same product on ML for R$79 with 1000+ sales"

### Sprint 3: Facebook Ads (PARALLEL)
1. Scrape FB Ad Library for wireless mic ads
2. Identify top advertisers and products
3. Add ad data to dashboard
4. **VALUE DELIVERED:** "These 5 sellers have been running ads for 6+ months"

### Sprint 4: Cross-Platform Analysis (AFTER DATA)
1. Price comparison across platforms
2. Competition density analysis
3. Sales velocity ranking
4. **VALUE DELIVERED:** "The money is in R$80-100 dual mics with case"

---

## TECHNICAL NOTES

### Scraping Strategy
- **Amazon BR:** browser-use (already proven, ~30s/page)
- **Mercado Livre:** browser-use with stealth, or manual data
- **Facebook Ads:** direct HTTP (already proven)
- **Proxy:** Decodo needs fixing, or skip for now

### Database Updates Needed
- Add columns: bsr_rank, review_count, sales_estimate, seller_count
- Add table: fb_ads (advertiser, product, start_date, platform)
- Add table: price_history (product_id, price, date, platform)

### Frontend Updates
- Product cards need sales data fields
- New "Trending" section at top
- Competition indicator on cards
- Platform comparison view

---

## SUCCESS METRICS

The MVP is successful when someone opens the page and says:
"This tells me exactly what to sell and at what price."

Not: "Here's a list of products"
Not: "Here's some analysis"
But: "This product sells 500/month at R$85 with only 3 sellers. Enter at R$79."
