/usr/bin/bash: warning: setlocale: LC_ALL: cannot change locale (pt_BR.UTF-8)
# ArbitLens v0.4.1 — Status

## Data
- **1,079 active products** across **19 L1 categories**
- **450 Amazon BR** | **301 Amazon US** | **328 Mercado Livre**
- **154 matches** (106 BR↔ML + 48 BR↔US)
  - CLIP embeddings, threshold 70%, 3-tier hierarchical matching
  - 88 strict (L1+L2+L3) | 3 medium (L1+L2) | 14 broad (L1 only)

## Category Taxonomy (v0.3.2)
- **3-level hierarchy**: L1 (19) → L2 (76) → L3 (299) — see `scripts/taxonomy.py`
- **100% products properly classified** (0 "Geral" products)
- Classifier (`categorize_products.py`): 60+ keyword rules (PT + EN) covering 16 L1

## Data Quality
- **Sales coverage:** 1,021/1,079 (95%)
- **Image coverage:** 100% (986 GCP + 93 CDN)
- **Price coverage:** 96.8%
- **Embedding coverage:** 91.8%

## ImportaSimples Production DB
- **Destination:** `34.170.210.220:5432/importasimples_products`
- **Source:** `arbt.ly` (NOT `arbitlens_brasil` — other agent)
- **Products:** 1,079 (all migrated)
- **Sales:** 1,021/1,079 (95%)
- **Images:** 986 GCP + 93 CDN = 100%
- **Scripts:** `migrate_to_importasimples.py`, `upload_images_to_gcp.py`
- **GCP SA:** `config/gcp-intel-images-writer.json`
- **Architecture:** bronze_products → PIPELINE → silver_products → Frontend
- **Rules:** NEVER write to silver_products/silver_prices directly

## Tools
- **Decodo Scraping API** (U0000420946) — ML best-sellers scraping ✅
- **Decodo Site Unblocker** (U0000434457) — Amazon BR + ML fallback ✅
- **Decodo Residential BR** (span5nxws5) — Amazon BR direct ✅
- **Decodo US Residential** (span5nxws5) — Amazon US enrichment ✅
- **Decodo ISP Static** (sp2idylm9q) — generic proxy ✅
- **Decodo Mobile** (spraglxgvk) — ❌ 407 auth fail
- **Firecrawl v2** (2 keys) — alternative scraping ✅

## Server
- **Port:** 5000 (systemd arbitlens-5000)
- **Public:** http://136.111.212.52:5000
- **Version:** 0.4.1

## Git
- **Branch:** master
- **Latest tag:** v0.4.0-beta
- **Repo:** https://github.com/diogochubatsu/arbt.ly
