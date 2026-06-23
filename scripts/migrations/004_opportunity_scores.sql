-- Migration: Create opportunity_scores table
-- Task 2.4: Opportunity scoring algorithm
-- Score = velocity_gap * margin * demand_signal
-- Run via: source .env && psql "$DATABASE_URL" -f scripts/migrations/004_opportunity_scores.sql

CREATE TABLE IF NOT EXISTS opportunity_scores (
    id BIGSERIAL PRIMARY KEY,
    silver_product_id BIGINT REFERENCES silver_products(id),
    product_title TEXT,
    opportunity_type TEXT NOT NULL,  -- 'china_bestseller_no_ml' | 'ml_bestseller_no_china' | 'high_velocity_gap'

    -- Raw components
    ml_sales_velocity NUMERIC,       -- ML sales volume (absolute or per-day)
    china_sales_velocity NUMERIC,    -- China repurchase_rate or listing sales as proxy
    velocity_gap NUMERIC,            -- ml_velocity / china_velocity (ratio)
    margin_pct NUMERIC,              -- profit_margin_estimate
    demand_signal NUMERIC,           -- normalized demand indicator

    -- Composite score
    score NUMERIC NOT NULL,          -- velocity_gap * margin * demand_signal (0-100 normalized)
    reasoning TEXT,                   -- human-readable explanation

    -- Context data
    ml_category TEXT,
    price_cny NUMERIC,
    price_brl NUMERIC,
    ml_avg_price NUMERIC,
    competition_level TEXT,
    repurchase_rate INTEGER,
    supplier_region TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for sorting/filtering
CREATE INDEX IF NOT EXISTS idx_opportunity_scores_type ON opportunity_scores(opportunity_type);
CREATE INDEX IF NOT EXISTS idx_opportunity_scores_score ON opportunity_scores(score DESC);
CREATE INDEX IF NOT EXISTS idx_opportunity_scores_product ON opportunity_scores(silver_product_id);

COMMENT ON TABLE opportunity_scores IS 'Cross-market opportunity scores: velocity_gap × margin × demand_signal';
COMMENT ON COLUMN opportunity_scores.opportunity_type IS 'china_bestseller_no_ml: sells in China absent in Brazil. ml_bestseller_no_china: sells in Brazil absent in China. high_velocity_gap: mismatch between markets';
COMMENT ON COLUMN opportunity_scores.score IS 'Composite 0-100 score = normalized(velocity_gap) × normalized(margin) × normalized(demand_signal)';
