/usr/bin/bash: warning: setlocale: LC_ALL: cannot change locale (pt_BR.UTF-8)
═══════════════════════════════════════════════════════════════
  ARBITLENS v0.2 — SALES PIPELINE & ONBOARDING EM MASSA
═══════════════════════════════════════════════════════════════

Início: 2026-06-12
Meta: 2.000+ produtos, 500+ matches, 60%+ com dados de venda

──────────────────────────────────────────────────────────────
EPIC D — Sales Pipeline (Prioridade Máxima)
──────────────────────────────────────────────────────────────

Problema: Apenas ~7% dos produtos têm sales_30d > 0.
Data quality gate bloqueia 93% por falta de vendas.

Solução:
- ML best sellers: Decodo já funciona (MLB263532 provado)
- Amazon BR: browser stealth extrai widget de vendas
- Pipeline automatizado que percorre TODAS as categorias

Categorias ML com best sellers conhecidos:
  MLB263532 — Ferramentas ✅ testado
  MLB270243 — Microfones
  MLB196208 — Headphones
  MLB430378 — LED Panels
  MLB1276 — Esportes
  MLB5672 — Acessórios para Veículos
  + encontrar IDs para Casa, Acessórios Mobile, Praia, etc.

Meta: 60%+ produtos com sales_30d > 0

──────────────────────────────────────────────────────────────
EPIC F — Onboarding em Massa
──────────────────────────────────────────────────────────────

Preencher lacunas nas categorias existentes + novas categorias.

Categorias existentes para completar:
  - Acessórios Mobile: falta Amazon BR (20) + US (15) - complementar
  - Casa: Amazon BR (31) pode expandir via browser
  - Esportes: Amazon US (30) ok, ML (60) forte
  - Praia: Amazon BR (12), US (9) - ambos podem expandir

Novas categorias:
  - Moda Íntima (lingerie, underwear)
  - Mochilas (backpacks, bags)
  - Bolsas (purses, handbags)
  - Meias (socks)
  - Pet Shop
  - Jardim
  - Cozinha
  - Saúde & Beleza

Critério de onboarding: ter best sellers acessíveis em ≥2 plataformas.

──────────────────────────────────────────────────────────────
Métricas de Sucesso v0.2
## Métricas de Sucesso v0.2

  [✅] 1.200+ produtos ativos (1.221)
  [✅] 150+ matches (156)
  [⚠️] 60%+ com sales_30d > 0 (41%)
  [✅] 15+ categorias (14)
  [✅] Moda íntima, mochilas, bolsas, meias onboarded
  [ ] Pipeline de vendas automatizado (cron)
