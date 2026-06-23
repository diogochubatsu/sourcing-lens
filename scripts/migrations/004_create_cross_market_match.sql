-- Migration: Create cross_market_match table
-- Links 1688 products (from silver_products) to MercadoLivre listings (from ml_bestsellers)
-- via title similarity matching (PT↔PT)

CREATE TABLE IF NOT EXISTS cross_market_match (
    id              BIGSERIAL PRIMARY KEY,

    -- ML side
    ml_item_id      TEXT NOT NULL,
    ml_title        TEXT,                       -- original ML title (PT)
    ml_price_brl    NUMERIC,
    ml_category     TEXT,                       -- category_code from ml_bestsellers

    -- 1688 side (silver_products)
    bronze_source   TEXT NOT NULL,              -- 'listing' | 'factory'
    bronze_id       BIGINT,                     -- silver_products.id
    offer_id        TEXT,                       -- 1688 offer_id
    china_title_zh  TEXT,                       -- original ZH title
    china_title_pt  TEXT,                       -- translated PT title
    china_price_cny NUMERIC,

    -- Match metadata
    match_score     NUMERIC NOT NULL,           -- 0.0–1.0 combined similarity
    match_method    TEXT NOT NULL DEFAULT 'title_semantic',  -- 'title_semantic' | 'title_fuzzy' | 'title_combined'
    fuzzy_score     NUMERIC,                    -- string-level fuzzy score
    semantic_score  NUMERIC,                    -- TF-IDF cosine similarity
    normalized_edit_distance NUMERIC,           -- Levenshtein-based

    -- Derived
    margin_estimate NUMERIC,                    -- (brl - cny*exchange_rate) / brl
    exchange_rate   NUMERIC DEFAULT 0.80,       -- CNY→BRL approximate rate

    -- Metadata
    matched_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_cmm_ml_item
    ON cross_market_match (ml_item_id);

CREATE INDEX IF NOT EXISTS idx_cmm_bronze
    ON cross_market_match (bronze_source, bronze_id);

CREATE INDEX IF NOT EXISTS idx_cmm_score
    ON cross_market_match (match_score DESC);

CREATE INDEX IF NOT EXISTS idx_cmm_method
    ON cross_market_match (match_method);

-- Prevent duplicate matches (same ML item + same 1688 product)
CREATE UNIQUE INDEX IF NOT EXISTS idx_cmm_unique_match
    ON cross_market_match (ml_item_id, bronze_source, bronze_id);

-- Comment
COMMENT ON TABLE cross_market_match IS
    'Cross-market product matching between 1688 (China) and MercadoLivre (Brazil). '
    'Populated by scripts/title-similarity-match.py. Score 0-1 indicates match confidence.';

COMMENT ON COLUMN cross_market_match.match_score IS
    'Combined similarity score (0-1). Weighted average of fuzzy_score and semantic_score.';

COMMENT ON COLUMN cross_market_match.match_method IS
    'Method used: title_combined (fuzzy+semantic), title_fuzzy (string only), title_semantic (TF-IDF only).';
