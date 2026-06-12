# ARBITLENS
### See the arbitrage. Before everyone else.

---

**Cross-platform product intelligence for Brazilian e-commerce.**
Amazon BR ↔ Mercado Livre ↔ Amazon US — CLIP vision matching,
sales data, price tracking, confidence-scored matches.

---

## v0.1 — Current State (2026-06-12)

```
📦 1.207 produtos ativos
🏆 153 matches CLIP (≥70% similaridade)
💰 41% com dados de venda
📊 14 categorias | 3 plataformas
🔍 Matching: CLIP ViT-B-32 + pgvector
```

### Categorias

| Categoria | BR | US | ML | Total |
|-----------|----|----|----|-------|
| Acessórios Mobile | 20 | 15 | 64 | 99 |
| Audio | 130 | 64 | 121 | 315 |
| Bolsas | 1 | — | 37 | 38 |
| Casa | 31 | 30 | 91 | 152 |
| Esportes | 31 | 30 | 60 | 121 |
| Ferramentas | 100 | 33 | 30 | 163 |
| Fotografia | 31 | 30 | 6 | 67 |
| Iluminação | 35 | 30 | 23 | 88 |
| Meias | 8 | — | 2 | 10 |
| Mochilas | 1 | — | 9 | 10 |
| Moda | 15 | — | 39 | 54 |
| Moda Íntima | 5 | — | 1 | 6 |
| Praia | 12 | 9 | 21 | 42 |
| Wearables | 30 | 29 | 17 | 76 |

### Tech Stack

| Component | Tech |
|-----------|------|
| Backend | FastAPI (Python 3.11) |
| Frontend | Vanilla HTML/CSS/JS |
| Database | PostgreSQL 15 + pgvector |
| Embeddings | CLIP ViT-B-32 (512 dim) |
| Scraping | Decodo API (ML) + Hermes browser (Amazon) |
| Matching | pgvector cosine similarity, intra-L3 |
| Server | systemd, port 5000 |

---

## How It Works

1. **Scrape** — ML best sellers via Decodo API ($0.001/req), Amazon via browser
2. **Embed** — CLIP ViT-B-32 generates 512-dim vectors for product images
3. **Match** — pgvector cosine similarity, threshold 70%, dedup 1-to-1
4. **Track** — Daily price snapshots, sales data, match history

---

## Non-Negotiables

- Every product: image, sales data, price
- 3 sources: Amazon BR, Mercado Livre, Amazon US
- Decodo ALWAYS works — agent error when it "fails"
- All matches are CLIP-based (≥70%), no false positives
- Category L3 prevents cross-type matching

---

## Roadmap (v0.2)

- [x] 1.200+ products
- [x] 150+ matches
- [x] Fashion categories (Bolsas, Mochilas, Moda, Meias, Moda Íntima)
- [ ] 60%+ with sales data
- [ ] Automated sales pipeline (cron)
- [ ] New categories: Pet Shop, Cozinha, Jardim

---

## Quick Start

```bash
# Server
sudo systemctl start arbitlens-5000
# API
curl http://localhost:5000/api/stats
# Matching
.venv/bin/python3 scripts/matching_v6.py
# Data quality
.venv/bin/python3 scripts/data_quality_gate.py
```

**Server:** http://34.30.146.117:5000
**GitHub:** https://github.com/diogochubatsu/arbt.ly
