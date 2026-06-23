#!/usr/bin/env python3
"""
opportunity_detect.py — Detect high-margin sourcing opportunities.

Finds products with:
1. High sales on Chinese platforms (1688, Taobao, Alibaba)
2. Low/no listings on MercadoLivre
3. High margin potential

Scoring: velocity_gap × margin_estimate × demand_signal

Usage:
  python3 opportunity_detect.py                    # detect all opportunities
  python3 opportunity_detect.py --category audio   # filter by category
  python3 opportunity_detect.py --min-score 50     # minimum score threshold
"""
import json
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def get_pg_conn():
    """Get PostgreSQL connection."""
    import psycopg2
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL not set")
    return psycopg2.connect(database_url)

def detect_opportunities(category=None, min_score=0, limit=50):
    """Detect sourcing opportunities by analyzing platform gaps."""
    conn = get_pg_conn()
    cursor = conn.cursor()
    
    # Find products with high sales on Chinese platforms
    # but potentially missing from MercadoLivre
    where_clauses = ["image_embedding IS NOT NULL"]
    params = []
    
    if category:
        where_clauses.append("category = %s")
        params.append(category)
    
    where_sql = " AND ".join(where_clauses)
    
    # Get Chinese platform products with sales data
    query = f"""
        SELECT 
            p.id,
            p.platform || '_' || p.platform_id as product_id,
            p.platform,
            p.title,
            p.price,
            p.category,
            COALESCE(p.sales_30d, 0) as sales_30d,
            COALESCE(p.review_count, 0) as review_count,
            COALESCE(p.review_avg, 0) as review_avg,
            CASE WHEN array_length(p.image_urls, 1) > 0 THEN p.image_urls[1] ELSE NULL END as image_url,
            CASE 
                WHEN p.platform LIKE '%1688%' THEN 
                    COALESCE(p.sales_30d, 0) * 0.4 + 
                    COALESCE(p.review_count, 0) * 0.3 +
                    COALESCE(p.review_avg, 0) * 20 * 0.3
                ELSE 
                    COALESCE(p.sales_30d, 0) * 0.5 + 
                    COALESCE(p.review_count, 0) * 0.5
            END as velocity_score
        FROM arbitlens_products p
        WHERE {where_sql}
            AND p.platform NOT LIKE '%mercado%'
            AND p.is_active = true
        ORDER BY velocity_score DESC
        LIMIT {int(limit)}
    """
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    products = cursor.fetchall()
    
    # Find matches on ML (if any)
    opportunities = []
    for prod in products:
        prod_id, platform_id, platform, title, price, cat, sales, reviews, rating, img_url, velocity = prod
        
        # Look for similar products on ML
        if cat:
            cursor.execute(
                "SELECT platform, price, title FROM arbitlens_products "
                "WHERE platform LIKE '%%mercado%%' AND category = %s "
                "AND image_embedding IS NOT NULL LIMIT 5",
                (cat,)
            )
        else:
            cursor.execute(
                "SELECT platform, price, title FROM arbitlens_products "
                "WHERE platform LIKE '%%mercado%%' "
                "AND image_embedding IS NOT NULL LIMIT 5"
            )
        ml_products = cursor.fetchall()
        
        # Calculate opportunity metrics
        ml_count = len(ml_products)
        ml_avg_price = sum(p[1] for p in ml_products) / ml_count if ml_count > 0 else 0
        china_price = float(price) if price else 0
        ml_avg_price_f = float(ml_avg_price)
        
        # Velocity gap: how much more popular in China vs ML
        velocity_gap = float(velocity) / max(ml_count * 10, 1)
        
        # Margin estimate: potential profit if sourced from China and sold on ML
        if china_price > 0 and ml_avg_price_f > 0:
            margin_pct = ((ml_avg_price_f - china_price * 1.5) / ml_avg_price_f) * 100  # 1.5x for shipping/taxes
        else:
            margin_pct = 0
        
        # Demand signal: based on sales velocity and reviews
        demand_signal = min(float(velocity) / 100, 1.0) + min(float(reviews) / 50, 0.5) if reviews else min(float(velocity) / 100, 1.0)
        
        # Competition level
        if ml_count == 0:
            competition = 'none'
        elif ml_count < 3:
            competition = 'low'
        elif ml_count < 10:
            competition = 'medium'
        else:
            competition = 'high'
        
        # Composite score (0-100)
        composite_score = min(100, (
            float(velocity_gap) * 30 +
            float(margin_pct) * 0.4 * 30 +
            float(demand_signal) * 40
        ))
        
        if composite_score >= min_score:
            opportunities.append({
                'product_id': platform_id,
                'platform': platform,
                'title': title,
                'price_china': china_price,
                'price_ml_avg': ml_avg_price,
                'category': cat,
                'sales_30d': sales,
                'review_count': reviews,
                'image_url': img_url,
                'velocity_gap': round(velocity_gap, 2),
                'margin_pct': round(margin_pct, 1),
                'demand_signal': round(demand_signal, 2),
                'competition': competition,
                'composite_score': round(composite_score, 1),
                'reasoning': _generate_reasoning(velocity, sales, reviews, ml_count, margin_pct, competition),
            })
    
    # Sort by score
    opportunities.sort(key=lambda x: x['composite_score'], reverse=True)
    
    conn.close()
    return opportunities

def _generate_reasoning(velocity, sales, reviews, ml_count, margin_pct, competition):
    """Generate human-readable reasoning for the opportunity."""
    parts = []
    
    if sales and sales > 50:
        parts.append(f"Alta demanda ({sales} vendas/mês)")
    elif sales and sales > 10:
        parts.append(f"Demanda moderada ({sales} vendas/mês)")
    
    if reviews and reviews > 20:
        parts.append(f"Boa reputação ({reviews} avaliações)")
    
    if ml_count == 0:
        parts.append("Sem concorrentes no ML")
    elif competition == 'low':
        parts.append("Pouca concorrência no ML")
    
    if margin_pct > 50:
        parts.append(f"Alta margem estimada ({margin_pct:.0f}%)")
    elif margin_pct > 20:
        parts.append(f"Margem moderada ({margin_pct:.0f}%)")
    
    return " | ".join(parts) if parts else "Oportunidade identificada"

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Detect sourcing opportunities')
    parser.add_argument('--category', help='Filter by category')
    parser.add_argument('--min-score', type=float, default=0, help='Minimum score threshold')
    parser.add_argument('--limit', type=int, default=50, help='Maximum results')
    args = parser.parse_args()
    
    opportunities = detect_opportunities(
        category=args.category,
        min_score=args.min_score,
        limit=args.limit
    )
    
    print(json.dumps({
        'opportunities': opportunities,
        'total': len(opportunities),
        'generated_at': datetime.utcnow().isoformat(),
    }, ensure_ascii=False, indent=2))
