"""
ArbitLens Pydantic Models for API responses
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# === REQUEST MODELS ===

class SearchRequest(BaseModel):
    """POST /search body. Exactly one of text/url/image_base64 should be set."""
    text: Optional[str] = None
    url: Optional[str] = None
    image_base64: Optional[str] = None


# === SHARED ===

class PriceEntry(BaseModel):
    platform: str
    platform_id: str
    price: float
    currency: str
    url: Optional[str] = None
    sales_total: Optional[int] = None
    review_avg: Optional[float] = None
    is_active: bool = True


class MatchResult(BaseModel):
    product_id: int
    platform: str
    platform_id: str
    title: str
    title_translated: Optional[str] = None
    price: float
    currency: str
    url: Optional[str] = None
    image_urls: Optional[list[str]] = None
    confidence: float
    match_method: str
    supplier_name: Optional[str] = None
    moq: Optional[int] = None


class MarginEntry(BaseModel):
    sell_platform: str
    quantity: int
    landed_cost_per_unit: float
    sell_price: float
    margin_pct: float
    currency: str
    factor_used: float
    notes: Optional[str] = None


class MarketPulse(BaseModel):
    velocity: str           # "hot", "warm", "cool", "dead"
    velocity_detail: str    # e.g. "trending up this month"
    competition: str        # "low", "medium", "high", "saturated"
    competition_detail: str # e.g. "12 sellers on ML"
    window: str             # e.g. "~3-6 months before saturation"


class Verdict(BaseModel):
    rating: str             # "strong", "moderate", "weak", "avoid"
    summary: str            # one-liner
    pros: list[str]
    cons: list[str]
    recommendation: str     # actionable advice


# === SEARCH RESPONSE ===

class SearchProduct(BaseModel):
    id: int
    platform: str
    platform_id: str
    title: str
    title_translated: Optional[str] = None
    price: float
    currency: str
    url: Optional[str] = None
    image_urls: Optional[list[str]] = None
    supplier_name: Optional[str] = None
    sales_total: Optional[int] = None
    review_avg: Optional[float] = None


class SearchResponse(BaseModel):
    query: str
    query_type: str             # "text", "url", "image"
    products: list[SearchProduct]
    total: int


# === PRODUCT DETAIL RESPONSE ===

class ProductDetail(BaseModel):
    id: int
    platform: str
    platform_id: str
    title: str
    title_translated: Optional[str] = None
    price: float
    currency: str
    url: Optional[str] = None
    image_urls: Optional[list[str]] = None
    supplier_name: Optional[str] = None
    moq: Optional[int] = None
    sales_total: Optional[int] = None
    sales_30d: Optional[int] = None
    review_count: Optional[int] = None
    review_avg: Optional[float] = None
    category: Optional[str] = None
    bsr_rank: Optional[int] = None
    is_active: bool = True
    first_seen: Optional[datetime] = None
    last_updated: Optional[datetime] = None


class ProductResponse(BaseModel):
    product: ProductDetail
    prices: list[PriceEntry]
    matches: list[MatchResult]
    margins: list[MarginEntry]
    pulse: Optional[MarketPulse] = None
    verdict: Optional[Verdict] = None
