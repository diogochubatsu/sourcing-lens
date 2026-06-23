---
name: 1688-intel-project
description: Project overview, architecture, and conventions for the 1688-intel platform — a data intelligence dashboard for 1688.com (Alibaba's B2B marketplace).
version: 1.0.0
metadata:
  hermes:
    tags: [1688, nextjs, postgresql, gcp, data-pipeline]
---

# 1688-Intel Project Overview

Data intelligence dashboard and web scraping platform for 1688.com (Alibaba's Chinese B2B wholesale marketplace).

## Quick Reference

| Item | Value |
|------|-------|
| Codebase | `/mnt/ssd/1688-intel` |
| GitHub Repo | https://github.com/diogochubatsu/1688-intel |
| Cloud Run URL | https://intel-dashboard-4766585081.us-central1.run.app |
| GCP Project | leafy-flash-489319-c7 |
| Region | us-central1 |
| Cloud SQL | intel-postgres (IP: 10.109.160.3) |
| Database | intel_data (PostgreSQL) |
| GCS Bucket | intel-dashboard-images-leafy-flash-489319-c7 |

## Tech Stack

- **Frontend:** Next.js 15 App Router, React 18, TypeScript, TailwindCSS
- **Database:** PostgreSQL (Cloud SQL)
- **Scraping:** Playwright, Puppeteer, Firecrawl, Decodo Site Unblocker
- **Storage:** Google Cloud Storage (image cache)
- **Deployment:** Docker, Cloud Run, GitHub Actions

## Project Structure

```
/mnt/ssd/1688-intel/
├── src/
│   ├── app/           # Next.js App Router pages
│   │   ├── dashboard/ # Main dashboard
│   │   ├── rankings/  # Rankings page
│   │   ├── products/  # Products listing
│   │   ├── factories/ # Factories page
│   │   ├── analysis/  # Analysis page
│   │   ├── bestsellers/ # Bestsellers
│   │   ├── reports/   # Reports
│   │   ├── enrich/    # Enrichment features
│   │   ├── suppliers/ # Suppliers page
│   │   ├── categories/ # Categories
│   │   └── api/       # API endpoints
│   ├── components/    # React components
│   ├── lib/           # Utilities and data queries
│   └── types/         # TypeScript types
├── scripts/           # Backfill and utility scripts
├── data/              # Data files
├── docs/              # Documentation
├── manifests/         # Infrastructure manifests
└── .github/workflows/ # CI/CD workflows
```

## Data Architecture

### Three-Layer Pipeline
1. **Bronze** — Raw JSON from 1688.com (stored as-is)
2. **Silver** — Normalized data
3. **Gold** — SQL tables (PostgreSQL)

### Key Tables
- `factory_products` — 18,467 rows; v1.5 enriched (main_spec, specs, models, variant_prices, video_url)
- `ranked_suppliers` — 904 rows; v1.4 enriched (category_label_pt)
- `listing_products` — 2,040 rows; bestsellers

### Data Pipeline Quirks
- 1688 `latest.json` files have a root `items` array
- Always use `data.items` and fallback to `shop_url`/`shop_name` for `supplier_key`
- `shop_id` is often null

## Design System

### Color Palette
- Background: `bg-stone-50`
- Cards: `bg-white rounded-2xl border border-stone-200 shadow-sm`
- Primary text: `text-ink` (custom, ~stone-900)
- Accent charts: `bg-amber-500`, `bg-emerald-500`, `bg-indigo-500`
- Badges: emerald (≥70%), amber (≥40%), red (<40%)

## Profile Roles

| Profile | Responsibility |
|---------|---------------|
| `1688devops` | Infrastructure, deployment, GCP, Docker, CI/CD |
| `1688front` | Frontend code, React, Next.js, UI/UX |
| `1688-scraping-agent` | Web scraping, data extraction, 1688.com |
| `1688-translator` | Translation, localization (PT/EN/ZH) |
| `orchestrator` | Decomposes work, routes to specialists via Kanban |

## Common Commands

```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Run tests
npm test

# Deploy to Cloud Run
gcloud run services replace manifests/cloudrun-service.yaml --region us-central1 --platform managed

# Check Cloud Run status
gcloud run services describe intel-dashboard --region us-central1
```
