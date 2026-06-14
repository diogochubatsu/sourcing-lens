"""Products router — product listing and history endpoints."""
from fastapi import APIRouter, Query
from decimal import Decimal
from typing import Optional

router = APIRouter(prefix="/api", tags=["products"])


@router.get("/products")
def list_products(
    platform: Optional[str] = Query(None, pattern="^(amazon_br|amazon_us|ml)$"),
    category_l1: Optional[str] = None,
    category_l2: Optional[str] = None,
    category_l3: Optional[str] = None,
    has_sales: Optional[bool] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    limit: int = Query(100, ge=1, le=1000)
):
    """List products, optionally filtered by platform, category, sales, or price."""
    from database import query as db_query

    conditions = ["is_active = TRUE"]
    params = []
    
    if platform:
        conditions.append("platform = %s")
        params.append(platform)
    if category_l1:
        conditions.append("category_l1 = %s")
        params.append(category_l1)
    if category_l2:
        conditions.append("category_l2 = %s")
        params.append(category_l2)
    if category_l3:
        conditions.append("category_l3 = %s")
        params.append(category_l3)
    if has_sales:
        conditions.append("sales_30d IS NOT NULL AND sales_30d > 0")
    if min_price is not None:
        conditions.append("price >= %s")
        params.append(min_price)
    if max_price is not None:
        conditions.append("price <= %s")
        params.append(max_price)
    
    sql = f"SELECT * FROM products WHERE {' AND '.join(conditions)} ORDER BY sales_30d DESC NULLS LAST LIMIT %s"
    params.append(limit)
    rows = db_query(sql, tuple(params))
    results = []
    for r in rows:
        d = dict(r)
        for k, v in d.items():
            if hasattr(v, 'isoformat'):
                d[k] = v.isoformat()
            elif isinstance(v, Decimal):
                d[k] = float(v)
        results.append(d)
    return {"products": results, "count": len(results)}


@router.get("/stats")
def get_stats():
    """Get platform and category statistics."""
    from database import query as db_query

    total = db_query("SELECT COUNT(*) as c FROM products WHERE is_active=true")[0]['c']
    by_platform = db_query("SELECT platform, COUNT(*) as cnt FROM products WHERE is_active=true GROUP BY platform")
    
    # Category stats
    by_category = db_query("""
        SELECT category_l1, COUNT(*) as cnt 
        FROM products WHERE is_active=true AND category_l1 IS NOT NULL
        GROUP BY category_l1 ORDER BY cnt DESC
    """)
    
    # Categories with matches
    with_matches = db_query("""
        SELECT p.category_l1, COUNT(DISTINCT m.id) as match_count
        FROM products p
        JOIN matches m ON (m.product_a_id = p.id OR m.product_b_id = p.id)
        WHERE p.is_active=true AND p.category_l1 IS NOT NULL
        GROUP BY p.category_l1
        ORDER BY match_count DESC
    """)
    
    return {
        "total_products": total,
        "by_platform": [dict(r) for r in by_platform],
        "by_category": [dict(r) for r in by_category],
        "categories_with_matches": [dict(r) for r in with_matches],
    }


@router.get("/categories")
def list_categories():
    """List all unique categories with product counts."""
    from database import query as db_query

    rows = db_query("""
        SELECT category_l1, category_l2, category_l3, 
               COUNT(*) as product_count,
               COUNT(*) FILTER (WHERE platform = 'amazon_br') as amazon_br_count,
               COUNT(*) FILTER (WHERE platform = 'amazon_us') as amazon_us_count,
               COUNT(*) FILTER (WHERE platform = 'ml') as ml_count
        FROM products 
        WHERE is_active=true AND category_l1 IS NOT NULL
        GROUP BY category_l1, category_l2, category_l3
        ORDER BY category_l1, category_l2, category_l3
    """)
    
    return {"categories": [dict(r) for r in rows], "count": len(rows)}


@router.get("/categories/{category_l1}")
def get_category_detail(category_l1: str):
    """Get detailed stats for a specific L1 category."""
    from database import query as db_query

    # Products in this category
    products = db_query("""
        SELECT platform, COUNT(*) as cnt, 
               AVG(price) as avg_price,
               SUM(COALESCE(sales_30d, 0)) as total_sales
        FROM products 
        WHERE is_active=true AND category_l1 = %s
        GROUP BY platform
    """, (category_l1,))
    
    # Subcategories
    subcategories = db_query("""
        SELECT category_l2, category_l3, COUNT(*) as cnt
        FROM products 
        WHERE is_active=true AND category_l1 = %s
        GROUP BY category_l2, category_l3
        ORDER BY cnt DESC
    """, (category_l1,))
    
    # Matches in this category
    matches = db_query("""
        SELECT COUNT(*) as match_count,
               AVG(m.confidence) as avg_confidence
        FROM matches m
        JOIN products p ON m.product_a_id = p.id
        WHERE p.category_l1 = %s
    """, (category_l1,))
    
    return {
        "category_l1": category_l1,
        "products_by_platform": [dict(p) for p in products],
        "subcategories": [dict(s) for s in subcategories],
        "matches": dict(matches[0]) if matches else {"match_count": 0, "avg_confidence": 0},
    }


@router.get("/price-history")
def get_price_history(platform_id: str = None):
    """Get price history for a product by platform_id."""
    from database import query as db_query

    if not platform_id:
        return {"history": []}
    rows = db_query("""
        SELECT ph.price, ph.sales_30d, ph.recorded_at
        FROM price_history ph
        JOIN products p ON ph.product_id = p.id
        WHERE p.platform_id = %s
        ORDER BY ph.recorded_at
    """, (platform_id,))
    return {"history": [dict(r) for r in rows]}


@router.get("/product-history/{product_id}")
def get_product_history(product_id: int):
    """Return price history for a single product."""
    from database import query as db_query

    rows = db_query("""
        SELECT ph.price, ph.sales_30d, ph.recorded_at
        FROM price_history ph
        WHERE ph.product_id = %s
        ORDER BY ph.recorded_at
    """, (product_id,))
    result = []
    for r in rows:
        d = dict(r)
        for k, v in d.items():
            if hasattr(v, 'isoformat'):
                d[k] = v.isoformat()
            elif hasattr(v, '__float__'):
                d[k] = float(v)
        result.append(d)
    return {"history": result}
