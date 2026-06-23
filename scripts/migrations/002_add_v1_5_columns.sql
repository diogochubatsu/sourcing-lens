-- Migration: Add v1.5 columns to factory_products
-- Applied after v1.5 API deployment

ALTER TABLE factory_products
  ADD COLUMN IF NOT EXISTS main_spec TEXT,
  ADD COLUMN IF NOT EXISTS specifications JSONB,
  ADD COLUMN IF NOT EXISTS models JSONB,
  ADD COLUMN IF NOT EXISTS variant_prices JSONB,
  ADD COLUMN IF NOT EXISTS video_url TEXT,
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;

-- Optional: index for updated_at (for incremental scans)
CREATE INDEX IF NOT EXISTS idx_factory_products_updated_at ON factory_products(updated_at);
