═══════════════════════════════════════════
  ARBITLENS — v0.4.1 (2026-06-25)
═══════════════════════════════════════════

Status: EM ANDAMENTO
Produtos: 1.079 (local) | 1.079 (ImportaSimples)
Matches: 154 (CLIP ViT-B-32, >=70%)
Categorias: 19 L1
Dados de venda: 95% (1.021/1.079)
Imagens: 100% (1.079)

Plataformas: Amazon BR (450) | ML (328) | Amazon US (301)
Servidor: http://136.111.212.52:5000

ImportaSimples:
  - Source: arbt.ly
  - bronze_products: 1.079
  - silver_categories_map: 19 mappings
  - Frontend: https://www.importasimples.com/inteligencia

Sprint 1 (2026-06-25 → 2026-06-27):
  - Corrigir created_by nos mappings
  - Corrigir platform amazon_us → amazon_usa
  - Corrigir source_product_id (remover prefixo arbt.ly:)
  - Documentar padrão source_product_id

Arquitetura:
  Agentes → bronze_products → PIPELINE → silver_products → Frontend
  NUNCA escrever em silver_products/silver_prices diretamente.

Próximo: Pipeline bronze→silver | Matching BR↔CN
