"""Alerts router — price drop and custom alerts."""
import os
from datetime import datetime, timedelta
from fastapi import APIRouter, Query

router = APIRouter(prefix="/api", tags=["alerts"])


@router.get("/alerts/price-drops")
def get_price_drops(limit: int = Query(10, ge=1, le=50)):
    """Get recent price drops across all matches."""
    from database import query as db_query

    rows = db_query("""
        SELECT 
            m.id as match_id,
            m.confidence,
            p1.title as amazon_title,
            p1.price as amazon_price,
            p1.platform_id as amazon_pid,
            p1.sales_30d as amazon_sales,
            p2.title as ml_title,
            p2.price as ml_price,
            p2.platform_id as ml_pid,
            p2.sales_30d as ml_sales,
            p1.category_l1,
            (p1.price - p2.price) as price_diff,
            CASE WHEN p2.price > 0 THEN 
                ROUND((p1.price - p2.price) / p2.price * 100, 1)
            ELSE 0 END as margin_pct
        FROM matches m
        JOIN products p1 ON m.product_a_id = p1.id
        JOIN products p2 ON m.product_b_id = p2.id
        WHERE p1.price IS NOT NULL AND p2.price IS NOT NULL
        ORDER BY price_diff DESC
        LIMIT %s
    """, (limit,))
    
    return {"drops": [dict(r) for r in rows], "count": len(rows)}


@router.get("/alerts/top-matches")
def get_top_matches(limit: int = Query(10, ge=1, le=50)):
    """Get highest confidence matches with best margins."""
    from database import query as db_query

    rows = db_query("""
        SELECT 
            m.id as match_id,
            m.confidence,
            p1.title as amazon_title,
            p1.price as amazon_price,
            p1.platform_id as amazon_pid,
            p1.sales_30d as amazon_sales,
            p2.title as ml_title,
            p2.price as ml_price,
            p2.platform_id as ml_pid,
            p2.sales_30d as ml_sales,
            p1.category_l1,
            (p1.price - p2.price) as price_diff,
            CASE WHEN p2.price > 0 THEN 
                ROUND((p1.price - p2.price) / p2.price * 100, 1)
            ELSE 0 END as margin_pct
        FROM matches m
        JOIN products p1 ON m.product_a_id = p1.id
        JOIN products p2 ON m.product_b_id = p2.id
        WHERE m.confidence >= 0.80
          AND p1.price IS NOT NULL AND p2.price IS NOT NULL
        ORDER BY m.confidence DESC, price_diff DESC
        LIMIT %s
    """, (limit,))
    
    return {"matches": [dict(r) for r in rows], "count": len(rows)}


@router.get("/alerts/new-products")
def get_new_products(days: int = Query(7, ge=1, le=30), limit: int = Query(20, ge=1, le=100)):
    """Get products added in the last N days."""
    from database import query as db_query

    rows = db_query("""
        SELECT id, platform, platform_id, title, price, currency, 
               sales_30d, category_l1, category_l2, category_l3, created_at
        FROM products
        WHERE is_active = TRUE
          AND created_at >= NOW() - INTERVAL '%s days'
        ORDER BY created_at DESC
        LIMIT %s
    """, (days, limit))
    
    return {"products": [dict(r) for r in rows], "count": len(rows)}


@router.get("/alerts/category-summary")
def get_category_summary():
    """Get summary of all categories with match rates."""
    from database import query as db_query

    rows = db_query("""
        SELECT 
            p.category_l1,
            COUNT(DISTINCT p.id) as total_products,
            COUNT(DISTINCT p.id) FILTER (WHERE p.platform = 'amazon_br') as amazon_br,
            COUNT(DISTINCT p.id) FILTER (WHERE p.platform = 'amazon_us') as amazon_us,
            COUNT(DISTINCT p.id) FILTER (WHERE p.platform = 'ml') as ml,
            COUNT(DISTINCT m.id) as matches,
            ROUND(AVG(p.price), 2) as avg_price,
            SUM(COALESCE(p.sales_30d, 0)) as total_sales
        FROM products p
        LEFT JOIN matches m ON (m.product_a_id = p.id OR m.product_b_id = p.id)
        WHERE p.is_active = TRUE AND p.category_l1 IS NOT NULL
        GROUP BY p.category_l1
        ORDER BY total_products DESC
    """)
    
    return {"categories": [dict(r) for r in rows], "count": len(rows)}


@router.get("/alerts/margin-analysis")
def get_margin_analysis():
    """Analyze margins across all matches."""
    from database import query as db_query

    rows = db_query("""
        SELECT 
            p1.category_l1,
            COUNT(*) as match_count,
            ROUND(AVG(p1.price), 2) as avg_amazon_price,
            ROUND(AVG(p2.price), 2) as avg_ml_price,
            ROUND(AVG(p1.price - p2.price), 2) as avg_price_diff,
            ROUND(AVG(CASE WHEN p2.price > 0 THEN (p1.price - p2.price) / p2.price * 100 ELSE 0 END), 1) as avg_margin_pct,
            ROUND(MIN(CASE WHEN p2.price > 0 THEN (p1.price - p2.price) / p2.price * 100 ELSE 0 END), 1) as min_margin_pct,
            ROUND(MAX(CASE WHEN p2.price > 0 THEN (p1.price - p2.price) / p2.price * 100 ELSE 0 END), 1) as max_margin_pct
        FROM matches m
        JOIN products p1 ON m.product_a_id = p1.id
        JOIN products p2 ON m.product_b_id = p2.id
        WHERE p1.price IS NOT NULL AND p2.price IS NOT NULL
        GROUP BY p1.category_l1
        ORDER BY avg_margin_pct DESC
    """)
    
    return {"analysis": [dict(r) for r in rows], "count": len(rows)}
