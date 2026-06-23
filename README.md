# ArbitLens — Cross-Marketplace Product Intelligence

## Status

**V3.1** — Frontend redesign (Sprint 1), GCP deployment, 4-level taxonomy, CLIP visual matching (Jun 2026)

## What It Does

Search products across Chinese marketplaces, show prices in BRL, compare across platforms, and discover sourcing opportunities for Brazilian Mercado Livre sellers.

## Access

- **Production:** https://arbitlens-v2-820365145375.us-central1.run.app
- **Local:** http://localhost:3002

## Current State

| Metric | Value |
|--------|-------|
| Products | 13,508 |
| CLIP Embeddings | 12,608 (93%) |
| Cross-platform Matches | 1,441 (84% avg confidence) |
| N1 Classification | 80.3% |
| N2 Classification | 65.6% |
| N3 Classification | 30.1% |
| Taxonomy Categories | 435 (19 N1, 89 N2, 162 N3, 32 N4) |
| API Endpoints | 45 |
| Tests | 9 |

## Scraping Sources

| Marketplace | Method | Status | Products |
|-------------|--------|--------|----------|
| Rakumart 1688 | Direct API | ✅ Works | 2,614 |
| Rakumart Alibaba | Direct API | ✅ Works | 2,714 |
| Rakumart Taobao | Direct API | ✅ Works | 2,428 |
| DHgate | Direct scraping | ✅ Works | 4,731 |
| Alibaba | Decodo Site Unblocker | ✅ Works | 915 |
| 1688 | Direct | ❌ CAPTCHA blocked | 1 |

## Tech Stack

- **Frontend:** Next.js 15, React 18, Tailwind CSS
- **Backend:** Node.js (API routes), Python (scrapers, ML)
- **Database:** PostgreSQL + pgvector (Cloud SQL)
- **ML:** CLIP (openai/clip-vit-base-patch32) for visual similarity
- **Infrastructure:** Cloud Run, Cloud Storage, Cloud SQL

## Architecture

```
Cloud Run (arbitlens-v2)
  ├── PostgreSQL (Cloud SQL) — Products, matches, taxonomy
  ├── Cloud Storage — Images, backups
  └── Secret Manager — Credentials

Frontend (Next.js)
  ├── /arbitlens — Search + product grid + taxonomy browser
  ├── /arbitlens/product/[id] — Product detail + visual matches
  └── /arbitlens/categories — 4-level taxonomy drill-down

Backend (Node.js API)
  ├── /api/arbitlens/search — Multi-platform search
  ├── /api/arbitlens/taxonomy — Category tree
  ├── /api/arbitlens/visual-match — CLIP similarity
  ├── /api/arbitlens/compare-v2 — Hybrid matching
  ├── /api/arbitlens/opportunities — Sourcing opportunities
  └── /api/arbitlens/price-history — Price tracking

Python Scrapers
  ├── scrape_rakumart_br.py — Rakumart (1688/Taobao/Alibaba)
  ├── scrape_dhgate.py — DHgate
  ├── scrape_alibaba_direct.py — Alibaba via Decodo
  ├── search.py — Parallel search orchestrator
  └── match_pg.py — pgvector similarity search
```

## What's Next

1. **Frontend Sprint 2** — Product detail, categories, compare panel
2. **Infrastructure** — Redis cache, cron automation, performance
3. **N2 Classification** — Improve from 65.6% to 75%
4. **N3 Classification** — Improve from 30.1% to 40%
5. **Product Expansion** — Add 2,000+ more products
