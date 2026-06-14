-- ArbitLens BR (arbtbr) — Schema v2
-- Database: arbtbr on PostgreSQL
-- Updated: 2026-06-14

-- Enable pgvector for image embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Products table (all platforms: ML, Amazon BR/US)
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(20) NOT NULL,
    platform_id VARCHAR(100) NOT NULL,
    title TEXT NOT NULL,
    title_translated TEXT,
    price DECIMAL(10,2),
    currency VARCHAR(5),
    url TEXT,
    image_urls TEXT[],
    local_images TEXT[],
    embedding vector(512),
    image_hash VARCHAR(64),
    supplier_name VARCHAR(200),
    moq INTEGER,
    sales_total INTEGER,
    sales_30d INTEGER,
    review_count INTEGER,
    review_avg DECIMAL(3,2),
    category VARCHAR(100),
    category_l1 VARCHAR(100),
    category_l2 VARCHAR(100),
    category_l3 VARCHAR(100),
    bsr_rank INTEGER,
    tags TEXT[],
    is_active BOOLEAN DEFAULT TRUE,
    first_seen TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW(),
    raw_data JSONB,
    UNIQUE(platform, platform_id)
);

-- Cross-platform matches
CREATE TABLE IF NOT EXISTS matches (
    id SERIAL PRIMARY KEY,
    product_a_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    product_b_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    confidence DECIMAL(5,4),
    match_method VARCHAR(20),
    user_verified BOOLEAN,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(product_a_id, product_b_id)
);

-- Price history (daily snapshots)
CREATE TABLE IF NOT EXISTS price_history (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    price DECIMAL(10,2),
    sales_30d INTEGER,
    recorded_at TIMESTAMP DEFAULT NOW()
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(200) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    preferred_categories JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Favorites
CREATE TABLE IF NOT EXISTS favorites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, product_id)
);

-- Alerts
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    alert_type VARCHAR(50),
    message TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Custom alerts (user-defined price/condition alerts)
CREATE TABLE IF NOT EXISTS custom_alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    alert_type VARCHAR(50),
    threshold_value DECIMAL(10,2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Import cost factors
CREATE TABLE IF NOT EXISTS import_factors (
    id SERIAL PRIMARY KEY,
    country VARCHAR(5) NOT NULL,
    quantity_min INTEGER,
    quantity_max INTEGER,
    factor DECIMAL(4,2),
    notes TEXT,
    UNIQUE(country, quantity_min, quantity_max)
);

-- User watchlists
CREATE TABLE IF NOT EXISTS watchlists (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    alert_price_change BOOLEAN DEFAULT TRUE,
    alert_velocity_change BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Scrape job tracking
CREATE TABLE IF NOT EXISTS scrape_jobs (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(20) NOT NULL,
    query TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    items_found INTEGER DEFAULT 0,
    items_saved INTEGER DEFAULT 0,
    error TEXT,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_products_platform ON products(platform);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_category_l1 ON products(category_l1);
CREATE INDEX IF NOT EXISTS idx_products_category_l3 ON products(category_l3);
CREATE INDEX IF NOT EXISTS idx_products_hash ON products(image_hash);
CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_products_embedding ON products USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_matches_confidence ON matches(confidence DESC);
CREATE INDEX IF NOT EXISTS idx_matches_pair ON matches(product_a_id, product_b_id);
CREATE INDEX IF NOT EXISTS idx_matches_method ON matches(match_method);
CREATE INDEX IF NOT EXISTS idx_price_history_product ON price_history(product_id);
CREATE INDEX IF NOT EXISTS idx_price_history_date ON price_history(recorded_at);
CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- Seed import factors
INSERT INTO import_factors (country, quantity_min, quantity_max, factor, notes) VALUES
('BR', 1, 50, 3.50, 'Small order, high per-unit shipping + import tax'),
('BR', 51, 200, 3.00, 'Better shipping rates'),
('BR', 201, 500, 2.60, 'Container sharing possible'),
('BR', 501, 1000, 2.30, 'Bulk rates, best for Brazil'),
('US', 1, 50, 2.80, 'Small order'),
('US', 51, 200, 2.30, 'Better rates'),
('US', 201, 500, 2.00, 'Container sharing'),
('US', 501, 1000, 1.80, 'Bulk rates')
ON CONFLICT (country, quantity_min, quantity_max) DO NOTHING;
