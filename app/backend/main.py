#!/usr/bin/env python3
"""ArbitLens BR — FastAPI backend."""
import os, sys, json

# Ensure app/backend/ is in sys.path for relative imports in routers/services
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datetime import datetime, timedelta
from decimal import Decimal
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from scripts.db import query, execute, execute_returning

app = FastAPI(title="ArbitLens BR", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routers.product import router as product_router
from routers.search import router as search_router
app.include_router(product_router, prefix="/api", tags=["product"])
app.include_router(search_router, prefix="/api", tags=["search"])

# ── API ──────────────────────────────────────────────────────

@app.get("/api/matches")
def list_matches(limit: int = 50, sort_by: str = Query("confidence", pattern="^(confidence|margin|-margin)$")):
    """List cross-platform matches with product details.

    sort_by options:
      - confidence (default): sort by match confidence DESC
      - margin: sort by price_diff DESC (biggest savings first)
      - -margin: sort by price_diff ASC (biggest loss first)
    """
    order_clause = "ORDER BY m.confidence DESC"
    if sort_by == "margin":
        order_clause = "ORDER BY price_diff DESC"
    elif sort_by == "-margin":
        order_clause = "ORDER BY price_diff ASC"

    rows = query(f"""
        SELECT 
            m.id, m.confidence, m.match_method,
            p1.platform_id as amazon_platform_id, 
            p1.title as amazon_title, p1.price as amazon_price, 
            p1.sales_30d as amazon_sales, p1.url as amazon_url, 
            p1.platform as amazon_platform,
            p1.category,
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
        WHERE (p1.platform = 'amazon_br' AND p2.platform = 'ml')
           OR (p1.platform = 'amazon_br' AND p2.platform = 'amazon_us')
        {order_clause}
        LIMIT %s
    """, (limit,))
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

        # Margin percentage
        if ml_price > 0:
            r['margin_percent'] = round((amz_price - ml_price) / ml_price * 100, 2)
        else:
            r['margin_percent'] = 0.0

        # Image URLs from join
        r['image_url_a'] = r.get('image_urls_a', [None])[0] if r.get('image_urls_a') else None
        r['image_url_b'] = r.get('image_urls_b', [None])[0] if r.get('image_urls_b') else None

        results.append(r)
    return {"matches": results, "count": len(results)}

@app.get("/api/products")
def list_products(platform: str = None, category: str = None, limit: int = 100):
    """List products, optionally filtered."""
    conditions = ["is_active = TRUE"]
    params = []
    if platform:
        conditions.append("platform = %s")
        params.append(platform)
    if category:
        conditions.append("category = %s")
        params.append(category)
    sql = f"SELECT * FROM products WHERE {' AND '.join(conditions)} ORDER BY sales_30d DESC NULLS LAST LIMIT %s"
    params.append(limit)
    rows = query(sql, tuple(params))
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

@app.get("/api/stats")
def get_stats():
    total = query("SELECT COUNT(*) as c FROM products WHERE is_active=true")[0]['c']
    by_platform = query("SELECT platform, COUNT(*) as cnt FROM products WHERE is_active=true GROUP BY platform")
    return {"total_products": total, "by_platform": [dict(r) for r in by_platform]}

@app.get("/api/price-history")
def get_price_history(platform_id: str = None):
    if not platform_id:
        return {"history": []}
    rows = query("""
        SELECT ph.price, ph.sales_30d, ph.recorded_at
        FROM price_history ph
        JOIN products p ON ph.product_id = p.id
        WHERE p.platform_id = %s
        ORDER BY ph.recorded_at
    """, (platform_id,))
    return {"history": [dict(r) for r in rows]}

@app.get("/api/match-history/{match_id}")
def get_match_history(match_id: int):
    """Return price history for BOTH products in a match."""
    rows = query("""
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

@app.get("/api/product-history/{product_id}")
def get_product_history(product_id: int):
    """Return price history for a single product."""
    rows = query("""
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

@app.get("/api/price-drops")
def get_price_drops(limit: int = 5):
    """Return top matches with biggest recent price gap changes.
    
    Calculates the change in price difference by comparing latest
    price readings with the average of the 3 previous readings.
    Positive change = Amazon got more expensive relative to ML (bad).
    Negative change = Amazon got cheaper relative to ML (good drop!).
    """
    # Get all matches with their latest price history records
    matches = query("""
        SELECT m.id, m.confidence,
               p1.id as amazon_id, p1.title as amazon_title, p1.platform_id as amazon_pid,
               p1.price as amazon_price, p1.platform as amazon_platform,
               p2.id as ml_id, p2.title as ml_title, p2.platform_id as ml_pid, 
               p2.price as ml_price, p2.platform as ml_platform,
               p1.category
        FROM matches m
        JOIN products p1 ON m.product_a_id = p1.id
        JOIN products p2 ON m.product_b_id = p2.id
        WHERE (p1.platform = 'amazon_br' AND p2.platform = 'ml')
           OR (p1.platform = 'amazon_br' AND p2.platform = 'amazon_us')
        ORDER BY m.confidence DESC
    """)
    
    results = []
    for m in matches:
        match_id = m['id']
        amz_id = m['amazon_id']
        ml_id = m['ml_id']
        
        # Get last 4 price history records for Amazon product
        amz_history = query("""
            SELECT price, recorded_at FROM price_history 
            WHERE product_id = %s ORDER BY recorded_at DESC LIMIT 4
        """, (amz_id,))
        
        # Get last 4 price history records for ML product
        ml_history = query("""
            SELECT price, recorded_at FROM price_history 
            WHERE product_id = %s ORDER BY recorded_at DESC LIMIT 4
        """, (ml_id,))
        
        if len(amz_history) < 2 or len(ml_history) < 2:
            continue  # Not enough data
        
        # Latest prices
        latest_amz = float(amz_history[0]['price'])
        latest_ml = float(ml_history[0]['price'])
        latest_diff = latest_amz - latest_ml
        
        # Average of previous 3 prices
        prev_amz = sum(float(r['price']) for r in amz_history[1:4]) / min(len(amz_history[1:4]), 3)
        prev_ml = sum(float(r['price']) for r in ml_history[1:4]) / min(len(ml_history[1:4]), 3)
        prev_diff = prev_amz - prev_ml
        
        # Change: negative means Amazon got cheaper relative to ML (price drop!)
        diff_change = latest_diff - prev_diff
        pct_change = (diff_change / prev_diff * 100) if prev_diff != 0 else 0
        
        results.append({
            'match_id': match_id,
            'amazon_title': m['amazon_title'][:60] if m['amazon_title'] else '',
            'ml_title': m['ml_title'][:60] if m['ml_title'] else '',
            'amazon_price': latest_amz,
            'ml_price': latest_ml,
            'latest_diff': latest_diff,
            'prev_avg_diff': round(prev_diff, 2),
            'diff_change': round(diff_change, 2),
            'pct_change': round(pct_change, 2),
            'category': m.get('category', ''),
            'confidence': float(m['confidence']) if m['confidence'] else 0,
            'amazon_platform': m['amazon_platform'],
            'ml_platform': m['ml_platform']
        })
    
    # Sort by biggest negative change (biggest price drop = amazon cheaper)
    results.sort(key=lambda r: r['diff_change'])
    
    return {"drops": results[:limit], "count": min(len(results), limit)}

@app.get("/api/alerts")
def get_alerts(limit: int = 20, unread_only: bool = False):
    cond = "WHERE 1=1"
    if unread_only:
        cond += " AND is_read = FALSE"
    rows = query(f"SELECT * FROM alerts {cond} ORDER BY created_at DESC LIMIT %s", (limit,))
    unread = query("SELECT COUNT(*) as c FROM alerts WHERE is_read = FALSE")[0]['c']
    return {"alerts": [dict(r) for r in rows], "count": len(rows), "unread_count": unread}

@app.post("/api/alerts/{alert_id}/read")
def mark_alert_read(alert_id: int):
    execute("UPDATE alerts SET is_read = TRUE WHERE id = %s", (alert_id,))
    return {"ok": True}

@app.post("/api/users")
def create_user(username: str, email: str, password: str):
    import hashlib
    pw = hashlib.sha256(password.encode()).hexdigest()
    try:
        r = execute_returning(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
            (username, email, pw)
        )
        return {"ok": True, "user_id": r[0]['id']}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/users/login")
def login(username: str, password: str):
    import hashlib
    pw = hashlib.sha256(password.encode()).hexdigest()
    r = query("SELECT id, username FROM users WHERE username=%s AND password_hash=%s", (username, pw))
    if r:
        return {"ok": True, "user": dict(r[0])}
    return {"ok": False, "error": "Invalid credentials"}

@app.post("/api/favorites")
def add_favorite(user_id: int, product_id: int):
    try:
        execute("INSERT INTO favorites (user_id, product_id) VALUES (%s, %s)", (user_id, product_id))
        return {"ok": True}
    except:
        return {"ok": False, "error": "Already exists"}

@app.delete("/api/favorites")
def remove_favorite(user_id: int, product_id: int):
    execute("DELETE FROM favorites WHERE user_id=%s AND product_id=%s", (user_id, product_id))
    return {"ok": True}

@app.get("/api/favorites")
def list_favorites(user_id: int):
    rows = query("""
        SELECT p.* FROM favorites f JOIN products p ON f.product_id = p.id
        WHERE f.user_id = %s ORDER BY f.created_at DESC
    """, (user_id,))
    return {"favorites": [dict(r) for r in rows]}

@app.post("/api/custom-alerts")
def create_alert(user_id: int, product_id: int, alert_type: str, threshold_value: float = None):
    execute("""
        INSERT INTO custom_alerts (user_id, product_id, alert_type, threshold_value)
        VALUES (%s, %s, %s, %s)
    """, (user_id, product_id, alert_type, threshold_value))
    return {"ok": True}

@app.get("/api/custom-alerts")
def list_alerts(user_id: int):
    rows = query("SELECT * FROM custom_alerts WHERE user_id=%s", (user_id,))
    return {"alerts": [dict(r) for r in rows]}

@app.put("/api/users/{user_id}/preferences")
def update_prefs(user_id: int, preferences: dict):
    execute("UPDATE users SET preferred_categories = %s WHERE id=%s",
            (json.dumps(preferences.get('categories', [])), user_id))
    return {"ok": True}

# ── Frontend ─────────────────────────────────────────────────

@app.get("/")
def serve_frontend():
    return FileResponse(os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html"))

frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# Serve local product images
images_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "images")
if os.path.exists(images_dir):
    app.mount("/images", StaticFiles(directory=images_dir), name="images")
else:
    print(f"Warning: frontend dir not found at {frontend_dir}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
