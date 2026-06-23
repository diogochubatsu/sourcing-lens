#!/usr/bin/env python3
"""Populate category_l1/l2/l3 from flat category using hierarchy mapping."""
import sys, json
sys.path.insert(0, '.')
from scripts.db import query, execute

HIERARCHY_FILE = 'scripts/category_hierarchy.json'

with open(HIERARCHY_FILE) as f:
    hierarchy = json.load(f)

products = query("""
    SELECT id, category_l1, category_l2, category_l3
    FROM products WHERE is_active=true
""")

updated = 0
skipped = 0
missing = 0

for p in products:
    cat = p.get('category_l1', '')
    if not cat:
        missing += 1
        continue

    if p.get('category_l2') and p.get('category_l3'):
        skipped += 1
        continue

    mapping = hierarchy.get(cat)
    if not mapping:
        print(f'  WARN: No hierarchy for category "{cat}" (product {p["id"]})')
        missing += 1
        continue

    execute("""
        UPDATE products SET
            category_l1 = %s,
            category_l2 = %s,
            category_l3 = %s
        WHERE id = %s
    """, (mapping['l1'], mapping['l2'], mapping['l3'], p['id']))
    updated += 1

print(f'Updated: {updated}, Already set: {skipped}, Missing hierarchy: {missing}')
