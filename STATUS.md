# ArbitLens v0.2.0 — Status

## Data
- **944 active products** across **19 L1 categories**
- **402 Amazon BR** | **301 Amazon US** | **241 Mercado Livre**
- **71 matches** (85% avg confidence)
  - 65 BR↔ML (CLIP embeddings, threshold 70%)
  - 6 BR↔US (CLIP embeddings, threshold 70%)

## Categories
Audio (250), Iluminação (78), Wearables (75), Esportes (72), Fotografia (67),
Casa (64), Beleza (60, NEW), Brinquedos (60, NEW), Ferramentas (40),
Bolsas (37), Moda (36), Bebê (30 US, NEW), Acessórios Mobile (29),
Pet Shop (14), Praia (13), Mochilas (10), Meias (4), Cozinha (3), Moda Intima (2)

## Data Quality
- 100% image_hash
- 100% currency, url, title
- 99.7% embeddings (2 products with image too small)
- 91% have prices (83 missing: scraped from best-sellers page, BSR only)
- 82% have sales_30d (170 missing)

## API Endpoints (16)
- `GET /api/health` — health check
- `GET /api/stats` — top-level stats
- `GET /api/categories` — list all categories (cached 60s)
- `GET /api/categories/{l1}` — products by category
- `GET /api/products` — products with filters
- `GET /api/matches` — match list (with `include_br_us=true` for BR↔US)
- `GET /api/match-history/{match_id}` — price history for a match
- `GET /api/price-history` — price history
- `GET /api/price-drops` — products with recent price drops (cached 30s)
- `GET /api/cache-stats` — cache statistics
- `GET /product/{product_id}` — full product detail with cross-platform prices
- `GET /api/admin/scraper-health` — scraper run history
- `GET /api/admin/categories` — admin category management
- `GET /api/users`, `POST /api/users/login` — user endpoints

## Performance
- 10 DB indexes (category, sales, bsr, platform filters)
- Query time: <2ms for category filter, <1.5ms for matches join
- Response cache: 60s for /api/stats, /api/categories, 30s for /api/price-drops
- Hit rate visible in /api/cache-stats

## Scrappers
| Scraper | Status | Notes |
|---------|--------|-------|
| `scrape_amazon_bestsellers` | ✅ Working | Amazon BR + US, has stealth headers |
| `scrape_ml_best_sellers` | ❌ Blocked | Decodo $0, ML bot detection even with BR residential proxy |
| `decodo_site_unblocker` | ❌ Auth fail | "Incorrect username or password" |
| `firecrawl` | ❌ Invalid | 401 Unauthorized (both keys) |

## Known Issues
- 83 products have no price (best-sellers scrape gets BSR, not price)
- 170 products have no sales_30d (similar)
- 2 products have no embedding (DVD players with small images)
- Bebê has 30 US products but 0 BR (URL pattern unknown)
- Jardim never scraped (URL pattern not found)
- ML scraping blocked: needs paid Decodo Site Unblocker or alternative

## Database
- PostgreSQL 16 on localhost:5432
- Database: `arbtbr`
- User: `hermes1688`
- Tables: products, matches, price_history, scraper_health, users, etc.

## Git
- Branch: master
- Latest: see `git log --oneline -5`
