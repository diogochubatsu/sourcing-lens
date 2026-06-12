#!/usr/bin/env python3
"""Quick smoke tests for margins.py"""
import sys
sys.path.insert(0, '/mnt/ssd/arbitlens/scripts')
from margins import calculate_margin, calculate_margin_range, get_import_factor, convert_currency

# Test calculate_margin()
r = calculate_margin(source_price=15.00, source_currency='CNY', retail_price=149.90, platform='ml', quantity=200, country='BR')
assert r['margin_pct'] == 73.0, f"Expected 73.0 got {r['margin_pct']}"
assert r['import_factor'] == 3.0
assert r['platform_fee_rate'] == 0.11
print('OK: calculate_margin()')

# Test tier range
tiers = calculate_margin_range(source_price=15.00, source_currency='CNY', retail_price=149.90)
assert len(tiers) == 3
assert tiers[0]['quantity'] == 50
assert tiers[1]['quantity'] == 200
assert tiers[2]['quantity'] == 500
print('OK: calculate_margin_range()')

# Test factor lookup
f = get_import_factor('BR', 50)
assert f['factor'] == 3.50
f = get_import_factor('BR', 201)
assert f['factor'] == 2.60
f = get_import_factor('US', 100)
assert f['factor'] == 2.30
print('OK: get_import_factor()')

# Test currency conversion
assert convert_currency(100, 'CNY', 'BRL') == 80.0
assert convert_currency(100, 'USD', 'BRL') == 510.0
print('OK: convert_currency()')

# Test all platforms
for p in ['ml', 'amazon_br', 'shopee']:
    r = calculate_margin(source_price=15.00, source_currency='CNY', retail_price=149.90, platform=p)
    assert r['margin_pct'] > 0
print('OK: all platforms')

print()
print('ALL TESTS PASSED')
