"""
arbitlens — Unified product schema for cross-marketplace matching.
All scrapers output ArbitlensProduct objects.
"""
from dataclasses import dataclass, asdict, field
from typing import Optional
import json
from datetime import datetime


@dataclass
class ArbitlensProduct:
    """Unified product schema across all marketplaces."""
    # Source
    source_platform: str            # 'dhgate', 'aliexpress', 'made-in-china', 'rakumart'
    source_product_id: str          # platform-specific ID
    source_url: str                 # full product URL
    
    # Product info
    product_name: str               # original title
    product_name_en: Optional[str] = None  # English translation if original is CN
    
    # Pricing
    price_low: Optional[float] = None      # lowest price in original currency
    price_high: Optional[float] = None     # highest price (if range)
    price_currency: str = "USD"            # USD, CNY, BRL
    price_cny: Optional[float] = None      # normalized to CNY for comparison
    
    # Seller
    seller_name: Optional[str] = None
    seller_id: Optional[str] = None
    seller_rating: Optional[float] = None
    seller_url: Optional[str] = None
    
    # Product details
    moq: Optional[int] = None              # minimum order quantity
    image_url: Optional[str] = None
    monthly_sales: Optional[int] = None
    review_count: Optional[int] = None
    rating: Optional[float] = None
    
    # Metadata
    category: Optional[str] = None
    description: Optional[str] = None
    scraped_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    raw_data: Optional[dict] = None        # full scraper output for debugging

    def to_dict(self):
        return asdict(self)
    
    def to_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def save_products(products: list, filepath: str):
    """Save list of ArbitlensProduct to JSON file."""
    data = [p.to_dict() for p in products]
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return len(data)


def load_products(filepath: str) -> list:
    """Load ArbitlensProduct list from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [ArbitlensProduct(**d) for d in data]


def print_summary(products: list, platform: str):
    """Print summary of scraped products."""
    print(f"\n{'='*60}")
    print(f"{platform}: {len(products)} products scraped")
    print(f"{'='*60}")
    for i, p in enumerate(products[:5], 1):
        price_str = f"${p.price_low}"
        if p.price_high:
            price_str += f" - ${p.price_high}"
        print(f"  {i}. {p.product_name[:70]}")
        print(f"     Price: {price_str} ({p.price_currency}) | MOQ: {p.moq} | Seller: {p.seller_name}")
        print(f"     Image: {p.image_url[:60] if p.image_url else 'N/A'}...")
    if len(products) > 5:
        print(f"  ... and {len(products) - 5} more")
