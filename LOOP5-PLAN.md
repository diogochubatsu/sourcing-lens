# LOOP 5 — Amazon BR Category Expansion + Movers & Shakers

## Goal
Expand Amazon BR product coverage to new categories (home, sports, etc.) and add Movers & Shakers as a trend source.

## DOD
- 3+ new categories added to category_ids.json
- Best sellers scraped for at least 2 new categories
- Movers & Shakers parser created and tested
- 40+ new products in DB
- Hygiene: temp files cleaned, dead scripts identified
- Skills: loop updated, amazon-br-scraping updated (if exists) or created

## Backlog

### T1 [🔧15min] Add new categories to category_ids.json (self)
- Browse Amazon BR to find category IDs for:
  - Home (17100533011 — user provided)
  - Sports (user provided zg_bs_nav_sports path)
  - Electronics subcategories we don't have
- Add to /mnt/ssd/arbitlens/scripts/category_ids.json
- DOD: category_ids.json has new entries with valid IDs and bestsellers_urls

### T2 [🏗️30min] Run best sellers scraper for new categories (delegate)
- Run: `python3 scripts/scrape_amazon_bestsellers.py --platform amazon_br --category home --dry-run`
- If dry-run looks good, run without --dry-run
- Same for sports category
- DOD: New products inserted in DB with category, price, image_hash, BSR

### T3 [🔧15min] Create Movers & Shakers parser (delegate)
- Read the existing best sellers scraper structure
- Create a new script or extend for https://www.amazon.com.br/gp/movers-and-shakers
- Parse: product title, ASIN, price, BSR change (% gain/loss), category
- Support --dry-run and --category flags like best sellers
- DOD: Script runs successfully, outputs parsed products

### T4 [⚡5min] Hygiene (self)
- Remove temp files from /tmp/
- Check for corrupted Python files
- Verify no duplicate products in DB
- DOD: All clean, zero issues

### T5 [⚡5min] Skills update (self)
- Update loop skill with refinements from this sprint
- Create/update amazon-br-scraping skill if data exists
- Save new category IDs to memory
- DOD: Skills patched, memory updated

## Critical Question
Should we stop trying to scrape ML categories that don't have best sellers pages?
→ YES. Focus on Amazon BR best sellers + Movers & Shakers. ML only for the 3 categories that work.
