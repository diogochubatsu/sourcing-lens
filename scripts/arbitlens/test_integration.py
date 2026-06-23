#!/usr/bin/env python3
"""Integration tests for arbitlens scrapers and classification."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_rakumart_scraper():
    """Test Rakumart scraper returns products with enriched fields."""
    from scrape_rakumart_br import search_rakumart_br
    products = search_rakumart_br('microfone', source='1688', page=1)
    assert len(products) > 0, "Rakumart scraper returned no products"
    p = products[0]
    assert p.source_platform == 'rakumart-1688'
    assert p.price_low is not None
    assert p.image_url is not None
    raw = p.raw_data or {}
    assert 'title_cn' in raw, "Missing title_cn in raw_data"
    assert 'trade_score' in raw, "Missing trade_score in raw_data"
    print("✓ Rakumart scraper works with enriched fields")

def test_dhgate_scraper():
    """Test DHgate scraper returns products."""
    from scrape_dhgate import scrape_dhgate
    products = scrape_dhgate('microfone')
    assert len(products) > 0, "DHgate scraper returned no products"
    p = products[0]
    assert p.source_platform == 'dhgate'
    assert p.price_low is not None
    print("✓ DHgate scraper works")

def test_classification():
    """Test classification system."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from classify_products import load_taxonomy, classify_product
    taxonomy, children = load_taxonomy()
    assert len(taxonomy) > 100, "Taxonomy too small"
    result = classify_product("Microfone蓝牙耳机", None, taxonomy, children)
    assert result['n1'] is not None, "Classification failed"
    print(f"✓ Classification works: {result['n1']}")

def test_search():
    """Test search returns products."""
    from search import search_all
    result = search_all('microfone', max_results_per_platform=1)
    assert result['total_products'] > 0, "Search returned no products"
    assert 'products' in result
    print(f"✓ Search works: {result['total_products']} products")

if __name__ == '__main__':
    test_rakumart_scraper()
    test_dhgate_scraper()
    test_classification()
    test_search()
    print("\n✅ All tests passed!")
