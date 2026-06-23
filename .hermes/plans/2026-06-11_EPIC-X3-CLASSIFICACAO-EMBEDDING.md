# EPIC X3 — Classificação + Embedding Matching

**Data:** 2026-06-11  
**Status:** Planejado  
**Duração:** 4 sprints (S30-S33)  

---

## Tese Central

> Categorização em 3 níveis + matching por embedding = pipeline robusto.
> Dentro de uma subcategoria N3, produtos são naturalmente ~70% similares.
> A imagem serve pra refinar, não pra carregar o peso sozinha.

---

## Arquitetura Proposta

```
Busca textual → 200+ produtos crus (status quo)
    ↓
Classificador N1 → "Eletrônicos, Áudio, Vestuário..."
    ↓
Classificador N2 → "Carregadores, Microfones, Relógios..."
    ↓
Classificador N3 → "Power Banks, Lapela SEM Fio, Smartwatch..."
    ↓
SigLIP2 embedding → similaridade por cosseno
    ↓
Rank dentro da subcategoria N3 + preço
    ↓
Resultado final com score refinado
```

---

## DoD — Critérios de Aceite (por sprint)

### Sprint 30 — Setup: Modelos + Schema + Pipeline de Embedding

- [ ] **S30-1**: SigLIP2 instalado e funcional (`pip install transformers torch` ou similar)
- [ ] **S30-2**: Schema PostgreSQL + pgvector definido e migrado:
  - Tabela `products` com `embedding vector(768)`, `category_n1`, `category_n2`, `category_n3`
  - Índice IVFFlat para busca por similaridade
  - `updated_at` para refresh incremental
- [ ] **S30-3**: Pipeline de embedding funcional: dado um product_id, computa embedding e salva no DB
- [ ] **S30-4**: Lotes de 50 produtos embeddados em < 60s (CPU)
- [ ] **S30-5**: Alternativa testada: SQLite com `sqlite-vec` se PostgreSQL não estiver disponível (fallback)

**Critério de sucesso:** 100 produtos reais embeddados e armazenados, query de similaridade retorna em < 500ms.

---

### Sprint 31 — Classificador N1 + N2 (Categorias Macro)

- [ ] **S31-1**: Corpus de treino mínimo: 50 produtos por categoria N1 rotulados manualmente
- [ ] **S31-2**: Classificador N1 testado com 3 modelos: (a) zero-shot SigLIP2, (b) zero-shot CLIP, (c) LLM zero-shot
- [ ] **S31-3**: Acurácia mínima N1: **85%** (baseline)
- [ ] **S31-4**: Corpus de treino N2: 30 produtos por subcategoria
- [ ] **S31-5**: Acurácia mínima N2: **75%**
- [ ] **S31-6**: Pipeline: titulo + imagem → categoria → salva no DB
- [ ] **S31-7**: Fallback: se confiança < 50%, marca como `uncategorised` (não força)

**Critério de sucesso:** 200 produtos classificados N1+N2, acurácia validada manualmente em amostra de 50.

---

### Sprint 32 — Classificador N3 + Matching por Embedding

- [ ] **S32-1**: Classificador N3 com lista fechada de subcategorias (20-30)
- [ ] **S32-2**: Acurácia mínima N3: **70%**
- [ ] **S32-3**: Matching pipeline refatorado: busca candidatos APENAS dentro da mesma subcategoria N3
- [ ] **S32-4**: Similaridade: cosseno entre embeddings SigLIP2 (img + titulo)
- [ ] **S32-5**: Score final = similarity(embedding) * 0.7 + price_proximity * 0.2 + sales * 0.1
- [ ] **S32-6**: Query: `SELECT * FROM products WHERE category_n3 = ? ORDER BY embedding <=> ? LIMIT 10`
- [ ] **S32-7**: Tempo médio de matching: < 3s (contra 10-15s hoje)

**Critério de sucesso:** Matching K15 dentro de "Microfones > Lapela SEM Fio" retorna > 90% score.

---

### Sprint 33 — Validação + Comparação

- [ ] **S33-1**: Benchmark comparativo: pHash atual vs SigLIP2 vs CLIP vs DINOv2
- [ ] **S33-2**: Testar com 10 produtos reais de tipos diferentes:
  - 2 com modelo (K15, Q8)
  - 3 genéricos com imagem distinta (power bank preto, fone branco, capinha rosa)
  - 3 genéricos com imagem similar (2 power banks pretos, 2 fones brancos)
  - 2 aleatórios
- [ ] **S33-3**: Métrica: precision@5 (dos top 5 matches, quantos são realmente o mesmo produto?)
- [ ] **S33-4**: Métrica: recall@10 (dos produtos do mesmo tipo, quantos aparecem nos top 10?)
- [ ] **S33-5**: Se SigLIP2 < 80% precision@5, testar ensemble (SigLIP2 + CLIP)
- [ ] **S33-6**: Relatório final com recomendação de qual modelo usar

**Critério de sucesso:** precision@5 > 80% para produtos com modelo, > 60% para genéricos.

---

## Modelos a Testar (Sprint 33)

| Modelo | Tamanho | CPU? | Precisão esperada |
|---|---|---|---|
| **SigLIP2** (google/siglip2-base-patch16-512) | ~500MB | ✅ 1-2s/img | Melhor V+L atual |
| **CLIP** (openai/clip-vit-base-patch32) | ~300MB | ✅ 0.5s/img | Clássico, baseline |
| **CLIP** (openai/clip-vit-large-patch14) | ~700MB | ⚠️ 2-3s/img | Mais preciso |
| **DINOv2** (facebook/dinov2-base) | ~300MB | ✅ 1s/img | Bom para similaridade visual |
| **Nomic Embed Vision** | ~250MB | ✅ 0.8s/img | Embedding texto+visão unificado |

---

## Armazenamento

```sql
-- PostgreSQL (preferencial)
CREATE TABLE products (
    id TEXT PRIMARY KEY,
    source_platform TEXT NOT NULL,
    product_name TEXT,
    category_n1 TEXT,
    category_n2 TEXT,
    category_n3 TEXT,
    embedding vector(768),         -- SigLIP2
    embedding_model TEXT,          -- 'siglip2', 'clip', etc
    price_brl NUMERIC,
    image_url TEXT,
    metadata JSONB,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_products_n3 ON products(category_n3);
CREATE INDEX idx_products_embedding ON products 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

---

## O que NÃO está no escopo deste EPIC

- Classificador treinado fine-tune (zero-shot only por enquanto)
- Pipeline de crawl contínuo (embedding sob demanda por enquanto)
- Interface de labeling (rotulagem manual via JSON)
- OCR em imagens de produto
- Recomendação cross-categoria

---

## Riscos

1. **Performance CPU**: SigLIP2 em CPU pode ser lento demais (> 2s/img). Mitigação: testar CLIP base primeiro (0.5s/img).
2. **pgvector sem PostgreSQL**: Se DB remoto estiver inacessível, usar SQLite + `sqlite-vec` como fallback.
3. **Qualidade dos dados**: Categorias N3 precisam de curadoria manual inicial. Sem isso, classificação vai errar.
4. **Falso positivo intra-categoria**: Dentro de "Power Banks", dois produtos podem ter embeddings similares mesmo sendo marcas diferentes — mas isso é aceitável (score alto = mesmo tipo de produto).
