-- Migration 003: Add sales_velocity to ml_bestsellers
-- sales_velocity = total_sales / days_since_publish
-- Applied to PostgreSQL (Cloud SQL intel-postgres)

-- 1. Add the column
ALTER TABLE ml_bestsellers
  ADD COLUMN IF NOT EXISTS sales_velocity NUMERIC;

COMMENT ON COLUMN ml_bestsellers.sales_velocity IS
    'Sales velocity: total_sales / GREATEST(days_since_publish, 1). '
    'Calculated at scrape time and refreshed via refresh_sales_velocity().';

-- 2. Function to compute sales_velocity for a single row
CREATE OR REPLACE FUNCTION calc_sales_velocity(
    p_total_sales INTEGER,
    p_publish_date TIMESTAMPTZ
) RETURNS NUMERIC AS $$
BEGIN
    IF p_total_sales IS NULL OR p_publish_date IS NULL THEN
        RETURN NULL;
    END IF;
    -- days_since_publish >= 1 to avoid division by zero
    RETURN p_total_sales::NUMERIC / GREATEST(
        EXTRACT(DAY FROM (NOW() - p_publish_date))::INTEGER,
        1
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 3. Function to backfill/refresh all rows
CREATE OR REPLACE FUNCTION refresh_sales_velocity() RETURNS INTEGER AS $$
DECLARE
    updated INTEGER;
BEGIN
    UPDATE ml_bestsellers
    SET sales_velocity = calc_sales_velocity(total_sales, publish_date)
    WHERE total_sales IS NOT NULL
      AND publish_date IS NOT NULL;
    GET DIAGNOSTICS updated = ROW_COUNT;
    RETURN updated;
END;
$$ LANGUAGE plpgsql;

-- 4. Backfill existing data
SELECT refresh_sales_velocity();

-- 5. Index for velocity-based queries (top sellers by velocity)
CREATE INDEX IF NOT EXISTS idx_ml_bestsellers_velocity
    ON ml_bestsellers (sales_velocity DESC NULLS LAST);

-- 6. Optional: dynamic view for always-fresh velocity
CREATE OR REPLACE VIEW ml_bestsellers_live AS
SELECT
    *,
    calc_sales_velocity(total_sales, publish_date) AS velocity_live
FROM ml_bestsellers;

COMMENT ON VIEW ml_bestsellers_live IS
    'Live view of ml_bestsellers with dynamically recalculated sales_velocity.';
