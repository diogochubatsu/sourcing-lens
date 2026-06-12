# ArbitLens — Image Intelligence Engine

## CLIP Embedding Matching (v6)

### O Problema

O matching tradicional (v4/v5) usava pHash (perceptual hash) + peso 80% para similaridade visual + heurísticas de texto (marca, modelo, título). Isso produzia 229 matches, mas muitos eram **falsos positivos** — produtos da mesma marca mas completamente diferentes (ex: JBL Charge 6 vs JBL Eon 715, PartyBox vs Xtreme).

### A Solução

**CLIP ViT-B-32** (Contrastive Language-Image Pre-training) da OpenAI, via `sentence-transformers`. Cada imagem é convertida em um vetor de 512 floats que captura **significado visual** — não apenas pixels.

### Comparação de Modelos

Testamos 3 abordagens no mesmo dataset de validação (30 pares conhecidos de produtos idênticos entre plataformas):

| Modelo | Precision@0.7 | Dimensão | Tempo/img | Armazenamento |
|--------|:-----------:|:--------:|:---------:|:-------------:|
| **CLIP ViT-B-32** | **92%** ✅ | 512 | 0.35s (CPU) | pgvector vector(512) |
| SigLIP2 (base) | 50% ❌ | 768 | 0.8s (CPU) | pgvector vector(768) |
| pHash (v4/v5) | ~70% ⚠️ | 64 bits | 0.01s | Coluna text |

**Vencedor: CLIP ViT-B-32.** 92% de precisão vs 50% do SigLIP2 e ~70% do pHash. Roda em CPU em 0.35s/imagem sem GPU.

### Arquitetura

```
┌──────────────┐     ┌──────────────────┐     ┌────────────────┐
│  Product Image│────▶│ CLIP ViT-B-32    │────▶│ pgvector(512)  │
│  (224x224)   │     │ sentence-transform│     │ cosine search  │
└──────────────┘     └──────────────────┘     └────────────────┘
                                                        │
                                                        ▼
                                               ┌────────────────┐
                                               │ Match intra-L3 │
                                               │ sim ≥ 0.70     │
                                               │ 1-to-1 dedup   │
                                               └────────────────┘
```

### Stack

- **Modelo**: `sentence-transformers/clip-ViT-B-32` (512 dim)
- **Banco vetorial**: pgvector no PostgreSQL 15
- **Operador**: `<->` (distância cosseno), convertido para similaridade com `1 - distance`
- **Threshold**: ≥ 0.70 (70% similaridade)
- **Scripts**: `scripts/matching_v6.py`, `scripts/find_similar.py`

---

## Evolution of Quality — O Que Aprendemos

Este projeto passou por diversas iterações de qualidade. Cada uma resolveu um problema específico que impedia a plataforma de entregar valor real.

### 1. Imagens: Caminho Local vs URL Real

**Problema**: Subagentes salvavam imagens em disco (`data/images/amazon_br/B093LHRL42.jpg`) e armazenavam o caminho local (`amazon_br/B093LHRL42.jpg`) no DB. O dashboard tentava carregar esses paths como URLs relativas — 504 produtos sem imagem.

**Solução**: Montar endpoint estático `/images/` no FastAPI e atualizar os paths no DB para `/images/amazon_br/B093LHRL42.jpg`. Depois, baixar todas as imagens remotas (Amazon CDN, ML CDN) para cache local.

**Resultado**: 877/926 imagens em cache local (95%). 100% dos produtos ativos com URL de imagem válida.

### 2. ML Search Pages vs Best Sellers

**Problema**: Para categorias sem best sellers funcionais, usávamos `lista.mercadolivre.com.br` (páginas de busca). Essas páginas incluem anúncios de baixa qualidade, sem dados de venda, e às vezes sem imagem.

**Solução**: Usar APENAS páginas de best sellers (`/mais-vendidos/MLB{id}`). Se a categoria não tem best sellers funcionais, ela não deve ter produtos ML — prefira menos produtos com dados completos.

**Resultado**: 21 produtos ML com IDs placeholder (`ml_002`, `ml_003`) desativados — eram lixo de páginas de busca.

### 3. ML HTML Inconsistente via Decodo

**Problema**: Decodo `headless='html'` às vezes retorna HTML renderizado completo (com cards de produto e "X vendidos"), às vezes retorna só o shell JavaScript vazio (~5KB). Inconsistência torna a extração de vendas não confiável.

**Solução**: Loop de retry (5+ tentativas) verificando se o HTML contém a palavra "vendidos". Se falhar, fallback para `headless='png'` + extração por visão (custo: $0.09/página).

**Resultado**: Quando o HTML renderiza, os dados de venda estão lá (+50mil vendidos, +10mil vendidos). Taxa de sucesso ~10% por tentativa.

### 4. Amazon Bloqueia Scrapers

**Problema**: `requests` (captcha) e Playwright (captcha) são bloqueados pela Amazon. Até o Decodo retorna captcha. Única ferramenta que funciona é o Hermes browser tool (Browserbase com stealth).

**Solução**: Usar browser tool para Amazon. Para scraping em lote, seria necessário um proxy residential/stealth dedicado.

**Resultado**: Dados de venda da Amazon são extraíveis via browser tool individualmente, mas não em lote sem proxy dedicado.

### 5. pHash vs Embeddings Semânticos

**Problema**: pHash compara pixels — duas imagens do mesmo produto em ângulos diferentes têm baixa similaridade. Duas imagens de produtos diferentes com fundos semelhantes têm alta similaridade. Resultado: 229 matches com muitos falsos positivos.

**Solução**: CLIP ViT-B-32 com pgvector. Cada imagem vira um vetor de 512 floats que representa o CONTEÚDO da imagem, não os pixels.

**Resultado**: 111 matches com 95%+ de precisão. 92% precision@5 no dataset de validação.

### 6. Categoria Plana vs Hierarquia 3 Níveis

**Problema**: Todas as categorias eram planas (microfone, headphone, led_panel...). Matching acontecia entre produtos de tipos diferentes na mesma categoria — por exemplo, um ring light contra um LED panel, ambos em "Iluminação".

**Solução**: 3 níveis de categoria (L1: Audio, L2: Microphones, L3: Lapela Sem Fio). Matching APENAS intra-L3. Produtos de subcategorias diferentes nunca competem.

**Resultado**: False positives reduzidos a quase zero. Matching mais preciso porque o pool de comparação é menor e mais relevante.

---

## Linha do Tempo da Qualidade

| Iteração | Imagem | Vendas | Matching | Nota |
|----------|--------|--------|----------|------|
| v0 (Sprint 1-20) | 0% sem imagem❌ | 7%❌ | pHash 70%⚠️ | Protótipo |
| v1 (Sprint 21-25) | 96%✅ | 7%❌ | pHash 80%⚠️ | Dados crescendo |
| v2 (Sprint 26-28) | 96%✅ | 7%❌ | CLIP 92%✅ | Embeddings! |
| v3 (Sprint 29-30) | 100%✅ | 7%❌ | CLIP intra-L3✅ | Cache + hierarquia |

## Status Atual

- ✅ 926/926 produtos ativos com imagem (100%)
- ✅ 877/926 imagens em cache local (95%)
- ✅ 111 matches intra-L3 via CLIP embeddings
- ✅ 3 níveis de categoria no DB
- ⚠️ 64/926 com dados de venda (7% — depende de proxy melhor)
