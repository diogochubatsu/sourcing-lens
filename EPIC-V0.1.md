═══════════════════════════════════════════════════════════════
  ARBITLENS v0.1 — TRÊS EPICS FUNDACIONAIS (FINALIZADO)
═══════════════════════════════════════════════════════════════

Data de fechamento: 2026-06-12
Produtos totais: 1.089 (420 BR / 270 US / 399 ML)
Matches: 234 (CLIP embeddings, intra-L3)
Categorias: 10 com match ativo

──────────────────────────────────────────────────────────────
EPIC A — Image Intelligence & Category Hierarchy  ✅ 90%
──────────────────────────────────────────────────────────────

Problema:
  Matching atual usa pHash (64 bits) + peso 80% imagem.
  Não há hierarquia de categoria — produtos de tipos diferentes
  (ex: microfone vs headphone) competem no mesmo pool.
  Sem embeddings, não há busca por similaridade visual real.

Solução:
  Embeddings visuais CLIP ViT-B-32 armazenados via pgvector.
  Categoria em 3 níveis (L1/L2/L3).
  Matching acontece APENAS dentro do mesmo L3.

Critérios de Aceite:
  [CA-A1] ✅ pgvector instalado e funcional no PostgreSQL
  [CA-A2] ✅ Coluna embedding vector(512) na tabela products
  [CA-A3] ✅ Dataset de validação: 30 pares conhecidos
  [CA-A4] ✅ CLIP vs SigLIP2 vs pHash testados e documentados
  [CA-A5] ✅ CLIP vence: 92% precision (vs SigLIP2 50%, pHash 70%)
  [CA-A6] ✅ Categorias migradas para 3 níveis (L1/L2/L3)
  [CA-A7] ✅ Matching engine: match APENAS intra-L3
  [CA-A8] ✅ Qualidade: Ferramentas 5/5 top matches corretos
  [CA-A9] ⚠️ Dashboard: sorting por confidence implementado

Métricas:
  - Precision@5: 92% ✅
  - Tempo query embedding: < 50ms ✅
  - Custo: ~$0 (modelo local, GPU-free)

──────────────────────────────────────────────────────────────
EPIC B — Sales Data Pipeline  ⚠️ 30%
──────────────────────────────────────────────────────────────

Problema:
  Maioria dos produtos sem dados de venda.
  Amazon: JS-renderizado (bloqueia scrapers).
  ML: Decodo HTML inconsistente, requer retry.

Solução:
  Pipeline existe (sales_pipeline.py) mas depende de proxy melhor
  para Amazon e Decodo para ML.

Critérios de Aceite:
  [CA-B1] ✅ Playwright instalado
  [CA-B2] ✅ Script de extração Amazon: browser navega + extrai
  [CA-B3] ✅ Script de extração ML: Decodo retry
  [CA-B4] ❌ 80%+ Amazon BR com sales_30d (atual: ~5%)
  [CA-B5] ❌ 80%+ Amazon US com sales_30d (atual: ~0%)
  [CA-B6] ❌ 80%+ ML best sellers com sales_30d (atual: ~18%)
  [CA-B7] ❌ Data quality gate ≥ 80%
  [CA-B8] ⚠️ Vendas no dashboard (parcial)

Nota: ML best sellers FUNCIONAM com Decodo. MLB263532 (Ferramentas)
retornou 18/18 produtos com vendas. O gargalo é escalar para todas
as categorias e contornar o bloqueio da Amazon.

──────────────────────────────────────────────────────────────
EPIC C — Scraping, Storage & Image Cache  ✅ 95%
──────────────────────────────────────────────────────────────

Problema:
  Imagens locais (504 produtos). 46 sem imagem.
  Scraper bloqueado na Amazon.

Solução:
  Browser para Amazon BR/US. Decodo para ML.
  Cache local + static mount + fallback remoto.
  Identificação autônoma de URLs de listas e categorias.

Critérios de Aceite:
  [CA-C1] ✅ 100% produtos ativos com image_urls válidas
  [CA-C2] ✅ 100% produtos com image_hash via CLIP embedding
  [CA-C3] ✅ Pipeline: Decodo retry 10x + browser fallback
  [CA-C4] ✅ Cache: /images/ static mount + FastAPI
  [CA-C5] ✅ Validação: imagens carregam
  [CA-C6] ✅ Sem placeholder no dashboard
  [CA-C7] ✅ Amazon: Hermes browser stealth (contorna captcha)

Aprendizado crítico:
  - ML best sellers (/mais-vendidos/MLB{id}) funcionam com Decodo
  - ML search (lista.mercadolivre.com.br) retornam JS shell
  - ML category (/c/{nome}) retornam produtos SEM vendas
  - Amazon BR/US best sellers funcionam com browser
  - Amazon US: /zgbs/{department} para best sellers de categoria
  - Amazon BR: /gp/bestsellers/{department}/{node_id}

──────────────────────────────────────────────────────────────
DEFINITION OF DONE — v0.1 ✅
──────────────────────────────────────────────────────────────

Checklist Final:
  [✅] EPIC A: Image Intelligence — 90% completo
  [⚠️] EPIC B: Sales Pipeline — 30% (MVP aceito para v0.1)
  [✅] EPIC C: Scraping & Cache — 95% completo
  [✅] Categoria de teste (Ferramentas) onboarded com sucesso
  [✅] Dashboard funcional com dados reais
  [✅] Pipeline de scraping autônomo para 3 plataformas
  [✅] CLIP embeddings + pgvector + intra-L3 matching
  [✅] 1089 produtos, 234 matches, 10 categorias

v0.1 encerrada em 2026-06-12.
Próximo: v0.2 — Sales Pipeline & Expansão de Categorias.
