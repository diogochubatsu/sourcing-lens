#!/usr/bin/env python3
"""Unit tests for arbitlens scrapers and utilities."""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from schema import ArbitlensProduct
from cn_pt_dict import cn_to_pt, has_chinese, translate_if_chinese
from pt_cn_dict import pt_to_cn, build_queries
from cache import cache_get, cache_set, cache_clear
from phash import phash_int

# ─── Schema tests ───

def test_arbitlens_product_fields():
    p = ArbitlensProduct(
        source_platform='dhgate',
        source_product_id='123',
        source_url='https://example.com',
        product_name='Test Product',
        price_low=9.99,
        price_currency='USD',
    )
    d = p.to_dict()
    assert d['source_platform'] == 'dhgate'
    assert d['price_low'] == 9.99
    assert d['product_name'] == 'Test Product'
    print('✓ ArbitlensProduct schema works')

def test_arbitlens_product_optional_fields():
    p = ArbitlensProduct(
        source_platform='rakumart-1688',
        source_product_id='456',
        source_url='https://example.com',
        product_name='Test',
    )
    assert p.price_low is None
    assert p.seller_name is None
    assert p.monthly_sales is None
    print('✓ Optional fields default to None')

# ─── CN→PT translation tests ───

def test_cn_to_pt_basic():
    result = cn_to_pt('蓝牙耳机')
    assert result == 'fone bluetooth'
    print('✓ CN→PT basic translation works')

def test_cn_to_pt_mixed():
    result = cn_to_pt('新款蓝牙耳机无线')
    assert 'fone bluetooth' in result
    print('✓ CN→PT mixed text translation works')

def test_cn_to_pt_no_chinese():
    result = cn_to_pt('microfone lapela')
    assert result == 'microfone lapela'
    print('✓ CN→PT passes through non-Chinese text')

def test_has_chinese():
    assert has_chinese('蓝牙耳机') == True
    assert has_chinese('hello') == False
    assert has_chinese('hello 蓝牙') == True
    print('✓ has_chinese detection works')

def test_translate_if_chinese():
    assert translate_if_chinese('蓝牙耳机') == 'fone bluetooth'
    assert translate_if_chinese('test') == 'test'
    print('✓ translate_if_chinese works')

# ─── PT→CN translation tests ───

def test_pt_to_cn():
    result = pt_to_cn('fone bluetooth')
    assert result == '蓝牙耳机'
    print('✓ PT→CN translation works')

def test_build_queries():
    queries = build_queries('fone bluetooth')
    assert 'fone bluetooth' in queries
    assert '蓝牙耳机' in queries
    print('✓ build_queries works')

def test_pt_to_cn_no_match():
    result = pt_to_cn('xyznonexistent')
    assert result is None
    print('✓ PT→CN returns None for unknown terms')

# ─── Cache tests ───

def test_cache_roundtrip():
    cache_clear()
    cache_set("test_key", {"data": [1, 2, 3]})
    result = cache_get("test_key")
    assert result == {"data": [1, 2, 3]}
    cache_clear()
    print('✓ Cache roundtrip works')

def test_cache_miss():
    cache_clear()
    assert cache_get("nonexistent") is None
    print('✓ Cache miss returns None')

# ─── Phash tests ───

def test_phash_returns_int():
    # Create a simple 100x100 white image as bytes
    from io import BytesIO
    try:
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='white')
        buf = BytesIO()
        img.save(buf, format='PNG')
        h = phash_int(buf.getvalue())
        assert isinstance(h, int)
        print('✓ phash_int returns integer hash')
    except ImportError:
        print('⊘ PIL not available, skipping phash test')

# ─── Run all tests ───

if __name__ == '__main__':
    test_arbitlens_product_fields()
    test_arbitlens_product_optional_fields()
    test_cn_to_pt_basic()
    test_cn_to_pt_mixed()
    test_cn_to_pt_no_chinese()
    test_has_chinese()
    test_translate_if_chinese()
    test_pt_to_cn()
    test_build_queries()
    test_pt_to_cn_no_match()
    test_cache_roundtrip()
    test_cache_miss()
    test_phash_returns_int()
    print('\n✅ All tests passed!')
