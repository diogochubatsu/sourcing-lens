"""Matches router — cross-platform product matching endpoints."""
from fastapi import APIRouter, Query
from decimal import Decimal

router = APIRouter(prefix="/api", tags=["matches"])


@router.get("/matches")
def list_matches(
    limit: int = Query(50, ge=1, le=500),
    sort_by: str = Query("confidence", pattern="^(confidence|margin|-margin)$"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0),
    category_l1: str = Query(None),
    min_sales: int = Query(0, ge=0),
):
    """List cross-platform matches with product details and quality filters."""
    from database import query as db_query

    order_clause = "ORDER BY m.confidence DESC"
    if sort_by == "margin":
        order_clause = "ORDER BY price_diff DESC"
    elif sort_by == "-margin":
        order_clause = "ORDER BY price_diff ASC"

    where_clauses = [
        "(p1.platform = 'amazon_br' AND p2.platform = 'ml')",
        "m.confidence >= %s",
    ]
    params = [min_confidence]

    if category_l1:
        where_clauses.append("p1.category_l1 = %s")
        params.append(category_l1)
    if min_sales > 0:
        where_clauses.append("(COALESCE(p1.sales_30d, 0) >= %s OR COALESCE(p2.sales_30d, 0) >= %s)")
        params.extend([min_sales, min_sales])

    where_sql = " AND ".join(where_clauses)
    params.append(limit)

    rows = db_query(f"""
        SELECT
            m.id, m.confidence, m.match_method,
            p1.id as product_a_id, p2.id as product_b_id,
            p1.platform_id as amazon_platform_id,
            p1.title as amazon_title, p1.price as amazon_price,
            p1.sales_30d as amazon_sales, p1.url as amazon_url,
            p1.platform as amazon_platform,
            p1.category_l1, p1.category_l2, p1.category_l3,
            p2.platform_id as ml_platform_id,
            p2.title as ml_title, p2.price as ml_price,
            p2.sales_30d as ml_sales, p2.url as ml_url,
            p2.platform as ml_platform,
            p2.currency as ml_currency,
            p1.image_urls as image_urls_a,
            p2.image_urls as image_urls_b,
            (COALESCE(p1.price, 0) - COALESCE(p2.price, 0)) as price_diff
        FROM matches m
        JOIN products p1 ON m.product_a_id = p1.id
        JOIN products p2 ON m.product_b_id = p2.id
        WHERE {where_sql}
        {order_clause}
        LIMIT %s
    """, tuple(params))
    
    results = []
    for r in rows:
        for k, v in r.items():
            if hasattr(v, 'isoformat'):
                r[k] = v.isoformat()
            elif hasattr(v, '__float__'):
                r[k] = float(v)
        amz_price = float(r.get('amazon_price') or 0)
        ml_price = float(r.get('ml_price') or 0)
        if r.get('ml_platform') == 'ml':
            r['ml_currency'] = 'BRL'
        else:
            r['ml_currency'] = 'USD'

        if ml_price > 0:
            r['margin_percent'] = round((amz_price - ml_price) / ml_price * 100, 2)
        else:
            r['margin_percent'] = 0.0

        r['image_url_a'] = r.get('image_urls_a', [None])[0] if r.get('image_urls_a') else None
        r['image_url_b'] = r.get('image_urls_b', [None])[0] if r.get('image_urls_b') else None

        results.append(r)
    return {"matches": results, "count": len(results)}


@router.get("/match-history/{match_id}")
def get_match_history(match_id: int):
    """Return price history for BOTH products in a match."""
    from database import query as db_query

    rows = db_query("""
        SELECT ph.price, ph.sales_30d, ph.recorded_at, p.platform_id, p.platform
        FROM price_history ph
        JOIN products p ON ph.product_id = p.id
        JOIN matches m ON (m.product_a_id = ph.product_id OR m.product_b_id = ph.product_id)
        WHERE m.id = %s
        ORDER BY ph.recorded_at, p.platform
    """, (match_id,))
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
