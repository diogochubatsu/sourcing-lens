#!/usr/bin/env python3
"""Unit tests for arbitlens modules."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_schema():
    """Test ArbitlensProduct schema."""
    from schema import ArbitlensProduct
    p = ArbitlensProduct(
        source_platform='test',
        source_product_id='123',
        source_url='https://example.com',
        product_name='Test Product',
        price_low=9.99,
        price_currency='USD',
    )
    assert p.source_platform == 'test'
    assert p.price_low == 9.99
    print("✓ Schema works")

def test_cn_pt_dict():
    """Test Chinese to Portuguese translation."""
    from cn_pt_dict import cn_to_pt, has_chinese, translate_if_chinese
    assert cn_to_pt('蓝牙耳机') == 'fone bluetooth'
    assert has_chinese('蓝牙耳机') == True
    assert has_chinese('test') == False
    assert translate_if_chinese('蓝牙耳机') == 'fone bluetooth'
    assert translate_if_chinese('test') == 'test'
    print("✓ CN→PT dictionary works")

def test_pt_cn_dict():
    """Test Portuguese to Chinese translation."""
    from pt_cn_dict import pt_to_cn, build_queries
    result = pt_to_cn('fone bluetooth')
    assert result is not None
    queries = build_queries('fone bluetooth')
    assert len(queries) == 2
    print("✓ PT→CN dictionary works")

def test_scoring():
    """Test scoring module."""
    from scoring import text_score, price_score, sales_score, composite_score, rank_results
    
    # Text scoring
    assert text_score('microfone', 'Microfone Lapela') == 100
    assert text_score('microfone', 'Caixa de Som') == 0
    
    # Price scoring
    assert price_score(10, 0, 100) > price_score(90, 0, 100)
    
    # Sales scoring
    assert sales_score(1000) > sales_score(10)
    
    # Composite scoring
    score = composite_score(80, 70, 60, 50)
    assert 60 < score < 80
    
    # Ranking
    results = [
        {'product_name': 'Microfone', 'price_brl': 29.99, 'monthly_sales': 500},
        {'product_name': 'Caixa', 'price_brl': 49.99, 'monthly_sales': 100},
    ]
    ranked = rank_results('microfone', results)
    assert ranked[0]['product_name'] == 'Microfone'
    print("✓ Scoring module works")

def test_cache():
    """Test API cache module."""
    from api_cache import cache_get, cache_set, cache_clear, cache_stats
    
    cache_clear()
    assert cache_get('test') is None
    
    cache_set('test', {'data': 123})
    assert cache_get('test') == {'data': 123}
    
    stats = cache_stats()
    assert stats['size'] == 1
    
    cache_clear()
    assert cache_get('test') is None
    print("✓ Cache module works")

if __name__ == '__main__':
    test_schema()
    test_cn_pt_dict()
    test_pt_cn_dict()
    test_scoring()
    test_cache()
    print("\n✅ All unit tests passed!")
