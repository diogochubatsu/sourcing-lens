# ArbitLens v1.0 — Production-Ready

**Data de release:** 2026-06-17
**Foco:** Quality baseline. Não expansão.

## Filosofia

Em vez de adicionar mais categorias e produtos, fechamos uma versão com dados **confiáveis**. Um usuário pode confiar que cada produto mostrado:
- Tem imagem real
- Tem evidência de vendas (BSR top-100 ou reviews)
- Foi pareado com SigLIP (modelo de visão > CLIP)

## Mudanças vs v0.2.1

| Métrica | v0.2.1 | v1.0 |
|---|---|---|
| Produtos ativos | 1,307 | **794** (-39%) |
| Sales data > 0 | 16% | **90%** (+74pp) |
| Image hash | 0% | **100%** |
| Embeddings | 99.8% | **100%** |
| Matches totais | 98 | **67** (limpos) |
| Avg confidence | 84% | **85%** |
| Falsos positivos | ~28 | ~6 (validados) |

## Pipeline de produção

### Imagem
- **Modelo:** SigLIP base (`google/siglip-base-patch16-224`, 768-dim)
- **Threshold:** 70% (sem override por categoria)
- **Filtro:** imagens < 150x150 px são descartadas
- **Hash:** SHA256 (primeiros 32 chars) por produto

### Sales enrichment
- **Amazon:** BSR rank → estimativa (top10=1000, top50=300, top100=100, top500=50)
- **ML:** sales_30d direto (regex "X vendidos")
- **Fallback:** review_count / 10

### Ativação de produtos
Critérios para `is_active=true`:
- Tem imagem válida
- E (sales_30d > 0 OU review_count > 0 OU bsr_rank > 0)
- E embedding não-nulo

513 produtos desativados (zero business signal):
- Sem sales
- Sem reviews
- Sem BSR
- Sem match

## Matches auditados e limpos

**Mantidos (67):** confidence ≥ 70% E produtos semanticamente similares

**Deletados (6 falsos positivos):**
1. Pet Shop: Milk-Bone ↔ Ração Golden (US dog treat vs BR dog food)
2. Pet Shop: Beef Liver ↔ Areia Sanitária (treat vs cat litter)
3. Pet Shop: Fresh Step Litter ↔ Ração Gatos (litter vs cat food)
4. Audio: MONDIAL ↔ JBL PartyBox (different brands)
5. Esportes: CarPlay adapter ↔ GPS tracker (different products)
6. Ferramentas: Kit brocas ↔ Furadeira (kit vs drill)

## Blockers conhecidos (não bloqueantes)

- **Decodo $0:** ML scraping via API bloqueado. Pet Shop e Cozinha têm dados parciais (sem US source).
- **Sales scraping Amazon direto:** BSR funciona, mas review_count e sales_30d direto requerem browser stealth (lento).
- **Pet Shop sem BR:** 0 matches (categoria só tem US + ML).

## Próximas versões

- v1.1: HTTPS + domínio arbt.ly (Caddy + Let's Encrypt)
- v1.2: User accounts (JWT já implementado)
- v1.3: Alertas de preço + best opportunities view
- v1.4: Decodo credit + ML completude (Pet Shop, Cozinha)

## Arquivos

- `scripts/generate_embeddings_v2.py` — SigLIP encoder (substitui v1)
- `scripts/sales_pipeline.py` — extract_sales regex (mantido)
- `scripts/matching_v6.py` — matching engine (mantido, threshold 70%)

## Database

- `products.embedding` agora `vector(768)` (era 512)
- 794 ativos, 604 inativos (archived)
- 67 matches ativos
- 13,625 price_history rows