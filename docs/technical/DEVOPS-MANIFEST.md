# 1688-Intel DevOps Manifest

This directory contains the infrastructure-as-code manifests for the 1688-intel project.

## Components

### Cloud Run Service (`cloudrun-service.yaml`)
Kubernetes-style manifest for the `intel-dashboard` service on Google Cloud Run (GKE-based).

**Key specs:**
- Port: 3002
- Memory: 1Gi, CPU: 1
- Max instances: 2
- Health endpoints: `/health`, `/ready`
- Cloud SQL connection: `leafy-flash-489319-c7:us-central1:intel-postgres`
- Image: `us-central1-docker.pkg.dev/leafy-flash-489319-c7/intel-app/intel-dashboard:${{ github.sha }}`

**Environment variables:**
- Database: `CLOUD_SQL_CONNECTION_NAME`, `DB_USER`, `DB_NAME`
- Image cache: `IMAGE_CACHE_BUCKET`
- Decodo: Site Unblocker (`U0000398789`) + Residential (`spvgqh3ebj`)
- Secrets: `DB_PASS` (from `intel-postgres-password`), `API_KEY` (from `api-key`)

**Deploy with:**
```bash
gcloud run services replace manifests/cloudrun-service.yaml --region us-central1 --platform managed
```

---

### GitHub Actions Workflows (`.github/workflows/`)

#### `deploy.yml` — Main deployment
- Triggers: push to `master`, manual (`workflow_dispatch`)
- Builds Docker image, pushes to Artifact Registry
- Deploys to Cloud Run with all env vars + secrets
- Ensures GCS bucket exists, grants IAM to Cloud Run SA

#### `ci.yml` — Continuous Integration
- Runs TypeScript type check (`tsc --noEmit`)
- Runs tests if present
- Lints code

#### `deploy-gcs-fix.yml` — GCS bucket repair
- One-off workflow to fix GCS bucket IAM permissions
- Use when images return 403/404

---

### GCS Bucket
- Name: `intel-dashboard-images-leafy-flash-489319-c7`
- Purpose: Image cache (SHA256 hash of alicdn URL)
- Current: 11,635 objects, 2.51 GB
- Access: Public read via image proxy (`/api/images`)

---

### Cloud SQL (PostgreSQL)
- Instance: `intel-postgres`
- Database: `intel_data`
- User: `postgres`
- Key tables:
  - `factory_products` — 18,467 rows; v1.5 enriched (main_spec, specs, models, variant_prices, video_url)
  - `ranked_suppliers` — 904 rows; v1.4 enriched (category_label_pt)
  - `listing_products` — 2,040 rows; bestsellers

---

### Secrets (Secret Manager)
| Secret | Used By | Purpose |
|--------|---------|---------|
| `intel-postgres-password` | Cloud Run (DB_PASS) | PostgreSQL auth |
| `api-key` | Cloud Run (API_KEY) | API authentication |
| `decodo-siteunblocker-password` | Scraper (SU_PASS) | 1688 page fetch |
| `decodo-residential-password` | (reserved) | Future browser automation |

---

### Docker
- Dockerfile: `Dockerfile` (multi-stage, Node 20-alpine)
- Build context: `.`
- Entrypoint: `npm start` (Next.js start)
- Excluded: `data/`, `storage/`, `.env` (gitignored)

---

### Decodo Configuration
**Site Unblocker (API mode — used for scraping):**
- Endpoint: `unblock.decodo.com:60000`
- Auth: Basic (`SU_USER` / `SU_PASS`)
- Headers: `X-SU-Geo: China`, `X-SU-Locale: zh-cn`, `X-SU-Headless: html`
- Quota: 10 GB trial; ~0.5 GB used to date

**Residential Proxies (browser mode — NOT currently used):**
- Endpoint: `gate.decodo.com:10001–10010`
- Auth: HTTP Basic
- Use case: Puppeteer/Selenium (disabled to save quota)

---

### Current Data Status
**v1.5 Enrichment (factory products):**
- 6 standardized categories: 764 products
- Fully enriched: 706 (92.4%)
- With video: 576 (75.4%)
- Gaps: 58 (Site Unblocker timeouts/removed listings)

**v1.4 Backfills:**
- Ranking PT: 904/904 (100%)
- Factory PT: 18,467/18,467 (100%)
- Region/City: 12,003/18,467 (65%)  ← partial; prefix-only mapping

---

## Quick Reference

| Item | Value |
|------|-------|
| GitHub Repo | https://github.com/diogochubatsu/1688-intel |
| Cloud Run URL | https://intel-dashboard-4766585081.us-central1.run.app |
| GCP Project | leafy-flash-489319-c7 |
| Region | us-central1 |
| Cloud SQL | intel-postgres (IP: 10.109.160.3) |
| GCS Bucket | intel-dashboard-images-leafy-flash-489319-c7 |
| Decodo SU | U0000398789 (10 GB trial) |
| Decodo Residential | spvgqh3ebj (ports 10001–10010) |

---

*Last updated: 2026-05-01 by Hermes Agent*
