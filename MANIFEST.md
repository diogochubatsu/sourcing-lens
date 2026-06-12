════════════════════════════════════════════
  ARBITLENS — MANIFEST MISSION v4
════════════════════════════════════════════

## Current State (2026-06-11)
Server:    ✅ systemd na porta 5000
Access:    http://34.30.146.117:5000
DB:        771 produtos, 171 matches, 9 categorias
Cron:      ✅ daily snapshot at 9:00
Matching:  threshold 50, imagem 80%, dedup 1-to-1

## Categorias (todas com matches ✅)
Categoria          BR    US    ML    BRvsML  BRvsUS  Total
──────────────────────────────────────────────────────────
headphone          32    30    29     20       4      24
microfone          38    12    27     20       4      24
phone_holder       20    15    55     19       7      26
sports             30    30    60     27       2      29
home_organization  30    30    91     19       1      20
led_panel          27    30    18     13       5      18
tripod             33    30    10      8       5      13
beach_towel_clip   12     9    21     12       0      12
ring_light         10     -    10      5       -       5

## Decodo
Token funcional com locale='pt-br' + premium pool.
Busca com nomes de produto específicos funciona (ex: "suporte celular mesa articulado").
Buscas genéricas retornam HTML vazio.
