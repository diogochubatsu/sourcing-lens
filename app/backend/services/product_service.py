from typing import Optional
from models import (
    ProductDetail, ProductResponse, PriceEntry, MatchResult,
    MarketPulse, MarginEntry,
)
from database import get_cursor
from services.margin_service import compute_margins
from services.verdict_service import compute_verdict


def get_product_detail(product_id: int) -> Optional[ProductResponse]:
    """
    Assemble full product detail response.
    Returns None if product not found.
    """
    with get_cursor() as cur:
        # 1. Get the product
        cur.execute("""
            SELECT id, platform, platform_id, title,
                   price, currency, url, image_urls,
                   sales_30d, review_count, review_avg,
                   category_l1, category_l2, category_l3, bsr_rank, is_active, last_updated
            FROM products
            WHERE id = %s
        """, (product_id,))
        
        row = cur.fetchone()
        if not row:
            return None
        
        product = _row_to_detail(row)
        
        # 2. Get cross-platform prices (from matches)
        cur.execute("""
            SELECT p.id, p.platform, p.platform_id, p.title, p.price, p.currency,
                   p.url, p.sales_30d, p.review_avg, p.is_active
            FROM products p
            JOIN matches m ON (
                (m.product_a_id = %s AND m.product_b_id = p.id)
                OR (m.product_b_id = %s AND m.product_a_id = p.id)
            )
            WHERE p.is_active = TRUE
            ORDER BY m.confidence DESC
        """, (product_id, product_id))
        
        price_rows = cur.fetchall()
        prices = [PriceEntry(
            platform=r["platform"],
            platform_id=r["platform_id"],
            price=float(r["price"]) if r.get("price") else 0.0,
            currency=r.get("currency") or "USD",
            url=r.get("url"),
            sales_total=r.get("sales_30d"),
            review_avg=float(r["review_avg"]) if r.get("review_avg") else None,
            is_active=r.get("is_active", True),
        ) for r in price_rows]
        
        # Also include the product itself in prices
        prices.insert(0, PriceEntry(
            platform=product.platform,
            platform_id=product.platform_id,
            price=product.price,
            currency=product.currency,
            url=product.url,
            sales_total=getattr(product, "sales_total", None) or 0,
            review_avg=product.review_avg,
            is_active=product.is_active,
        ))
        
        # 3. Get full match details (confidence-ranked)
        cur.execute("""
            SELECT p.id, p.platform, p.platform_id, p.title,
                   p.price, p.currency, p.url, p.image_urls,
                   m.confidence, m.match_method
            FROM products p
            JOIN matches m ON (
                (m.product_a_id = %s AND m.product_b_id = p.id)
                OR (m.product_b_id = %s AND m.product_a_id = p.id)
            )
            WHERE p.is_active = TRUE
            ORDER BY m.confidence DESC
            LIMIT 10
        """, (product_id, product_id))
        
        match_rows = cur.fetchall()
        matches = [MatchResult(
            product_id=r["id"],
            platform=r["platform"],
            platform_id=r["platform_id"],
            title=r["title"],
            title_translated=None,
            price=float(r["price"]) if r.get("price") else 0.0,
            currency=r.get("currency") or "USD",
            url=r.get("url"),
            image_urls=r.get("image_urls"),
            confidence=float(r["confidence"]),
            match_method=r.get("match_method") or "unknown",
            supplier_name=None,
            moq=None,
        ) for r in match_rows]
    
    # 4. Compute margins (only if product has a price)
    sell_prices = [
        {"platform": p.platform, "price": p.price, "currency": p.currency}
        for p in prices
        if p.platform != product.platform and p.price > 0
    ]
    
    margins = []
    if product.price > 0 and sell_prices:
        source_currency = product.currency or "CNY"
        margins = compute_margins(
            source_price=product.price,
            source_currency=source_currency,
            sell_prices=sell_prices,
        )
    
    # 5. Compute market pulse
    pulse = _compute_pulse(product, prices, matches)
    
    # 6. Compute verdict
    verdict = compute_verdict(
        margins=margins,
        matches=matches,
        pulse=pulse,
    )
    
    return ProductResponse(
        product=product,
        prices=prices,
        matches=matches,
        margins=margins,
        pulse=pulse,
        verdict=verdict,
    )


