---
name: 1688-intel-translator
description: Translation and localization conventions for the 1688-intel platform — PT/EN/ZH translations for product data, UI text, and documentation.
version: 1.0.0
metadata:
  hermes:
    tags: [1688, translation, localization, pt, en, zh]
---

# 1688-Intel Translator Skill

Translation and localization procedures for the 1688-intel platform.

## Translation Context

The 1688-intel platform deals with Chinese wholesale marketplace data that needs translation for Portuguese-speaking users (Brazil/Portugal).

## Translation Priorities

### High Priority (User-Facing)
1. **Product names** — Factory products, listing products
2. **Category labels** — Product categories (6 standardized categories)
3. **Supplier names** — Factory/supplier company names
4. **Region/City names** — Chinese locations to Portuguese
5. **UI text** — Dashboard labels, buttons, navigation

### Medium Priority (Data Layer)
1. **Specifications** — Technical specs (main_spec, specifications)
2. **Descriptions** — Product descriptions
3. **Search terms** — Portuguese search keywords

### Low Priority (Internal)
1. **Error messages** — System errors
2. **Logs** — Debug information
3. **Comments** — Code comments

## Translation Conventions

### Product Names
- Keep original Chinese name in parentheses when useful
- Use Portuguese market terminology
- Example: `Fone de Ouvido Bluetooth (蓝牙耳机)` 

### Categories
6 standardized categories (already translated):
1. `Eletrônicos` (Electronics)
2. `Roupas` (Clothing)
3. `Casa e Jardim` (Home & Garden)
4. `Esportes` (Sports)
5. `Beleza` (Beauty)
6. `Automotivo` (Automotive)

### Regions/Cities
- Use standard Portuguese transliteration
- Keep Chinese characters in data field for reference
- Example: `Guangzhou (广州)`

## Database Fields

### factory_products
- `category_label_pt` — Portuguese category label
- `region_city` — Region/city in Portuguese
- `main_spec` — Main specification (translate)
- `specifications` — JSON array of specs (translate each)

### ranked_suppliers
- `category_label_pt` — Portuguese category label
- `region_city` — Region/city in Portuguese

## Quality Standards

1. **Accuracy** — Technical terms must be precise
2. **Consistency** — Same term same translation throughout
3. **Naturalness** — Read like native Portuguese
4. **Context** — Consider Brazilian vs European Portuguese

## Common Patterns

### Batch Translation
```sql
-- Find untranslated entries
SELECT id, product_name, category 
FROM factory_products 
WHERE category_label_pt IS NULL OR category_label_pt = ''
LIMIT 100;
```

### Validation
```sql
-- Check translation coverage
SELECT 
  COUNT(*) as total,
  COUNT(CASE WHEN category_label_pt IS NOT NULL THEN 1 END) as translated,
  ROUND(COUNT(CASE WHEN category_label_pt IS NOT NULL THEN 1 END) * 100.0 / COUNT(*), 1) as pct
FROM factory_products;
```

## Tools

- **1688-scraping-agent** — Can fetch original Chinese text
- **Google Translate API** — For bulk translation (verify manually)
- **DeepL** — Higher quality for technical content
