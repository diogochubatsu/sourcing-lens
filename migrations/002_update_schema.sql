-- ArbitLens BR — Schema Update v0.2
-- Aligns migration with actual DB state (CLIP ViT-B-32, 512-dim)
-- Run after 001_initial_schema.sql or on existing DB

-- ============================================================
-- 1. Fix embedding column: vector(768) → vector(512)
-- ============================================================

-- Drop old index on wrong dimension
DROP INDEX IF EXISTS idx_products_embedding;

-- Alter column type if it exists as vector(768)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'products' AND column_name = 'image_embedding'
        AND udt_name = 'vector'
    ) THEN
        -- Check current dimension
        PERFORM ALTER COLUMN image_embedding TYPE vector(512)
            USING image_embedding::vector(512);
    END IF;
EXCEPTION WHEN OTHERS THEN
    -- Column may not exist or may already be correct
    NULL;
END $$;

-- Add 'embedding' column if it doesn't exist (alias for image_embedding)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'products' AND column_name = 'embedding'
    ) THEN
        ALTER TABLE products ADD COLUMN embedding vector(512);
    END IF;
END $$;

-- Copy data from image_embedding to embedding if needed
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'products' AND column_name = 'image_embedding'
    ) THEN
        UPDATE products SET embedding = image_embedding WHERE embedding IS NULL AND image_embedding IS NOT NULL;
    END IF;
END $$;

-- ============================================================
-- 2. Add hierarchical category columns
-- ============================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'products' AND column_name = 'category_l1'
    ) THEN
        ALTER TABLE products ADD COLUMN category_l1 VARCHAR(100);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'products' AND column_name = 'category_l2'
    ) THEN
        ALTER TABLE products ADD COLUMN category_l2 VARCHAR(100);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'products' AND column_name = 'category_l3'
    ) THEN
        ALTER TABLE products ADD COLUMN category_l3 VARCHAR(100);
    END IF;
END $$;

-- ============================================================
-- 3. Add title_translated if missing
-- ============================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'products' AND column_name = 'title_translated'
    ) THEN
        ALTER TABLE products ADD COLUMN title_translated TEXT;
    END IF;
END $$;

-- ============================================================
-- 4. Create price_history table
-- ============================================================

CREATE TABLE IF NOT EXISTS price_history (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    price DECIMAL(10,2),
    sales_30d INTEGER,
    recorded_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_price_history_product ON price_history(product_id);
CREATE INDEX IF NOT EXISTS idx_price_history_date ON price_history(recorded_at);

-- ============================================================
-- 5. Create alerts table
-- ============================================================

CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    title TEXT,
    message TEXT,
    alert_type VARCHAR(50),
    is_read BOOLEAN DEFAULT FALSE,
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alerts_unread ON alerts(is_read) WHERE is_read = FALSE;

-- ============================================================
-- 6. Create users table
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(200) UNIQUE NOT NULL,
    password_hash VARCHAR(200) NOT NULL,
    preferred_categories JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 7. Create favorites table
-- ============================================================

CREATE TABLE IF NOT EXISTS favorites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, product_id)
);

CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id);

-- ============================================================
-- 8. Create custom_alerts table
-- ============================================================

CREATE TABLE IF NOT EXISTS custom_alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL,
    threshold_value DECIMAL(10,2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_custom_alerts_user ON custom_alerts(user_id);

-- ============================================================
-- 9. Recreate HNSW index on embedding column
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_products_embedding
    ON products USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- ============================================================
-- 10. Add category hierarchy indexes
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_products_category_l1 ON products(category_l1);
CREATE INDEX IF NOT EXISTS idx_products_category_l3 ON products(category_l3);
CREATE INDEX IF NOT EXISTS idx_products_category_l1_l3 ON products(category_l1, category_l3);
