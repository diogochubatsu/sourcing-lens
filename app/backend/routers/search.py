"""
Search Router — POST /search
Accepts text, URL, or image and returns matching products.
"""
from fastapi import APIRouter, HTTPException
from models import SearchRequest, SearchResponse
from services.search_service import search_by_text, search_by_url, search_by_image

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest):
    """
    Search for products by text, URL, or image.
    Exactly one input type should be provided.
    """
    # Determine query type
    if req.url:
        products = search_by_url(req.url)
        return SearchResponse(
            query=req.url,
            query_type="url",
            products=products,
            total=len(products),
        )
    
    if req.text:
        products = search_by_text(req.text)
        return SearchResponse(
            query=req.text,
            query_type="text",
            products=products,
            total=len(products),
        )
    
    if req.image_base64:
        products = search_by_image(req.image_base64)
        return SearchResponse(
            query="<image>",
            query_type="image",
            products=products,
            total=len(products),
        )
    
    raise HTTPException(
        status_code=400,
        detail="Provide one of: text, url, or image_base64",
    )
