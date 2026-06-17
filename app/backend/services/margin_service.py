"""
Margin Calculator Service
Computes landed cost and margin for selling a product on target platforms.
Uses import factors from the import_factors table.
"""
from typing import Optional
from models import MarginEntry
from database import get_cursor


# Default fallback factors if DB lookup fails
DEFAULT_FACTORS = {
    "BR": {1: 3.50, 51: 3.00, 201: 2.60, 501: 2.30},
    "US": {1: 2.80, 51: 2.30, 201: 2.00, 501: 1.80},
}

# Typical platform fees (percentage of sale price)
PLATFORM_FEES = {
    "ml": 0.16,            # Mercado Livre ~16%
    "amazon_br": 0.15,     # Amazon BR ~15%
    "amazon_us": 0.15,     # Amazon US ~15%
    "shopee": 0.10,        # Shopee ~10%
    "tiktok": 0.08,        # TikTok Shop ~8%
}

# Selling platforms and their typical currencies
SELL_PLATFORMS = [
    {"platform": "ml", "label": "Mercado Livre", "currency": "BRL"},
    {"platform": "amazon_br", "label": "Amazon BR", "currency": "BRL"},
    {"platform": "shopee", "label": "Shopee BR", "currency": "BRL"},
    {"platform": "amazon_us", "label": "Amazon USA", "currency": "USD"},
]


def load_import_factors() -> dict:
    """Load import factors from DB. Returns {country: {qty_min: factor}}."""
    factors = {}
    try:
        with get_cursor() as cur:
            cur.execute("SELECT country, quantity_min, factor FROM import_factors ORDER BY country, quantity_min")
            for row in cur.fetchall():
                country = row["country"]
                if country not in factors:
                    factors[country] = {}
                factors[country][row["quantity_min"]] = float(row["factor"])
    except Exception:
        return DEFAULT_FACTORS
    return factors if factors else DEFAULT_FACTORS


def get_factor(factors: dict, country: str, quantity: int) -> float:
    """Look up the import factor for a country/quantity. Uses the tier the quantity falls into."""
    country_factors = factors.get(country, factors.get("BR", {}))
    # Find the right tier
    applicable = 3.50  # default
    for qty_min in sorted(country_factors.keys()):
        if quantity >= qty_min:
            applicable = country_factors[qty_min]
    return applicable


def compute_margins(
    source_price: float,
    source_currency: str,
    sell_prices: list[dict],
    factors: Optional[dict] = None,
) -> list[MarginEntry]:
    """
    Compute margin for each selling platform.
    
    source_price: price on 1688/AliExpress in source currency
    source_currency: 'CNY' or 'USD'
    sell_prices: list of {platform, price, currency}
    """
    if factors is None:
        factors = load_import_factors()

    # Currency conversion (approximate for MVP)
    # These should ideally come from a rates API
    CNY_TO_USD = 0.14
    CNY_TO_BRL = 0.78
    USD_TO_BRL = 5.60

    # Normalize source to USD
    if source_currency == "CNY":
        source_usd = source_price * CNY_TO_USD
    elif source_currency == "USD":
        source_usd = source_price
    else:
        source_usd = source_price  # assume USD

    results = []
    
    # Test at two quantity tiers: 50 and 200
    for qty_label, qty in [("50 units", 50), ("200 units", 200)]:
        factor = get_factor(factors, "BR", qty)
        landed_usd = source_usd * factor
        
        for sp in sell_prices:
            sell_price = sp["price"]
            sell_currency = sp["currency"]
            platform = sp["platform"]
            
            # Convert landed cost to sell currency
            if sell_currency == "BRL":
                landed_local = landed_usd * USD_TO_BRL
            elif sell_currency == "USD":
                landed_local = landed_usd
            else:
                landed_local = landed_usd
            
            # Deduct platform fee
            fee_pct = PLATFORM_FEES.get(platform, 0.12)
            net_revenue = sell_price * (1 - fee_pct)
            
            # Margin
            if net_revenue > 0:
                margin_pct = (net_revenue - landed_local) / net_revenue
            else:
                margin_pct = 0.0
            
            results.append(MarginEntry(
                sell_platform=platform,
                quantity=qty,
                landed_cost_per_unit=round(landed_local, 2),
                sell_price=sell_price,
                margin_pct=round(margin_pct * 100, 1),
                currency=sell_currency,
                factor_used=factor,
                notes=f"Factor {factor}x includes shipping + import tax + handling",
            ))

    return results
