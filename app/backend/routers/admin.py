"""Admin router — category mapping management endpoints."""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/categories")
def list_categories(platform: Optional[str] = None, verified: Optional[bool] = None):
    """List category mappings."""
    from database import query as db_query

    conditions = ["1=1"]
    params = []
    
    if platform:
        conditions.append("platform = %s")
        params.append(platform)
    if verified is not None:
        conditions.append("verified = %s")
        params.append(verified)
    
    where = " AND ".join(conditions)
    rows = db_query(f"""
        SELECT id, our_l1, our_l2, our_l3, platform, platform_category_id,
               platform_category_name, bestsellers_url, confidence, verified,
               product_count, last_scraped, created_at
        FROM category_mappings
        WHERE {where}
        ORDER BY our_l1, our_l2, our_l3, platform
    """, tuple(params))
    
    return {"categories": [dict(r) for r in rows], "count": len(rows)}


@router.get("/categories/stats")
def category_stats():
    """Get category mapping statistics."""
    from database import query as db_query

    stats = db_query("""
        SELECT 
            platform,
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE verified = TRUE) as verified,
            COUNT(*) FILTER (WHERE bestsellers_url IS NOT NULL) as with_url,
            SUM(COALESCE(product_count, 0)) as total_products
        FROM category_mappings
        GROUP BY platform
        ORDER BY platform
    """)
    
    total = db_query("SELECT COUNT(*) as c FROM category_mappings")[0]['c']
    internal = db_query("SELECT COUNT(DISTINCT our_l1 || '/' || our_l2 || '/' || our_l3) as c FROM category_mappings")[0]['c']
    
    return {
        "by_platform": [dict(s) for s in stats],
        "total_mappings": total,
        "internal_categories": internal,
    }


@router.get("/categories/{category_id}")
def get_category(category_id: int):
    """Get a single category mapping."""
    from database import query as db_query

    rows = db_query("""
        SELECT id, our_l1, our_l2, our_l3, platform, platform_category_id,
               platform_category_name, platform_category_path, bestsellers_url,
               confidence, verified, product_count, last_scraped
        FROM category_mappings WHERE id = %s
    """, (category_id,))
    
    if not rows:
        raise HTTPException(status_code=404, detail="Category mapping not found")
    
    return {"category": dict(rows[0])}


@router.post("/categories")
def create_category(
    our_l1: str = Query(...), our_l2: str = Query(...), our_l3: str = Query(...),
    platform: str = Query(...), platform_id: Optional[str] = None,
    platform_name: Optional[str] = None, bestsellers_url: Optional[str] = None,
    confidence: float = Query(0.5, ge=0, le=1)
):
    """Create a new category mapping."""
    from database import execute_returning as db_execute_returning

    try:
        result = db_execute_returning("""
            INSERT INTO category_mappings 
                (our_l1, our_l2, our_l3, platform, platform_category_id,
                 platform_category_name, bestsellers_url, confidence)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (our_l1, our_l2, our_l3, platform) 
            DO UPDATE SET
                platform_category_id = COALESCE(EXCLUDED.platform_category_id, category_mappings.platform_category_id),
                platform_category_name = COALESCE(EXCLUDED.platform_category_name, category_mappings.platform_category_name),
                bestsellers_url = COALESCE(EXCLUDED.bestsellers_url, category_mappings.bestsellers_url),
                confidence = GREATEST(EXCLUDED.confidence, category_mappings.confidence),
                updated_at = NOW()
            RETURNING id
        """, (our_l1, our_l2, our_l3, platform, platform_id, platform_name, bestsellers_url, confidence))
        
        return {"ok": True, "id": result[0]['id']}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.put("/categories/{category_id}")
def update_category(
    category_id: int,
    verified: Optional[bool] = None,
    confidence: Optional[float] = Query(None, ge=0, le=1)
):
    """Update a category mapping."""
    from database import execute as db_execute

    updates = []
    params = []
    
    if verified is not None:
        updates.append("verified = %s")
        params.append(verified)
    if confidence is not None:
        updates.append("confidence = %s")
        params.append(confidence)
    
    if not updates:
        return {"ok": False, "error": "No fields to update"}
    
    updates.append("updated_at = NOW()")
    params.append(category_id)
    
    db_execute(f"""
        UPDATE category_mappings SET {', '.join(updates)} WHERE id = %s
    """, tuple(params))
    
    return {"ok": True}


@router.delete("/categories/{category_id}")
def delete_category(category_id: int):
    """Delete a category mapping."""
    from database import execute as db_execute

    db_execute("DELETE FROM category_mappings WHERE id = %s", (category_id,))
    return {"ok": True}


@router.get("/categories/discover")
def discover_category(url: str):
    """Discover category mapping from a product URL."""
    import requests
    import re
    from bs4 import BeautifulSoup

    try:
        if 'amazon' in url:
            platform = 'amazon_br' if '.com.br' in url else 'amazon_us'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept-Language': 'pt-BR,pt;q=0.9',
            }
            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code != 200:
                return {"ok": False, "error": f"HTTP {resp.status_code}"}
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            title_el = soup.select_one('#productTitle, #title span')
            title = title_el.get_text(strip=True) if title_el else ''
            
            breadcrumb = soup.select('#wayfinding-breadcrumbs_container a')
            categories = [a.get_text(strip=True) for a in breadcrumb]
            
            bestsellers_link = soup.select_one('a[href*="bestsellers"]')
            bestsellers_url = bestsellers_link.get('href', '') if bestsellers_link else ''
            if bestsellers_url.startswith('/'):
                bestsellers_url = f'https://www.amazon.com.br{bestsellers_url}'
            
            return {
                "ok": True,
                "platform": platform,
                "title": title,
                "categories": categories,
                "bestsellers_url": bestsellers_url,
            }
        
        elif 'mercadolivre' in url:
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
            if resp.status_code != 200:
                return {"ok": False, "error": f"HTTP {resp.status_code}"}
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            title_el = soup.select_one('h1')
            title = title_el.get_text(strip=True) if title_el else ''
            
            breadcrumb = soup.select('.andes-breadcrumb a')
            categories = [a.get_text(strip=True) for a in breadcrumb]
            
            return {
                "ok": True,
                "platform": "ml",
                "title": title,
                "categories": categories,
            }
        
        else:
            return {"ok": False, "error": "Unsupported URL"}
    
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/scraper-health")
def scraper_health(limit: int = 50):
    """Show recent scraper runs and their status. Useful for monitoring scraper reliability."""
    from database import query
    rows = query("""
        SELECT scraper_name, target_platform, target_category, status,
               products_scraped, products_inserted, products_updated, errors,
               error_message, started_at, completed_at, duration_seconds
        FROM scraper_health
        ORDER BY started_at DESC
        LIMIT %s
    """, (limit,))

    # Summary stats
    summary = query("""
        SELECT
            COUNT(*) FILTER (WHERE status='success') as success_count,
            COUNT(*) FILTER (WHERE status='error') as error_count,
            COUNT(*) FILTER (WHERE status='partial') as partial_count,
            COUNT(*) as total_runs,
            MAX(started_at) as last_run,
            SUM(products_inserted) as total_products_inserted
        FROM scraper_health
    """)
    return {
        "summary": summary[0] if summary else {},
        "runs": rows
    }
