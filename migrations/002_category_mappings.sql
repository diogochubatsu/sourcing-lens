-- Category Mappings Table
-- Maps internal categories (L1/L2/L3) to platform-specific categories
-- Used to find best sellers URLs for scraping

CREATE TABLE IF NOT EXISTS category_mappings (
    id SERIAL PRIMARY KEY,
    our_l1 VARCHAR(100) NOT NULL,
    our_l2 VARCHAR(100) NOT NULL,
    our_l3 VARCHAR(100) NOT NULL,
    platform VARCHAR(20) NOT NULL,
    platform_category_id VARCHAR(100),
    platform_category_name TEXT,
    platform_category_path TEXT,
    bestsellers_url TEXT,
    confidence DECIMAL(3,2) DEFAULT 0.5,
    verified BOOLEAN DEFAULT FALSE,
    product_count INTEGER DEFAULT 0,
    last_scraped TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(our_l1, our_l2, our_l3, platform)
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_category_mappings_platform ON category_mappings(platform);
CREATE INDEX IF NOT EXISTS idx_category_mappings_l3 ON category_mappings(our_l1, our_l2, our_l3);
CREATE INDEX IF NOT EXISTS idx_category_mappings_verified ON category_mappings(verified) WHERE verified = TRUE;

-- Scrape queue for recursive discovery
CREATE TABLE IF NOT EXISTS scrape_queue (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(20) NOT NULL,
    platform_category_id VARCHAR(100),
    platform_category_name TEXT,
    bestsellers_url TEXT,
    priority INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    attempts INTEGER DEFAULT 0,
    last_attempt TIMESTAMP,
    error TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scrape_queue_status ON scrape_queue(status);
CREATE INDEX IF NOT EXISTS idx_scrape_queue_platform ON scrape_queue(platform);
