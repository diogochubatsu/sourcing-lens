# Sourcing Lens — Cross-Marketplace Product Intelligence

Search products across Chinese marketplaces, compare prices, and discover sourcing opportunities for Brazilian sellers.

**Live:** https://arbitlens-v2-820365145375.us-central1.run.app  
**Data Warehouse:** https://arbitlens-v2-820365145375.us-central1.run.app/warehouse/  
**GitHub:** https://github.com/diogochubatsu/sourcing-lens

---

## Current State

| Metric | Value |
|--------|-------|
| Products | 13,508 |
| Platforms | 5 (1688, Taobao, Alibaba, DHgate, Alibaba Direct) |
| CLIP Embeddings | 12,608 (93%) |
| Cross-platform Matches | 1,441 |
| N1 Classification | 100% (19 categories + Uncategorized) |
| Taxonomy | 435 categories (19 N1 → 89 N2 → 162 N3 → 32 N4) |

---

## Features

- **Multi-platform search** — Search across 5 Chinese marketplaces simultaneously
- **Visual matching** — CLIP embeddings find similar products across platforms
- **4-level taxonomy** — Hierarchical product classification (N1→N4)
- **Price comparison** — See prices across platforms for the same product
- **Data warehouse** — Multi-dimensional filtering by category, platform, price, sales, match quality
- **Cross-platform clusters** — Same product found on multiple marketplaces

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Next.js 15, React 18, Tailwind CSS |
| Backend | Node.js (API routes), Python (scrapers, ML) |
| Database | PostgreSQL + pgvector (Cloud SQL) |
| ML | CLIP (openai/clip-vit-base-patch32) |
| Infrastructure | Cloud Run, Cloud SQL, Cloud Storage |

---

## Pages

| Page | URL | Description |
|------|-----|-------------|
| Dashboard | `/arbitlens` | Overview with stats, categories, products |
| Data Warehouse | `/warehouse/` | Multi-dimensional filtering |
| Search | `/arbitlens/search?q=` | Full-text search |
| Categories | `/arbitlens/categories` | 4-level taxonomy browser |
| Category Detail | `/arbitlens/categories/[slug]` | Products in category |
| Matches | `/arbitlens/matches` | Cross-platform matches |
| Clusters | `/arbitlens/clusters` | Same product across platforms |
| Product Detail | `/arbitlens/product/[id]` | Full product info |

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/arbitlens/explore` | GET | Multi-dimensional product query |
| `/api/arbitlens/search` | GET | Full-text search |
| `/api/arbitlens/taxonomy` | GET | Category tree |
| `/api/arbitlens/product` | GET | Product detail |
| `/api/arbitlens/stats` | GET | Platform statistics |
| `/api/arbitlens/matches` | GET | Cross-platform matches |
| `/api/arbitlens/clusters` | GET | Product clusters |

### Explore API Example

```
GET /api/arbitlens/explore
  ?category=audio
  &platform=rakumart-1688,rakumart-taobao
  &min_price=10
  &max_price=100
  &min_sales=50
  &min_match=0.80
  &sort=price_asc
  &page=1
  &limit=50
```

---

## Setup

### Prerequisites

- Node.js 18+
- Python 3.11+
- PostgreSQL 16 with pgvector extension
- GCP account (for Cloud Run deployment)

### Local Development

```bash
# Clone the repo
git clone https://github.com/diogochubatsu/sourcing-lens.git
cd sourcing-lens

# Install Node.js dependencies
npm install

# Create .env file
cat > .env << 'EOF'
DATABASE_URL=postgresql://user:password@localhost:5432/intel_data
EOF

# Start development server
npm run dev
```

The app will be available at http://localhost:3002

### Python Scripts Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Or install key packages manually
pip install psycopg2-binary numpy transformers torch pillow
```

### Database Setup

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE intel_data;

# Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

# Run migrations
psql -U postgres -d intel_data -f scripts/migrations/001_initial_schema.sql
```

---

## Deployment

### Google Cloud Run

```bash
# Set project
gcloud config set project project-18ce40b8-a806-441c-9c4

# Build and deploy
gcloud builds submit --config cloudbuild.yaml .

# Or deploy manually
gcloud run deploy arbitlens-v2 \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1
```

### Environment Variables (Cloud Run)

| Variable | Description |
|----------|-------------|
| `CLOUD_SQL_CONNECTION_NAME` | Cloud SQL instance connection name |
| `DB_USER` | Database username |
| `DB_PASS` | Database password |
| `DB_NAME` | Database name (default: intel_data) |

---

## Project Structure

```
sourcing-lens/
├── src/
│   ├── app/                    # Next.js pages
│   │   ├── arbitlens/          # Main app pages
│   │   │   ├── page.tsx        # Dashboard
│   │   │   ├── search/         # Search page
│   │   │   ├── categories/     # Category browser
│   │   │   ├── explore/        # Data warehouse
│   │   │   ├── matches/        # Cross-platform matches
│   │   │   ├── clusters/       # Product clusters
│   │   │   └── product/        # Product detail
│   │   └── api/arbitlens/      # API routes
│   ├── lib/                    # Shared utilities
│   └── components/             # React components
├── scripts/
│   ├── arbitlens/              # Python scrapers and ML
│   ├── classify_products.py    # Product classification
│   └── taxonomy_setup.py       # Taxonomy setup
├── public/
│   └── warehouse/              # Data warehouse frontend
├── Dockerfile                  # Docker configuration
├── cloudbuild.yaml             # GCP Cloud Build config
└── tailwind.config.ts          # Tailwind configuration
```

---

## Database Schema

### Core Tables

| Table | Description |
|-------|-------------|
| `arbitlens_products` | 13,508 products across 5 platforms |
| `arbitlens_matches` | 1,441 cross-platform matches |
| `taxonomy` | 435 categories (4 levels) |

### Product Fields

| Field | Description |
|-------|-------------|
| `platform` | Marketplace (rakumart-1688, rakumart-taobao, etc.) |
| `platform_id` | Original product ID |
| `title` | Product title |
| `price` | Price in BRL |
| `image_urls` | Array of image URLs |
| `image_embedding` | CLIP embedding (768-dim) |
| `category` | N1 category |
| `category_n2` | N2 subcategory |
| `category_n3` | N3 product type |
| `category_n4` | N4 niche |

---

## Key Scripts

| Script | Purpose |
|--------|---------|
| `scripts/classify_products.py` | Classify products into taxonomy |
| `scripts/expand_keywords.py` | Expand N2 keyword rules |
| `scripts/expand_n3_keywords.py` | Expand N3 keyword rules |
| `scripts/arbitlens/search.py` | Multi-platform search |
| `scripts/arbitlens/scrape_rakumart_br.py` | Rakumart scraper |
| `scripts/arbitlens/scrape_dhgate.py` | DHgate scraper |
| `scripts/arbitlens/match_pg.py` | pgvector similarity search |

---

## Classification System

The app uses a 4-level taxonomy for product classification:

```
N1: Audio (keyword) →
N2: Microphones (keyword + CLIP) →
N3: Wireless Lavalier (keyword + CLIP) →
N4: 2.4GHz (CLIP zero-shot)
```

### Coverage

| Level | Coverage | Method |
|-------|----------|--------|
| N1 | 100% | Keywords + CLIP fallback + Uncategorized |
| N2 | 66.5% | Keywords + CLIP fallback |
| N3 | 30.8% | Keywords + CLIP fallback |
| N4 | 0% | CLIP zero-shot (not implemented) |

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

---

## License

MIT
