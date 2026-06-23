"""ArbitLens BR — FastAPI backend."""
import os
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database import init_pool, close_pool
from routers import matches_router, products_router, users_router, alerts_router
from routers.product import router as product_router
from routers.admin import router as admin_router

from services.cache import cached, cache_stats
# ── Logging ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("arbitlens")

# ── App ──────────────────────────────────────────────────────
app = FastAPI(title="ArbitLens BR", version="0.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5000",
        "http://34.30.146.117:5000",
        "http://127.0.0.1:5000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────
app.include_router(matches_router)
app.include_router(products_router)
app.include_router(users_router)
app.include_router(alerts_router)
app.include_router(product_router)
app.include_router(admin_router)

# ── Health ───────────────────────────────────────────────────

@app.get("/api/health")
def health_check():
    """Health check endpoint for monitoring."""
    try:
        from database import query as db_query
        result = db_query("SELECT 1 as ok")
        db_ok = len(result) > 0
    except Exception as e:
        logger.error(f"Health check DB error: {e}")
        db_ok = False
    return {"status": "healthy" if db_ok else "degraded", "database": "connected" if db_ok else "disconnected", "version": "0.4.0"}


# ── Price Drops (optimized) ─────────────────────────────────

@app.get("/api/price-drops")
@cached(ttl_seconds=30)
def get_price_drops(limit: int = 5):
    """Return top matches with biggest recent price gap changes.
    
    Optimized: single query instead of N+1.
    """
    from database import query as db_query

    matches = db_query("""
        SELECT m.id, m.confidence,
               p1.id as amazon_id, p1.title as amazon_title, p1.platform_id as amazon_pid,
               p1.price as amazon_price, p1.platform as amazon_platform,
               p2.id as ml_id, p2.title as ml_title, p2.platform_id as ml_pid, 
               p2.price as ml_price, p2.platform as ml_platform,
               p1.category_l1
        FROM matches m
        JOIN products p1 ON m.product_a_id = p1.id
        JOIN products p2 ON m.product_b_id = p2.id
        WHERE (p1.platform = 'amazon_br' AND p2.platform = 'ml')
           OR (p1.platform = 'amazon_br' AND p2.platform = 'amazon_us')
        ORDER BY m.confidence DESC
    """)
    
    if not matches:
        return {"drops": [], "count": 0}
    
    # Get all product IDs
    product_ids = set()
    for m in matches:
        product_ids.add(m['amazon_id'])
        product_ids.add(m['ml_id'])
    
    # Batch fetch price history for all products
    history_query = """
        SELECT product_id, price, recorded_at
        FROM price_history
        WHERE product_id = ANY(%s)
        ORDER BY product_id, recorded_at DESC
    """
    all_history = db_query(history_query, (list(product_ids),))
    
    # Group history by product_id
    history_by_product = {}
    for h in all_history:
        pid = h['product_id']
        if pid not in history_by_product:
            history_by_product[pid] = []
        history_by_product[pid].append(h)
    
    results = []
    for m in matches:
        amz_history = history_by_product.get(m['amazon_id'], [])
        ml_history = history_by_product.get(m['ml_id'], [])
        
        if len(amz_history) < 2 or len(ml_history) < 2:
            continue
        
        latest_amz = float(amz_history[0]['price'])
        latest_ml = float(ml_history[0]['price'])
        latest_diff = latest_amz - latest_ml
        
        prev_amz = sum(float(r['price']) for r in amz_history[1:4]) / min(len(amz_history[1:4]), 3)
        prev_ml = sum(float(r['price']) for r in ml_history[1:4]) / min(len(ml_history[1:4]), 3)
        prev_diff = prev_amz - prev_ml
        
        diff_change = latest_diff - prev_diff
        pct_change = (diff_change / prev_diff * 100) if prev_diff != 0 else 0
        
        results.append({
            'match_id': m['id'],
            'amazon_title': m['amazon_title'][:60] if m['amazon_title'] else '',
            'ml_title': m['ml_title'][:60] if m['ml_title'] else '',
            'amazon_price': latest_amz,
            'ml_price': latest_ml,
            'latest_diff': latest_diff,
            'prev_avg_diff': round(prev_diff, 2),
            'diff_change': round(diff_change, 2),
            'pct_change': round(pct_change, 2),
            'category': m.get('category_l1', ''),
            'confidence': float(m['confidence']) if m['confidence'] else 0,
            'amazon_platform': m['amazon_platform'],
            'ml_platform': m['ml_platform']
        })
    
    results.sort(key=lambda r: r['diff_change'])
    
    return {"drops": results[:limit], "count": min(len(results), limit)}


# ── Frontend ─────────────────────────────────────────────────

@app.get("/")
def serve_frontend():
    return FileResponse(os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html"))

@app.get("/schema")
def serve_schema():
    return FileResponse(os.path.join(os.path.dirname(__file__), "..", "frontend", "schema.html"))

@app.get("/schema")
def serve_schema():
    return FileResponse(os.path.join(os.path.dirname(__file__), "..", "frontend", "schema.html"))

frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

images_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "images")
if os.path.exists(images_dir):
    app.mount("/images", StaticFiles(directory=images_dir), name="images")



# ── Cache Stats ─────────────────────────────────────────────

@app.get("/api/cache-stats")
def cache_stats_endpoint():
    from services.cache import cache_stats
    return cache_stats()

# ── Lifecycle ────────────────────────────────────────────────

@app.on_event("startup")
def startup():
    logger.info("Starting ArbitLens backend...")
    try:
        init_pool()
        logger.info("Database pool initialized")
    except Exception as e:
        logger.warning(f"Database not available: {e}")
        logger.warning("Running in degraded mode - API endpoints requiring DB will fail")

@app.on_event("shutdown")
def shutdown():
    logger.info("Shutting down ArbitLens backend...")
    close_pool()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
