# ArbitLens v0.3.0 — Status

## Data
- **997 active products** across **19 L1 categories**
- **432 Amazon BR** | **301 Amazon US** | **264 Mercado Livre**
- **130 matches** (80% avg confidence, 3-tier hierarchical matching)
  - 106 BR↔ML (CLIP embeddings, threshold 70%, 15 L1 categories)
    - 88 strict (L1+L2+L3) | 3 medium (L1+L2) | 14 broad (L1 only)
  - 24 BR↔US (CLIP embeddings, threshold 70%)

## Category Taxonomy (v0.3.2)
- **3-level hierarchy**: L1 (19) → L2 (76) → L3 (299) — see `scripts/taxonomy.py`
- **84.8% of products properly classified** (844/997 with specific L3, 153 still "Geral")
- Cleanup: 239 L2=L1 + 187 L3=L1 circulars + 2 NULL L1 fixed
- Classifier (`categorize_products.py`): 60+ keyword rules (PT + EN) covering 16 L1
- Cleanup tool: `scripts/cleanup_categories.py` (handles legacy L2=L1/L3=L1)

## 3-Tier Matching (v0.3.2)
- **STRICT** (L1+L2+L3): highest confidence, exact same subcategory — 88 matches
- **MEDIUM** (L1+L2): same broad group, L3 may be "Geral" — 3 matches
- **BROAD** (L1 only): fallback when L2/L3 not yet classified — 14 matches
- Script: `scripts/matching_v7.py` (replaces v6)
- Net improvement: 50→106 BR↔ML matches (+112%), 18→24 BR↔US (+33%)

## Site Unblocker (SU) — Gentle scraper
- Decodo SU (U0000434457): forward proxy @ unblock.decodo.com:60000
- Bypasses both Amazon BR 503 blocks AND ML bot detection
- Used in `scrape_amazon_bestsellers.py --use-su` for Amazon BR
- Tested: 1 Amazon BR category (Beauty, 30 products in 5s) and Brinquedos (30 in 27s)
- Caveat: SSL self-signed, need `ssl._create_unverified_context()`

## Tools (v0.3.0)
- **Decodo Scraping API** (U0000420946) — ML best-sellers scraping (JSON REST) ✅
- **Decodo Site Unblocker** (U0000434457) — Amazon BR + ML fallback on 503/429 (forward proxy) ✅
- **Decodo Residential BR** (span5nxws5) — Amazon BR direct scraping ✅
- **Decodo US Residential** (span5nxws5) — Amazon US direct scraping ✅
- **Decodo ISP Static** (sp2idylm9q) — generic proxy (AU IP) ✅
- **Decodo Mobile** (spraglxgvk) — ❌ 407 auth fail (wrong password / inactive plan)
- **Firecrawl v2** (2 keys) — alternative scraping ✅
- See `DECODO_TOOLBOX.md` for full status of all tools

## Amazon BR Scraper (v0.3.0)
- New: `--use-su` flag enables Decodo Site Unblocker fallback on 503/429/block (opt-in)
- New: `--delay N` overrides request delay (default 2s)
- New: `--max-requests N` overrides rate limit per minute (default 10/min, gentle)
- Built-in rate limiter sleeps automatically when over limit
- Test run: `--use-su --delay 4 --max-requests 3 --no-enrich --category beauty`
  - 30 products Beleza scraped in 20s
  - 503 on first attempt, SU fallback succeeded

## ML Scraping (v0.3.0)
- **49 new ML products** via Decodo Scraping API:
  - Beleza: 19
  - Brinquedos: 10
  - Bebê: 20
- ML parser: JSON-LD embedded in page → product_id, title, current_price, pictures.id, url
- Image URL: `https://http2.mlstatic.com/D_Q_NP_2X_{picture_id}-AB.webp`
- 5 new BR↔ML matches: Beleza 3 (87%, 77%, 76%), Brinquedos 2 (88%, 80%)
- 6 new BR↔US matches: Beleza 2, Brinquedos 4

## Categories
Audio (250), Beleza (79, NEW ML), Iluminação (78), Wearables (75), Brinquedos (70, NEW ML), Casa (66), Esportes (61), Bebê (50, NEW ML), Eletrodomésticos (50), Escritório (48), Bolsas (45), Cozinha (44), Ferramentas (40), Jardim (35), Moda (28), Saúde (25), Pet Shop (20), Beleza L3 (10), Informática (8)

## Endpoints (16 active)
- `/api/health` `/api/stats` `/api/categories`
- `/api/categories/{l1}` `/api/products` `/api/matches?include_br_us=true`
- `/api/matches` `/api/match-history/{id}`
- `/api/price-history` `/api/price-drops` `/api/cache-stats`
- `/product/{id}` `/api/admin/scraper-health`
- `/api/admin/categories` `/api/users` `/api/users/login`

## Database
- 10 indexes (category, sales, bsr, platform, etc.) — queries <2ms
- Cache: 60s/30s TTL on stats/categories/price-drops
- `scraper_health` table: tracks runs

## Recent Git
- `ff645b95` Add Decodo Site Unblocker fallback to Amazon BR scraper
- `fd456162` Add DECODO_TOOLBOX.md — full test of all Decodo tools
- `35d2963a` v0.3.0: ML scraping working via Decodo Scraping API
- `659fe7ed` v0.2.0: +150 new products, 71 matches, 19 L1 categories
