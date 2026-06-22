# Changelog

All notable changes to arbt.ly (ArbitLens) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0 BETA] - 2026-06-22

### Added
- **Sales enrichment pipeline** (`scripts/enrich_amazon_sales.py`) — Decodo Scraping API + SU fallback
  - Amazon BR: 78→23 null sales (-70%)
  - Handles split-span HTML patterns (e.g. "10</span><span>mil")
  - Rate-limit aware (3x retries with exponential backoff)
- **Kitchen category** — 30 Amazon BR products scraped, 10 properly classified
  - L1: Cozinha, L2: Panelas/Utensílios/Eletrodomésticos, L3: specific types
- **L1 detection from title** (`detect_l1_from_title()`) — 60+ patterns
  - Restored missing iteration loop (was returning None silently)
- **30+ new L2/L3 categories**:
  - Brinquedos: Massinha, Livros, Festa, Coleção, Veículos, Sensory, Cubo Mágico
  - Pet Shop: Ração, Antipulgas, Areia Sanitária, Acessório
  - Casa: Banho, Cesto, Pote, Tapete de Entrada, Limpeza
  - Beleza: Maquiagem (Mascara, Eyeliner, Brow), Cabelo (Secador, Prancha), Barbearia
  - Bebê: Quarto (Swaddle, Toalha), Mobilidade (Canguru, Cadeira Alimentação), Alimentação
  - Audio: Som Automotivo, Caixa Amplificada, Boombox
  - Ferramentas: Soquetes, Chaveiro
  - Moda: Acessórios, Carteira
  - Auto: Acessórios Auto
  - Meias: Meia Calça, Cano Médio/Alto
  - Mochilas: Mochila, Capa

### Changed
- **Matching v7** (`scripts/matching_v7.py`) — 3-tier strictness (STRICT/MEDIUM/BROAD)
  - STRICT: L1 + L2 + L3 all match (93 matches)
  - MEDIUM: L1 + L2 match (4 matches)
  - BROAD: L1 only (8 matches, fallback)
- **categorize_products.py** — major refactor with detect_l1_from_title
- **Backend health endpoint** reports v0.2.0 (TODO: bump to v0.4.0)

### Fixed
- **`\b` → `\x08` encoding bug** — 28 word-boundary escapes corrupted to backspace
  - Affected: 1008 products with broken L1 detection
  - Restored: full L1 detection working
- **`\s+` pattern compatibility** — "Massa para Modelar" vs "Massa de Modelar" both supported
- **Deduplicated KEYWORD_RULES** — removed duplicate `(Beleza, Maquiagem)` and `(Beleza, Barbearia)` sections

### Statistics (v0.4.0 BETA)
| Metric | v0.3.2 | v0.4.0 BETA | Delta |
|---|---|---|---|
| Total products | 997 | 1008 | +11 |
| Products with L1 | 84.8% | 100% | +15.2% |
| Products with L2 | 84.5% | 100% | +15.5% |
| Products with L3 (no Geral) | 84.5% | 100% | +15.5% |
| "Geral" products | 156 | 0 | -100% |
| Total matches | 130 | 147 | +13% |
| BR↔ML matches | 105 | 105 | stable |
| BR↔US matches | 24 | 42 | +75% |
| Amazon BR with sales | 23% null | 23% null | stable |
| Amazon US with sales | 0% enriched | 30% enriched | +30% (US blocked) |
| L1/L2/L3 categories | 19/76/299 | 19/76/325+ | +26 L3 |

### Known Limitations
- **US sales enrichment FAILED** — both Decodo Scraping API and Site Unblocker returned 429 (rate-limited)
  - 90/301 Amazon US products still without sales_30d
  - Requires different IP pool or different proxy provider
- **Decodo Mobile** — 407 wrong password (not blocking critical paths)
- **"Geral" classification** — went from 156 to 0 via brute-force pattern matching
  - Some misclassifications likely (e.g., "Açomix Portão Pet" classified as Bebê but is Pet Shop)
  - LLM-based classification (Nous subscription, free) could refine further

### Architecture
- **Backend API** — FastAPI (production), serves 16 endpoints
- **Frontend** — vanilla HTML/CSS/JS (61KB), 4 main views
- **Database** — PostgreSQL `arbtbr` with pgvector for embeddings
- **Scraping** — Decodo (3 tools: Scraping API, Site Unblocker, Residential BR)
- **Matching** — CLIP embeddings (512-dim) + cosine similarity

## [0.3.2] - 2026-06-21

### Added
- 3-tier L1/L2/L3 matching — 130 matches (was 68)
- 3-level taxonomy: 19 L1, 76 L2, 299 L3

## [0.3.1] - 2026-06-21

### Added
- 3-level category taxonomy — L1 (19), L2 (76), L3 (299)
- 84.8% products with proper L1+L2+L3

## [0.3.0] - 2026-06-20

### Added
- Decodo Scraping API integration — solved ML scraping
- 49 new ML products (Beleza, Brinquedos, Bebê)

## [0.1.0] - 2026-06-08

### Added
- Initial release
- 3 sources: Amazon BR, Amazon US, Mercado Livre
- Basic scraping + CLIP matching
