# Data Storage & Locations

**Last updated:** 2026-04-29

This document maps where every piece of project data lives — locally on the SSD, in the cloud, and what's tracked (or not) in git.

---

## 📁 Local Storage (SSD: `/mnt/ssd/1688-intel/`)

All project files live on the dedicated SSD mount. This is the **working directory** for development, scraping, and local database access.

### In Git (Tracked)

| Path | Purpose | Size |
|------|---------|------|
| `src/` | Next.js app source code + components | ~500 KB |
| `scripts/` | Python/TypeScript scraping & migration scripts | ~200 KB |
| `src/lib/scraper/` | Puppeteer scrapers (factory backfill) | ~8 KB |
| `.env.example` | Configuration template (commit this) | 1 KB |
| `README.md` | Project documentation | 50 KB |
| `ARCHITECTURE.md` | System design | 2 KB |
| `package.json`, `tsconfig.json` | Build configs | ~10 KB |

**Total tracked repo size:** ~760 KB (code only — no bulk data)

### Out of Git (Gitignored)

| Path | Purpose | Why excluded |
|------|---------|--------------|
| `.env` | Real credentials (Decodo, Firecrawl, DB password) | Secrets — must not commit |
| `data/` | Raw scraped data (HTML, JSON rankings, cookies) | Large, transient, contains PII |
| `storage/` | SQLite database + backups | Private data, large binary |
| `node_modules/` | NPM dependencies | Huge, reproducible via `npm install` |
| `.next/` | Next.js build output | Generated, reproducible |
| `.cache/` | Playwright/Chromium cache | Large, reproducible |

**Total untracked on SSD:** ~339 MB (`data/` 333 MB + `storage/` 5.9 MB)

---

## ☁️ Cloud Storage

| Service | What | URL / Connection |
|---------|------|------------------|
| **Cloud SQL (PostgreSQL)** | Primary production database | `10.109.160.3:5432/intel_data` |
| **Google Cloud Storage** | Image cache (proxied CDN) | `4766585081.appspot.com` |
| **Cloud Run** | Hosted Next.js app | `https://intel-dashboard-4766585081.us-central1.run.app/` |

The app reads from PostgreSQL (not SQLite) when deployed. Locally you can use SQLite (`storage/1688-intel.db`) for development, but **never commit it**.

---

## 🗄️ Data Directory Structure (`data/1688/`)

```
data/1688/
├── air/                    # AIR pipeline runs (rankings)
│   └── 2026-04-22T../      # timestamped runs
│       ├── air-products.json
│       └── raw/            # source HTML/AJAX responses
├── bestsellers/            # Bestseller pipeline runs
│   └── 2026-04-22T../
│       └── products.json
├── cache/                  # Local caches
│   └── title_cache.json
├── cookies.json            # Browser cookies for auth (gitignored)
├── cost_ledger_smart.jsonl # Smart scraper cost tracking (gitignored)
├── datalake/               # Firecrawl/bulk ingestion (already gitignored subdir)
│   └── factory-v2/
│       ├── enriched/
│       ├── manifest.json
│       └── raw/
├── rankings/               # v1.3 ranking pipeline outputs (legacy, gitignored)
│   ├── latest.json
│   └── 2026-04-08T../
├── scrape_log_decodo.jsonl # Site Unblocker fetch logs (gitignored)
├── titles-to-translate.json# Translation batch input (gitignored)
└── manual_review_decodo.txt# Failed Decodo fetches needing manual fix (gitignored)
```

> **Note:** All files in `data/1688/` are now **gitignored** after the 2026-04-29 cleanup. Only the directory structure (empty) remains untracked.

---

## 🗃️ Database Schema

### PostgreSQL (Production)
- **Host:** Cloud SQL (private IP) — `10.109.160.3`
- **Database:** `intel_data`
- **User:** `hermes1688`
- **Tables:**
  - `listing_products` — Bestsellers (~2K rows)
  - `ranked_suppliers` — Ranked suppliers with `top_products_json` (904 suppliers)
  - `factory_products` — Full factory catalog (~18.7K rows) — **enriched with specs, images, region/city**

### SQLite (Local Development)
- **Path:** `storage/1688-intel.db`
- **Status:** Gitignored — do not commit
- **Use case:** Local testing; sync to PostgreSQL via migration scripts
- **Backups:** `storage/1688-intel.db.backup-*` (also gitignored)

---

## 🔐 Secrets & Configuration

| Secret | Location | Git tracked? |
|--------|----------|--------------|
| `DECODO_USER` / `DECODO_PASS` (Residential proxy) | `.env` | ❌ No |
| `DECODO_SITEUNBLOCKER_USER` / `DECODO_SITEUNBLOCKER_PASS` | `.env` | ❌ No |
| `FIRECRAWL_API_KEY` | `.env` | ❌ No |
| `DATABASE_URL` (PostgreSQL) | `.env` | ❌ No |

Template: `.env.example` (committed — contains placeholders only)

---

## 🔄 Data Flow

```
Scraper (Selenium/Puppeteer + Decodo proxy)
    ↓
Raw HTML / JSON → data/1688/[pipeline]/[timestamp]/raw/
    ↓
Parsed → data/1688/[pipeline]/[timestamp]/*.json
    ↓
Ingest script → PostgreSQL (Cloud SQL) ← production app reads from here
    ↓
Local SQLite copy (storage/1688-intel.db) — for dev / backup only
```

---

## 💾 Backup Strategy

| Data | Backup method | Frequency |
|------|---------------|-----------|
| PostgreSQL | Cloud SQL automated exports → GCS bucket `gs://1688-intel-backups/` | Daily |
| `data/1688/` raw scrapes | Not backed up (transient) — re-scrape as needed | — |
| Local SQLite | Manual `.bak` files created before migrations | On-demand |
| Image cache | GCS with 30-day TTL + browser cache | Automatic |

**Recovery:** To rebuild local `data/1688/` from scratch, re-run the scraping pipelines. The PostgreSQL database is the single source of truth.

---

## 🧹 Cleanup Policy

- **Old ranking runs:** `data/1688/rankings/` contains historical runs — safe to delete after verifying latest pipeline worked
- **Datalake enriched files:** `data/1688/datalake/factory-v2/` – can be cleared and re-ingested from raw
- **Cookies:** Delete `data/1688/cookies.json` if sessions expire
- **Logs:** `data/1688/scrape_log_*.jsonl` – rotate or delete after review

Never delete:
- `storage/1688-intel.db` while local dev is active (unless you're restoring from backup)
- Any files in `data/1688/` that are currently being used by an in-progress pipeline

---

## 🚀 Migration Notes

### Before committing (if ever):**
1. Ensure `.env` is never committed (it's in `.gitignore`)
2. Ensure `data/` and `storage/` remain gitignored
3. Only commit code, config templates, and documentation

### To reset local dev database:**
```bash
rm storage/1688-intel.db
# Re-run ingest pipeline:
npx tsx scripts/ingest-factory.ts
```

### To clear scraped data:**
```bash
# Keep directory structure, delete contents
find data/1688 -type f -not -path "*/datalake/*" -delete
# Or selectively:
rm -rf data/1688/rankings/*
```
