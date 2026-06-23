-- Migration 005: Product snapshots for time-series velocity tracking
-- Enables "sold X this week" vs "total sold" in Scout
-- Applied to PostgreSQL (Cloud SQL intel_data)

-- 1. Snapshot table: stores a row per product per scrape run
CREATE TABLE IF NOT EXISTS product_snapshots (
    id            SERIAL PRIMARY KEY,
    offer_id      TEXT NOT NULL,
    title         TEXT,
    sales_volume_estimate INTEGER,
    price_min     NUMERIC,
    repurchase_rate INTEGER,
    category_label TEXT,
    supplier_name  TEXT,
    scraped_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    snapshot_source TEXT DEFAULT 'scrape'  -- 'scrape', 'backfill', etc.
);

COMMENT ON TABLE product_snapshots IS
    'Time-series snapshots of listing_products. Each row = one product at one scrape time. '
    'Used to compute sales velocity (change in sales_volume_estimate between scrapes).';

-- 2. Unique constraint: one snapshot per product per scrape timestamp
CREATE UNIQUE INDEX IF NOT EXISTS idx_product_snapshots_offer_scraped
    ON product_snapshots (offer_id, scraped_at);

-- 3. Index for velocity queries (get latest two snapshots for a product)
CREATE INDEX IF NOT EXISTS idx_product_snapshots_offer_date
    ON product_snapshots (offer_id, scraped_at DESC);

-- 4. Index for "trending this week" queries
CREATE INDEX IF NOT EXISTS idx_product_snapshots_scraped
    ON product_snapshots (scraped_at DESC);

-- 5. Backfill: snapshot current listing_products as baseline
-- (run once — subsequent scrapes will add new rows via INSERT)
INSERT INTO product_snapshots (offer_id, title, sales_volume_estimate, price_min, repurchase_rate, category_label, supplier_name, scraped_at, snapshot_source)
SELECT
    offer_id,
    title,
    sales_volume_estimate,
    price_min,
    repurchase_rate,
    category_label,
    supplier_name,
    COALESCE(scraped_at, NOW()),
    'backfill'
FROM listing_products
WHERE offer_id IS NOT NULL
ON CONFLICT (offer_id, scraped_at) DO NOTHING;

-- 6. Velocity view: computes change between latest two snapshots per product
CREATE OR REPLACE VIEW product_velocity AS
WITH ranked AS (
    SELECT
        offer_id,
        sales_volume_estimate,
        scraped_at,
        ROW_NUMBER() OVER (PARTITION BY offer_id ORDER BY scraped_at DESC) as rn
    FROM product_snapshots
    WHERE sales_volume_estimate IS NOT NULL
)
SELECT
    latest.offer_id,
    latest.sales_volume_estimate AS current_sales,
    prev.sales_volume_estimate AS previous_sales,
    latest.scraped_at AS latest_scrape,
    prev.scraped_at AS previous_scrape,
    (latest.sales_volume_estimate - COALESCE(prev.sales_volume_estimate, 0)) AS sales_delta,
    EXTRACT(DAY FROM (latest.scraped_at - prev.scraped_at))::INTEGER AS days_between,
    CASE
        WHEN prev.sales_volume_estimate IS NOT NULL
             AND EXTRACT(DAY FROM (latest.scraped_at - prev.scraped_at)) > 0
        THEN ROUND(
            (latest.sales_volume_estimate - prev.sales_volume_estimate)::NUMERIC
            / EXTRACT(DAY FROM (latest.scraped_at - prev.scraped_at)),
            1
        )
        ELSE NULL
    END AS daily_velocity
FROM ranked latest
LEFT JOIN ranked prev ON latest.offer_id = prev.offer_id AND prev.rn = 2
WHERE latest.rn = 1;

COMMENT ON VIEW product_velocity IS
    'Computed sales velocity per product. Compares latest vs previous snapshot. '
    'daily_velocity = sales_delta / days_between. NULL if only one snapshot exists.';