def _compute_pulse(
    product: ProductDetail,
    prices: list[PriceEntry],
    matches: list[MatchResult],
) -> MarketPulse:
    """
    Estimate market pulse from available data.
    Heuristic for MVP — will improve with time-series data later.
    """
    # Velocity: based on sales_30d vs sales_total ratio
    velocity = "warm"
    velocity_detail = "Steady demand"
    
    if product.sales_30d and getattr(product, "sales_total", None) or 0:
        ratio = product.sales_30d / max(getattr(product, "sales_total", None) or 0, 1)
        if ratio > 0.3:
            velocity = "hot"
            velocity_detail = f"{product.sales_30d} sales in last 30 days — trending up"
        elif ratio > 0.15:
            velocity = "warm"
            velocity_detail = f"{product.sales_30d} sales in last 30 days — steady"
        elif ratio > 0.05:
            velocity = "cool"
            velocity_detail = f"{product.sales_30d} sales in last 30 days — slowing"
        else:
            velocity = "dead"
            velocity_detail = "Very few recent sales"
    elif product.bsr_rank:
        if product.bsr_rank < 1000:
            velocity = "hot"
            velocity_detail = f"BSR #{product.bsr_rank} — high volume"
        elif product.bsr_rank < 10000:
            velocity = "warm"
            velocity_detail = f"BSR #{product.bsr_rank} — moderate"
        else:
            velocity = "cool"
            velocity_detail = f"BSR #{product.bsr_rank} — low volume"
    
    # Competition: count of same-platform sellers with similar products
    seller_count = len(set(p.platform_id for p in prices))
    if seller_count <= 3:
        competition = "low"
        competition_detail = f"{seller_count} sellers found"
    elif seller_count <= 10:
        competition = "medium"
        competition_detail = f"{seller_count} sellers found"
    elif seller_count <= 25:
        competition = "high"
        competition_detail = f"{seller_count} sellers — crowded"
    else:
        competition = "saturated"
        competition_detail = f"{seller_count} sellers — saturated"
    
    # Window estimate
    if velocity == "hot" and competition in ("low", "medium"):
        window = "~3-6 months before saturation"
    elif velocity == "hot" and competition in ("high", "saturated"):
        window = "~1-2 months — act fast"
    elif velocity == "warm":
        window = "~6-12 months steady"
    else:
        window = "Window may have closed"
    
    return MarketPulse(
        velocity=velocity,
        velocity_detail=velocity_detail,
        competition=competition,
        competition_detail=competition_detail,
        window=window,
    )


def _row_to_detail(row: dict) -> ProductDetail:
    """Convert a DB row to ProductDetail."""
    return ProductDetail(
        id=row["id"],
        platform=row["platform"],
        platform_id=row["platform_id"],
        title=row["title"],
        title_translated=row.get("title_translated"),
        price=float(row["price"]) if row.get("price") else 0.0,
        currency=row.get("currency") or "USD",
        url=row.get("url"),
        image_urls=row.get("image_urls"),
        supplier_name=row.get("supplier_name"),
        moq=row.get("moq"),
        sales_total=row.get("sales_total"),
        sales_30d=row.get("sales_30d"),
        review_count=row.get("review_count"),
        review_avg=float(row["review_avg"]) if row.get("review_avg") else None,
        category=row.get("category"),
        bsr_rank=row.get("bsr_rank"),
        is_active=row.get("is_active", True),
        first_seen=row.get("first_seen"),
        last_updated=row.get("last_updated"),
    )
