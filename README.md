# ARBITLENS
### See the arbitrage. Before everyone else.

---

**Cross-platform product intelligence for Brazilian e-commerce.**
Amazon BR ↔ Mercado Livre ↔ Amazon US — CLIP vision matching,
sales data, price tracking, confidence-scored matches.

---

## Sumário

1. [Current State (v0.1)](#v01--current-state-2026-06-12)
2. [Data Pipeline](#data-pipeline)
3. [Vector Embedding Model](#vector-embedding-model)
4. [Data Modeling](#data-modeling)
5. [Matching Engine](#matching-engine)
6. [Database Schema](#database-schema)
7. [Scraping Architecture](#scraping-architecture)
8. [Non-Negotiables](#non-negotiables)
9. [Evolution Roadmap](#evolution-roadmap)

---

## v0.1 — Current State (2026-06-12)

```
📦 1.207 produtos ativos
🏆 153 matches CLIP (≥70% similaridade)
💰 41% com dados de venda
📊 14 categorias | 3 plataformas
🔍 Matching: CLIP ViT-B-32 + pgvector
💵 Custo scraping: ~$0.81/mês (Decodo)
```

### Categorias

| Categoria | Amazon BR | Amazon US | Mercado Livre | Total | Matches |
|-----------|-----------|-----------|---------------|-------|---------|
| Acessórios Mobile | 20 | 15 | 64 | 99 | 11 |
| Audio | 130 | 64 | 121 | 315 | 49 |
| Bolsas 🆕 | 1 | — | 37 | 38 | 1 |
| Casa | 31 | 30 | 91 | 152 | 13 |
| Esportes | 31 | 30 | 60 | 121 | 18 |
| Ferramentas | 100 | 33 | 30 | 163 | 16 |
| Fotografia | 31 | 30 | 6 | 67 | 4 |
| Iluminação | 35 | 30 | 23 | 88 | 13 |
| Meias 🆕 | 8 | — | 2 | 10 | 1 |
| Mochilas 🆕 | 1 | — | 9 | 10 | 1 |
| Moda 🆕 | 15 | — | 39 | 54 | 10 |
| Moda Íntima 🆕 | 5 | — | 1 | 6 | — |
| Praia | 12 | 9 | 21 | 42 | 7 |
| Wearables | 30 | 29 | 17 | 76 | 9 |
| **Total** | **444** | **256** | **507** | **1.207** | **153** |

---

## Data Pipeline

```
┌────────────────────────────────────────────────────────────┐
│                     DATA PIPELINE                           │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  SCRAPE                                                      │
│  ├── ML Best Sellers → Decodo API (headless=html)           │
│  │   → Retry 3-10x, premium proxy, locale pt-br             │
│  │   → $0.001/request, ~500 req/mês                        │
│  │                                                           │
│  ├── Amazon BR Best Sellers → Hermes Browser (stealth)      │
│  │   → Navega, espera render, extrai via JS console         │
│  │   → Selector: .zg-grid-general-faceout                   │
│  │                                                           │
│  └── Amazon US Best Sellers → Hermes Browser                │
│      → Formato: /zgbs/{department}                          │
│      → Mesmo selector do Amazon BR                          │
│                                                              │
│  CLASSIFY                                                    │
│  └── Título do produto → category_l1 / l2 / l3              │
│      → Regras: Casa split (Copos Térmicos/Cozinha/Org)      │
│      → Fashion split (Meias/Moda Íntima/Bolsas/Mochilas)    │
│                                                              │
│  EMBED                                                       │
│  └── CLIP ViT-B-32 → vector(512) via sentence-transformers  │
│      → Imagem principal do produto (image_urls[0])          │
│      → 0.35s/imagem em CPU                                  │
│      → Armazenado em products.embedding (pgvector)          │
│                                                              │
│  MATCH                                                       │
│  └── pgvector cosine similarity (<=> operator)              │
│      → Intra-L3 apenas (mesma subcategoria)                 │
│      → Threshold ≥ 0.70 (70% similaridade)                  │
│      → Dedup 1-to-1 (greedy best-first)                     │
│      → Armazenado em matches (product_a, product_b, score)  │
│                                                              │
│  TRACK                                                       │
│  └── Daily snapshot → price_history table                   │
│      → Preço, sales_30d, timestamp                          │
│      → Permite gráfico de evolução de preço no dashboard    │
│                                                              │
└────────────────────────────────────────────────────────────┘
```

### Custos Operacionais (v0.1)

| Item | Custo | Frequência |
|------|-------|------------|
| Decodo API (ML) | ~$0.81/mês | 500-600 req |
| Modelo CLIP | $0 (local, CPU) | — |
| Servidor VM | Incluso | — |
| PostgreSQL | $0 (local) | — |
| **Total** | **~$0.81/mês** | |

---

## Vector Embedding Model

### Modelo: CLIP ViT-B-32

| Parâmetro | Valor |
|-----------|-------|
| Modelo | `sentence-transformers/clip-ViT-B-32` |
| Dimensão | 512 |
| Storage | PostgreSQL pgvector `vector(512)` |
| Operador | `<->` (cosine distance) |
| Threshold | `>= 0.70` (70% similaridade) |
| Velocidade | ~0.35s/imagem em CPU |
| Precisão | **92%** no dataset de validação (30 pares) |

### Por que CLIP e não SigLIP2 ou pHash?

| Modelo | Precisão@0.7 | Falsos Positivos | Velocidade |
|--------|-------------|-------------------|------------|
| **CLIP ViT-B-32** | **92%** | Muito baixos | 0.35s |
| SigLIP2 | 50% | Altos | 0.40s |
| pHash (v4/v5) | ~70% | Moderados | 0.01s |

CLIP venceu em precisão com tolerância aceitável a falsos positivos.
O segredo está no **intra-L3 matching** — restringir a comparação
para produtos da mesma subcategoria elimina a maioria dos falsos
positivos que CLIP produziria em categorias genéricas.

### Como o embedding é gerado

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("clip-ViT-B-32")
img = Image.open(requests.get(url, stream=True).raw).convert('RGB')
emb = model.encode(img)          # numpy array 512-dim
emb_list = emb.tolist()          # Python list para pgvector
execute("UPDATE products SET embedding = %s::vector WHERE id = %s",
        (emb_list, product_id))
```

---

## Data Modeling

### Hierarquia de 3 Níveis (L1 / L2 / L3)

Produtos são categorizados em 3 níveis. O matching só acontece
**dentro do mesmo L3** — isso é o que elimina falsos positivos.

```
L1 (categoria)    L2 (subcategoria)    L3 (tipo específico)
──────────────────────────────────────────────────────────
Audio             Headphones           Bluetooth
                                        Com Fio
                  Microfones           Lapela Sem Fio
                                        Condensador

Casa              Copos Térmicos       Stanley Quencher
                                        Garrafa Térmica
                  Organização          Caixa Organizadora
                                        Cesto/Cabide
                  Cozinha              Potes Herméticos

Ferramentas       Ferramentas          Ferramentas
                  (mesmo L1/L2/L3 por   (categoria nova,
                   enquanto)            L3 genérico)

Moda              Bolsas               Bolsas
                  Mochilas             Mochilas
                  Meias                Meias
                  Moda Íntima          Moda Íntima
```

### L3 Split: o caso de Casa

**Antes:** Casa tinha 152 produtos misturados. CLIP matching
produzia falsos positivos como "Lixeira ↔ Stanley Quencher"
porque ambos são objetos cilíndricos visualmente.

**Depois:** Casa split em 3 L3s:
- `Copos Térmicos` → 97 produtos, matches só entre copos
- `Cozinha` → 2 produtos
- `Organização` → 12 produtos

Resultado: **zero falsos positivos** entre subcategorias.

### Colunas da Tabela Products

| Coluna | Tipo | Uso |
|--------|------|-----|
| `id` | SERIAL PK | Identificador único |
| `platform` | VARCHAR | `amazon_br`, `amazon_us`, `ml` |
| `platform_id` | VARCHAR | ASIN (Amazon) ou MLB ID (ML) |
| `title` | TEXT | Nome do produto |
| `price` | DECIMAL | Preço atual |
| `image_urls` | TEXT[] | URLs das imagens |
| `sales_30d` | INTEGER | Vendas nos últimos 30 dias |
| `category_l1` | VARCHAR | Categoria nível 1 |
| `category_l2` | VARCHAR | Categoria nível 2 |
| `category_l3` | VARCHAR | Categoria nível 3 (usada no matching) |
| `embedding` | VECTOR(512) | CLIP embedding da imagem principal |
| `url` | TEXT | URL do produto na plataforma |
| `is_active` | BOOLEAN | Produto ativo (não desativado) |
| `created_at` | TIMESTAMP | Data de inserção |
| `last_updated` | TIMESTAMP | Última atualização |

---

## Matching Engine

### v6 — CLIP Embedding (ATUAL)

```
BRUT:  Para cada produto Amazon BR na categoria L3:
         → Busca ML mais similar via pgvector (cosine)
         → Se score ≥ 0.70, adiciona à lista

DEDUP: Ordena por score decrescente
       → Pega melhor match (maior score)
       → Remove ambos da pool (1-to-1)
       → Repete até não haver mais pares

RESULT: 153 matches, todos CLIP, todos intra-L3
```

### Threshold por Tipo de Categoria

| Tipo | Threshold | Exemplo |
|------|-----------|---------|
| Produtos com marca | 0.70 | Audio (99% Philips, 98% Xiaomi) |
| Produtos genéricos | 0.80 | Ferramentas, Casa |
| Produtos novos | 0.70 | Moda, Bolsas |

### Histórico de Evolução

| Versão | Método | Matches | Precisão | Status |
|--------|--------|---------|----------|--------|
| v4 | pHash + texto (80% img) | 66 | ~60% | ❌ Deletado |
| v5 | pHash + texto (80% img) | 46 | ~50% | ❌ Deletado |
| v6 | CLIP ViT-B-32 + pgvector | 153 | **92%** | ✅ Atual |

---

## Scraping Architecture

### Mercado Livre — Decodo API

```json
POST https://scraper-api.decodo.com/v2/scrape
Authorization: Basic {base64(user:pass)}
{
  "url": "https://www.mercadolivre.com.br/mais-vendidos/MLB{id}",
  "headless": "html",
  "proxy_pool": "premium",
  "locale": "pt-br"
}
```

| MLB ID | Categoria | Funciona? |
|--------|-----------|-----------|
| MLB263532 | Ferramentas | ✅ |
| MLB3835 | Áudio | ✅ |
| MLB3813 | Acess. Celular | ✅ |
| MLB417704 | Smartwatches | ✅ |
| MLB1457 | Bolsas/Malas | ✅ |
| MLB3127 | Mochilas | ✅ |
| MLB108786 | Moda Íntima | ❌ (JS-rendered, usar browser) |
| MLB430391 | Moda Praia | ❌ (sempre vazio) |

### Amazon BR/US — Hermes Browser

Amazon bloqueia todos os scrapers programáticos (requests,
Playwright, Decodo). Único método que funciona: Hermes browser
(stealth mode).

```javascript
// Extracting products from best sellers page
const products = Array.from(
  document.querySelectorAll('.zg-grid-general-faceout')
).map(el => ({
  asin: el.querySelector('a[href*="/dp/"]').href.match(/\/dp\/([A-Z0-9]{10})/)[1],
  title: el.querySelector('img').getAttribute('alt'),
  price: el.textContent.match(/R\$\s*[\d.,]+/)[0],
  imgUrl: el.querySelector('img').getAttribute('data-a-hires') || 
          el.querySelector('img').getAttribute('src'),
}));
```

### ML Fashion — Estrutura Diferente

Moda no ML usa estrutura diferente:
- Selector: `div[class*="poly-card"]` (não `andes-card`)
- Links: `MLB-{number}` (não `/p/MLB{number}`)
- Preço: último `R$\s*[\d.,]+` no texto

---

## Non-Negotiables

1. **3 fontes obrigatórias**: Amazon BR, Mercado Livre, Amazon US
2. **Todo produto precisa**: imagem, preço, dados de venda
3. **Decodo SEMPRE funciona** — erro de scraping é erro do agente
4. **Sem global DELETE** na tabela de matches
5. **Matching só intra-L3** — mesma subcategoria
6. **Nunca dizer "amanhã"** — trabalho contínuo em loop

---

## Evolution Roadmap

### v0.1 ✅ (Completa)
```
[✅] CLIP embeddings + pgvector
[✅] 3-level category hierarchy (L1/L2/L3)
[✅] Intra-L3 matching (92% precisão)
[✅] 1.200+ produtos | 150+ matches
[✅] Scraping: Decodo ML + Browser Amazon
[✅] Dashboard com categorias, badges, histórico
[✅] 14 categorias (incluindo moda)
```

### v0.2 — Sales Pipeline & Expansão (Em andamento)
```
[✅] Fashion categories onborded (5 novas)
[⚠️] 41% com dados de venda (meta: 60%+)
[ ] Cron de scraping automático
[ ] Pipeline de vendas: ML best sellers → Decodo
[ ] Pipeline de vendas: Amazon BR → browser
[ ] Novas categorias: Pet Shop, Cozinha, Jardim
```

### v0.3 — Cross-Border CLIP (BR vs US)
```
[ ] Adaptar matching para amazon_br vs amazon_us
[ ] Amazon US como fonte de tendências e referência
[ ] Alertas de preço (BR vs US)
```

### v0.4 — Maturidade
```
[ ] 5.000+ produtos
[ ] 1.000+ matches
[ ] 80%+ com dados de venda
[ ] Alertas automáticos de arbitrage
[ ] Webhooks / notificações
```

---

## Quick Start

```bash
# Server
sudo systemctl start arbitlens-5000

# API
curl http://localhost:5000/api/stats

# Run matching for all categories
.venv/bin/python3 scripts/matching_v6.py

# Data quality audit
.venv/bin/python3 scripts/data_quality_gate.py

# Generate embeddings for new products
.venv/bin/python3 -c "
from scripts.db import query
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('clip-ViT-B-32')
products = query('SELECT id, image_urls FROM products WHERE embedding IS NULL')
for p in products:
    # ... generate and store embedding
"

# Find similar products (product ID 164)
.venv/bin/python3 scripts/find_similar.py --product-id 164

# Daily price snapshot
.venv/bin/python3 scripts/daily_snapshot.py
```

**Server:** http://34.30.146.117:5000
**GitHub:** https://github.com/diogochubatsu/arbt.ly
**Decodo:** ~$0.81/mês | 92.8% success rate | 566 requests
