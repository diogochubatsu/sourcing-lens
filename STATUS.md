# ArbitLens v0.3.0 — Status

## Data
- **993 active products** across **19 L1 categories**
- **402 Amazon BR** | **301 Amazon US** | **290 Mercado Livre** (was 241, +49 new)
- **82 matches** (85% avg confidence)
  - 70 BR↔ML (CLIP embeddings, threshold 70%)
  - 12 BR↔US (CLIP embeddings, threshold 70%)

## New This Version (ML Scraping)
- **ML scraper working** via Decodo Scraping API (U0000420946, balance OK)
- **49 new ML products** scraped:
  - Beleza: 19 (BR↔ML: 3 matches at 87%, 77%, 76%)
  - Brinquedos: 10 (BR↔ML: 2 matches at 88%, 80%)
  - Bebê: 20 (no BR, so no BR↔ML matches; BR↔US: 0)
- New category depth: Beleza, Brinquedos, Bebê all now have 3-platform coverage
- "Bebe" / "Bebê" inconsistency fixed in DB

## Categories
Audio (250), Beleza (79, NEW ML), Iluminação (78), Wearables (75),
Esportes (72), Brinquedos (70, NEW ML), Fotografia (67), Casa (64),
Bebê (50, NEW ML), Ferramentas (40), Bolsas (37), Moda (36),
Acessórios Mobile (29), Pet Shop (14), Praia (13), Mochilas (10),
Meias (4), Cozinha (3), Moda Intima (2)

## Data Quality
- 100% image_hash
- 99.8% embeddings (1 product: DVD player with small image)
- 92% have prices (still missing for Amazon best-sellers)
- 100% image_urls populated (all 3 platforms)

## Credentials
| Service | Status | Notes |
|---------|--------|-------|
| Decodo Scraping API | ✅ Working | U0000420946 - bypasses ML bot detection |
| Decodo Residential BR | ✅ Working | Nova Lima, BR |
| Decodo US Residential | ✅ Working | Chicago, US |
| Decodo ISP (AU) | ✅ Working | Canberra, AU |
| Decodo Mobile | ❌ 407 Auth fail | Wrong password |
| Decodo Site Unblocker | ❌ 401 Auth fail | Wrong username/password |
| Firecrawl v2 | ✅ Working | Both keys valid (api.firecrawl.dev/v2/scrape) |
| Firecrawl v0/v1 | ❌ Invalid | Use v2 instead |

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

## Scrappers
| Scraper | Status | Notes |
|---------|--------|-------|
| `scrape_amazon_bestsellers` | ✅ Working | Amazon BR + US, has stealth headers |
| `scrape_ml_decodo` | ✅ Working | NEW - Decodo Scraping API, parses JSON-LD embedded data |
| `scrape_ml_best_sellers` | ❌ Blocked | Old - direct curl, ML bot detection |
| `matching_v6.py` | ✅ Working | BR↔ML CLIP matching, per-category dedup |
| `matching_br_us.py` | ✅ Working | NEW - BR↔US matching for categories without ML |

## Known Issues
- 80 products have no price (best-sellers scrape gets BSR, not price)
- Bebê has 30 US + 20 ML = 50 products, but 0 BR (URL pattern unknown)
- Jardim never scraped (URL pattern not found)
- Match prices show 0 for Amazon (only BSR scraped, not product page)

## Database
- PostgreSQL 16 on localhost:5432
- Database: `arbtbr`
- User: `hermes1688`
- Tables: products, matches, price_history, scraper_health, users

## Secrets Storage
- `config/decodo_scraping.key` (gitignored) - Decodo API auth
- `config/decodo_br.key` etc. can be added similarly
- See `config/.env` for env var reference

## Git
- Branch: master
- Latest: see `git log --oneline -5`
