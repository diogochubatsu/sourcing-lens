#!/usr/bin/env python3
"""Platform Adapters — Stubs for additional platforms (Shopee, TikTok Shop).

These are placeholder implementations for future platform integration.
Each adapter follows the same interface:
  - search_products(query) -> list of products
  - get_best_sellers(category_id) -> list of products
  - get_product_details(product_id) -> product dict
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class BasePlatform:
    """Base class for platform adapters."""
    
    name = "base"
    
    def search_products(self, query, limit=20):
        """Search for products on the platform."""
        raise NotImplementedError
    
    def get_best_sellers(self, category_id, limit=50):
        """Get best sellers for a category."""
        raise NotImplementedError
    
    def get_product_details(self, product_id):
        """Get detailed product information."""
        raise NotImplementedError
    
    def normalize_product(self, raw_product):
        """Normalize product data to standard format."""
        return {
            'platform': self.name,
            'platform_id': raw_product.get('id', ''),
            'title': raw_product.get('title', ''),
            'price': raw_product.get('price', 0),
            'currency': raw_product.get('currency', 'BRL'),
            'url': raw_product.get('url', ''),
            'image_url': raw_product.get('image_url', ''),
            'sales_30d': raw_product.get('sales_30d'),
            'review_count': raw_product.get('review_count'),
            'review_avg': raw_product.get('review_avg'),
        }


class ShopeeAdapter(BasePlatform):
    """Shopee Brazil adapter.
    
    Status: NOT IMPLEMENTED
    Requires: Residential proxy (Shopee blocks datacenter IPs)
    
    API Documentation:
    - Search: https://shopee.com.br/api/v4/search/search_items
    - Best Sellers: https://shopee.com.br/api/v4/recommend/recommend?bundle=category_landing_page
    """
    
    name = "shopee_br"
    
    def __init__(self):
        self.base_url = "https://shopee.com.br"
        self.api_url = "https://shopee.com.br/api/v4"
    
    def search_products(self, query, limit=20):
        """Search Shopee for products."""
        print(f"[Shopee] Search not implemented: {query}")
        return []
    
    def get_best_sellers(self, category_id, limit=50):
        """Get Shopee best sellers."""
        print(f"[Shopee] Best sellers not implemented: {category_id}")
        return []
    
    def get_product_details(self, product_id):
        """Get Shopee product details."""
        print(f"[Shopee] Product details not implemented: {product_id}")
        return None


class TikTokShopAdapter(BasePlatform):
    """TikTok Shop adapter.
    
    Status: NOT IMPLEMENTED
    Requires: Kalodata ($46/mo) or residential proxy
    
    API Documentation:
    - Kalodata API: https://docs.kalodata.com/
    - TikTok Shop Seller API: https://partner.tiktokshop.com/docv2/page/6507ead7b99d5302be949ba9
    """
    
    name = "tiktok_shop"
    
    def __init__(self):
        self.base_url = "https://www.tiktok.com/shop"
        self.api_url = "https://seller.tiktokglobalshop.com/api"
    
    def search_products(self, query, limit=20):
        """Search TikTok Shop for products."""
        print(f"[TikTok] Search not implemented: {query}")
        return []
    
    def get_best_sellers(self, category_id, limit=50):
        """Get TikTok Shop best sellers."""
        print(f"[TikTok] Best sellers not implemented: {category_id}")
        return []
    
    def get_product_details(self, product_id):
        """Get TikTok Shop product details."""
        print(f"[TikTok] Product details not implemented: {product_id}")
        return None


# Platform registry
PLATFORMS = {
    'amazon_br': None,  # Uses existing scrape_amazon_bestsellers.py
    'amazon_us': None,  # Uses existing scrape_amazon_bestsellers.py
    'ml': None,         # Uses existing sales_pipeline.py
    'shopee_br': ShopeeAdapter(),
    'tiktok_shop': TikTokShopAdapter(),
}


def get_platform(name):
    """Get platform adapter by name."""
    return PLATFORMS.get(name)


def list_platforms():
    """List all available platforms."""
    return list(PLATFORMS.keys())


if __name__ == '__main__':
    print("Available platforms:")
    for name, adapter in PLATFORMS.items():
        status = "Implemented" if adapter is None else "Stub"
        print(f"  {name}: {status}")
