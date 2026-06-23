# Handoff para o Clone — Arbitlens V2

**Data:** 2026-06-09
**Status:** Sprint 1 COMPLETE ✅ — Trending Products Dashboard
**Commit base:** 1431826 — feat: arbitlens v2 — clean rebuild with lessons learned

## IMPORTANTE: V2, NÃO V1
V2 é uma rebuild limpa que descartou a abordagem V1.
- V1 descartado por 27% de acurácia no matching automatizado
- V2 = abordagem Helium 10 Black Box: ferramentas para o USUÁRIO decidir
- SEM match_scorer, SEM CLIP embeddings, SEM confidence scores

## Sprint 1 — Completo ✅

### O que foi feito
1. **Scrapers testados e corrigidos:**
   - Rakumart BR (1688/Taobao/Alibaba) — 50 produtos, preços BRL, vendas/mês ✅
   - DHgate — 40 produtos, preços USD. Bug de URL encoding corrigido ✅
   - Alibaba — 30 produtos, preços USD. Bug de URL encoding corrigido ✅

2. **search.py reescrito para V2** — scraping paralelo em 5 plataformas, retorna produtos planos ordenados por preço BRL. SEM matching, SEM confidence scores.

3. **Instrumentation simplificado** — removeu dependência `pg` que crashava o dev server.

4. **Frontend /arbitlens reescrito** — grid de cards com imagem, nome, badge da plataforma, preço BRL, vendas/mês. Tabs por plataforma. Ordenação por preço ou vendas. Em português.

5. **App rodando na porta 3001** — build passa, API funcional (~5.4s para 25 produtos em 5 plataformas).

### Problemas corrigidos
- `scrape_dhgate.py` e `scrape_alibaba.py`: URLs não codificavam espaços com `urllib.parse.quote_plus` → `http.client.InvalidURL`
- `src/instrumentation.ts`: importava `pg` que puxava `fs` → crash no webpack dev server. Simplificado para V2.
- `search.py`: importava `match_scorer` (arquivado no V1) e `CLIP embeddings` (descartado). Reescrito do zero.

## Plano V2 — Próximos Sprints

### Sprint 2: Image Search (Ctrl+V) — COMPLETE ✅
- Input de imagem: paste (Ctrl+V), drag-drop, upload via file picker
- Backend: Rakumart BR image pipeline (token → OSS → cross API) + fallback textual
- Grid de resultados visuais (reusa grid do Sprint 1)
- /api/arbitlens/image-search endpoint (POST, aceita file upload ou JSON com image_url)

Tasks:
- [x] Implement Rakumart BR image search API (3-step pipeline descoberto via reverse-engineering)
- [x] Implement Alibaba image search (via Rakumart BR cross API que busca em 1688)
- [x] Build image upload UI (Ctrl+V paste, drag-drop, file picker)
- [x] Build results page (reusa grid do Sprint 1)

### Sprint 3: Cross-Platform Price Comparison — COMPLETE ✅
- Botão "Comparar preços" em cada card de produto nos resultados
- Backend: extrai palavras-chave do título, busca em todas as outras plataformas
- Tabela de comparação: produtos agrupados por plataforma com checkboxes
- USUÁRIO decide matching (marca checkboxes para indicar mesmo produto)
- /api/arbitlens/compare endpoint (GET, aceita title + platform + k)

Tasks:
- [x] From trending/image search, click "Compare prices"
- [x] Search other platforms with product attributes
- [x] Show price comparison table
- [x] User decides if same product (no automated matching)

### Sprint 4: Production Polish
- Deploy Cloud Run, error handling, onboarding
- Docs e README atualizados

## Skills
- `arbitlens-v2` — skill principal do V2 (CARREGUE PRIMEIRO)
- `arbitlens-scraping` — scraping details e gotchas
- `rakumart-scraper` — Rakumart BR detalhes
- `dhgate-scraper` — DHgate scraper
- `marketplace-scraping` — class-level scraping knowledge

## Infraestrutura
- Git: origin → github.com/diogochubatsu/1688-intel.git
- Cloud Run: intel-dashboard-4766585081.us-central1.run.app
- GCP: leafy-flash-489319-c7
- DB: Cloud SQL intel_data
- VM: 34.30.146.117, app na porta 3001
- Hermes: perfil 1688-intel, OpenRouter deepseek

## Regras de Ouro
1. Não entregue features, entregue valor
2. Verifique no site real (clique nos links)
3. Acurácia > expansão (3 com 90% > 50 com 27%)
4. Evite matching automatizado — usuário decide
5. Commits atômicos por sprint
6. Docs atualizados sempre

## O Que NÃO Fazer
- NÃO construir multi-signal scorer (27% no V1)
- NÃO confiar em CLIP p/ matching automático
- NÃO expandir antes de validar
- NÃO deployar sem testar local
- NÃO ignorar o site real

## Como Validar
Para cada sprint: teste no navegador, clique nos links, confira preços, teste 5 casos, documente resultados.
