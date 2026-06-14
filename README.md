# ARBITLENS
### See the arbitrage. Before everyone else.

---

**Cross-platform product intelligence for Brazilian e-commerce.**
Amazon BR ↔ Mercado Livre ↔ Amazon US — CLIP vision matching,
sales data, price tracking, confidence-scored matches.

---

## Tech Stack

| Component | Tech |
|-----------|------|
| Backend | FastAPI (Python 3.11) |
| Frontend | Vanilla HTML/CSS/JS |
| Database | PostgreSQL 15 + pgvector |
| Embeddings | CLIP ViT-B-32 (512 dim) via sentence-transformers |
| Scraping ML | Decodo Scraper API |
| Scraping Amazon | Hermes browser (stealth) |
| Matching | pgvector cosine similarity, intra-L3 |
| Auth | JWT + bcrypt |
| Server | systemd or Docker |

---

## Quick Start

### Docker (Recommended)

```bash
# Clone and configure
git clone <repo-url>
cd arbt.ly
cp config/.env.example config/.env
# Edit config/.env with your credentials

# Run
docker-compose up -d
```

### Manual

```bash
# Install dependencies
cd app/backend
pip install -r requirements.txt

# Configure environment
cp config/.env.example config/.env
# Edit config/.env with your credentials

# Run server
python main.py
```

---

## API Endpoints

### Products
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/products` | GET | List products with filters |
| `/api/products?category_l1=Audio` | GET | Filter by L1 category |
| `/api/products?platform=amazon_br` | GET | Filter by platform |
| `/api/products?has_sales=true` | GET | Only products with sales |
| `/api/categories` | GET | List all categories with counts |
| `/api/categories/{l1}` | GET | Detailed category stats |
| `/api/stats` | GET | Platform and category statistics |

### Matches
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/matches` | GET | List cross-platform matches |
| `/api/matches?sort_by=margin` | GET | Sort by margin |
| `/api/match-history/{id}` | GET | Price history for match |

### Alerts
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/alerts/price-drops` | GET | Recent price drops |
| `/api/alerts/top-matches` | GET | High-confidence matches |
| `/api/alerts/new-products` | GET | Recently added products |
| `/api/alerts/category-summary` | GET | Category overview |
| `/api/alerts/margin-analysis` | GET | Margin analysis by category |

### Admin
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/admin/categories` | GET | List category mappings |
| `/api/admin/categories/stats` | GET | Mapping statistics |
| `/api/admin/categories` | POST | Create/update mapping |
| `/api/admin/categories/discover` | GET | Auto-discover from URL |

### Auth
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/users` | POST | Create user |
| `/api/users/login` | POST | Login, get JWT |
| `/api/favorites` | GET/POST/DELETE | Manage favorites |
| `/api/health` | GET | Health check |

---

## Project Structure

```
arbt.ly/
├── app/
│   ├── backend/
│   │   ├── main.py            # FastAPI app entry point
│   │   ├── database.py        # Connection pool
│   │   ├── config.py          # Settings
│   │   └── routers/
│   │       ├── matches.py     # Match endpoints
│   │       ├── products.py    # Product endpoints
│   │       ├── users.py       # Auth endpoints
│   │       ├── alerts.py      # Alert endpoints
│   │       └── admin.py       # Admin endpoints
│   └── frontend/
│       └── index.html         # Dashboard UI
├── scripts/
│   ├── db.py                  # DB helper
│   ├── matching_v6.py         # CLIP matching engine
│   ├── sales_pipeline.py      # ML sales extraction
│   ├── daily_snapshot.py      # Price history recording
│   ├── data_quality_gate.py   # Data validation
│   ├── find_similar.py        # Similarity search
│   ├── scrape_amazon_bestsellers.py  # Amazon scraper
│   ├── scrape_best_sellers.py # Unified scraper
│   ├── category_mapper.py     # Category CRUD
│   ├── discover_categories.py # Auto-discover categories
│   ├── validate_mappings.py   # Validate mappings
│   ├── cluster_products.py    # CLIP clustering
│   ├── generate_embeddings.py # Generate embeddings
│   ├── run_pipeline.py        # Full pipeline runner
│   └── daily_pipeline.sh      # Cron script
├── migrations/
│   ├── 001_initial_schema.sql
│   └── 002_category_mappings.sql
├── config/
│   └── .env                   # Environment variables
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Category System

### Three-Level Hierarchy
- **L1 (Department):** Audio, Photography, Lighting, Tech, etc.
- **L2 (Category):** Microphones, Headphones, Tripods, etc.
- **L3 (Subcategory):** Lapela, Bluetooth, Celular, etc.

### Category Mappings
Maps internal categories to platform-specific categories:
```sql
SELECT * FROM category_mappings;
-- our_l1: Audio, our_l2: Microphones, our_l3: Lapela
-- platform: amazon_br, platform_category_id: 17095831011
-- platform: ml, platform_category_id: MLB3835
```

---

## Scripts

| Script | Purpose |
|--------|---------|
| `run_pipeline.py` | Full pipeline (scrape → embed → match) |
| `scrape_best_sellers.py` | Scrape from category mappings |
| `category_mapper.py` | CRUD for category mappings |
| `discover_categories.py` | Auto-discover from product URLs |
| `validate_mappings.py` | Validate mapping quality |
| `cluster_products.py` | CLIP-based clustering |
| `generate_embeddings.py` | Generate CLIP embeddings |
| `matching_v6.py` | Run matching engine |
| `daily_snapshot.py` | Record daily price history |
| `daily_pipeline.sh` | Cron script for daily runs |

---

## Running the Pipeline

```bash
# Full pipeline
python3 scripts/run_pipeline.py --all

# Scrape only
python3 scripts/run_pipeline.py --scrape

# Generate embeddings
python3 scripts/generate_embeddings.py --limit 500

# Match products
python3 scripts/matching_v6.py

# Daily cron
0 9 * * * /home/hermeshideki/arbt.ly/scripts/daily_pipeline.sh
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DB_HOST` | PostgreSQL host |
| `DB_PORT` | PostgreSQL port |
| `DB_USER` | Database user |
| `DB_PASSWORD` | Database password |
| `DB_NAME` | Database name |
| `JWT_SECRET_KEY` | JWT signing secret |
| `DECODO_USER` | Decodo API username |
| `DECODO_PASS` | Decodo API password |

---

## License

Private repository.
