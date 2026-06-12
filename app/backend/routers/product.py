"""
Product Router — GET /product/{id}
Returns full product detail with prices, margins, matches, pulse, and verdict.
"""
from fastapi import APIRouter, HTTPException
from models import ProductResponse
from services.product_service import get_product_detail

router = APIRouter()


@router.get("/product/{product_id}", response_model=ProductResponse)
async def product_detail(product_id: int):
    """
    Get full product detail including:
    - Product info
    - Cross-platform prices
    - Confidence-scored matches
    - Margin analysis
    - Market pulse
    - AI verdict
    """
    result = get_product_detail(product_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    return result
