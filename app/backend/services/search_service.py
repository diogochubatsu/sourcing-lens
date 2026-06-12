"""
Search Service
Handles text, URL, and image-based product search.
"""
import re
from typing import Optional
from models import SearchProduct
from database import get_cursor


# URL patterns to extract platform + platform_id
URL_PATTERNS = [
    # 1688
    (r"detail\.1688\.com/offer/(\d+)", "1688"),
    # AliExpress
    (r"aliexpress\.com/item/(\d+)", "aliexpress"),
    # Amazon BR
    (r"amazon\.com\.br/dp/([A-Z0-9]+)", "amazon_br"),
    # Amazon US
    (r"amazon\.com/dp/([A-Z0-9]+)", "amazon_us"),
    # Mercado Livre
    (r"mercadolivre\.com\.br/(?:produto/)?([A-Z0-9\-]+)", "ml"),
    # Shopee
    (r"shopee\.com\.br/product/(\d+/\d+)", "shopee"),
]


def parse_url(url: str) -> Optional[tuple[str, str]]:
    """Extract (platform, platform_id) from a product URL."""
    for pattern, platform in URL_PATTERNS:
        m = re.search(pattern, url)
        if m:
            return (platform, m.group(1))
    return None


def search_by_text(query: str, limit: int = 20) -> list[SearchProduct]:
    """Full-text search on product titles."""
    with get_cursor() as cur:
        cur.execute("""
            SELECT id, platform, platform_id, title, title_translated,
                   price, currency, url, image_urls, supplier_name,
                   sales_total, review_avg
            FROM arbitlens_products
            WHERE is_active = TRUE
              AND (title ILIKE %s OR title_translated ILIKE %s)
            ORDER BY sales_total DESC NULLS LAST
            LIMIT %s
        """, (f"%{query}%", f"%{query}%", limit))
        
        rows = cur.fetchall()
        return [_row_to_search_product(r) for r in rows]


def search_by_url(url: str) -> list[SearchProduct]:
    """Search by URL — extract platform/id, then find cross-platform matches."""
    parsed = parse_url(url)
    if not parsed:
        # Fall back to text search on URL domain
        return search_by_text(url, limit=5)
    
    platform, platform_id = parsed
    
    with get_cursor() as cur:
        # First find the product
        cur.execute("""
            SELECT id, platform, platform_id, title, title_translated,
                   price, currency, url, image_urls, supplier_name,
                   sales_total, review_avg
            FROM arbitlens_products
            WHERE platform = %s AND platform_id = %s
        """, (platform, platform_id))
        
        product = cur.fetchone()
        if not product:
            return []
        
        # Then find matches
        cur.execute("""
            SELECT p.id, p.platform, p.platform_id, p.title, p.title_translated,
                   p.price, p.currency, p.url, p.image_urls, p.supplier_name,
                   p.sales_total, p.review_avg
            FROM arbitlens_products p
            JOIN arbitlens_matches m ON (
                (m.product_a_id = %s AND m.product_b_id = p.id)
                OR (m.product_b_id = %s AND m.product_a_id = p.id)
            )
            WHERE p.is_active = TRUE
            ORDER BY m.confidence DESC
            LIMIT 20
        """, (product["id"], product["id"]))
        
        matches = cur.fetchall()
        
        # Return original + matches
        results = [_row_to_search_product(product)]
        results.extend(_row_to_search_product(r) for r in matches)
        return results


def search_by_image(image_base64: str, limit: int = 20) -> list[SearchProduct]:
    """
    Image-based search using pgvector cosine similarity.
    Requires SigLIP2 embeddings to be computed (future feature).
    For now, returns empty — will be wired when embeddings pipeline is ready.
    """
    # TODO: When SigLIP2 embeddings are in the DB:
    # 1. Decode image_base64
    # 2. Compute SigLIP2 embedding
    # 3. SELECT ... ORDER BY image_embedding <=> %s LIMIT %s
    return []


def _row_to_search_product(row: dict) -> SearchProduct:
    """Convert a DB row to a SearchProduct."""
    return SearchProduct(
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
        sales_total=row.get("sales_total"),
        review_avg=float(row["review_avg"]) if row.get("review_avg") else None,
    )
