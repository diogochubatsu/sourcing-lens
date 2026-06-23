import { query, queryOne } from './db-pg';

export interface ScoutProduct {
  title: string;
  title_pt: string | null;
  price_min: number | null;
  repurchase_rate: number | null;
  sales_volume_estimate: number | null;
  moq_raw: string | null;
  supplier_name: string | null;
  category_label: string | null;
  category_label_pt: string | null;
  image_url: string | null;
  offer_id: string | null;
}

export interface ScoutCategory {
  category_label: string;
  category_label_pt: string | null;
  product_count: number;
  avg_repurchase: number;
  avg_price: number;
  total_sales: number;
}

export interface ProductVelocity {
  offer_id: string;
  current_sales: number | null;
  previous_sales: number | null;
  latest_scrape: string;
  previous_scrape: string | null;
  sales_delta: number | null;
  days_between: number | null;
  daily_velocity: number | null;
}

// ─── Category relevance constants ───
// Commodity categories: low-margin, oversaturated, boring for ML sellers.
// These get deprioritized in results.
const COMMODITY_CATEGORIES: string[] = [
  '手机保护套',     // Phone cases
  '运动休闲棉袜',   // Sports socks
  '垃圾袋',         // Trash bags
  '发圈',           // Hair ties
  '衣架',           // Hangers
  '收纳盒',         // Storage boxes
  '手机数据线',     // Phone cables
  '钥匙扣配件',     // Keychain accessories
  '抽纸',           // Tissues
  '纸箱',           // Cardboard boxes
  '收纳袋收纳包',   // Storage bags
  '发夹',           // Hair clips
  '毛绒公仔',       // Plush toys
  // Underwear basics — high repurchase but low margin, oversaturated on ML
  '男士内裤',       // Men's underwear (briefs)
  '女士内裤',       // Women's underwear (briefs)
  '男士平角裤',     // Men's boxer briefs
  '女士三角裤',     // Women's panties
  '文胸',           // Bras
  '袜子',           // Socks (generic)
  '丝袜/打底袜',    // Stockings/tights
  '儿童袜',         // Children's socks
  '保暖内衣',       // Thermal underwear
];

// High-value categories: high margin, exciting for ML sellers.
// These get boosted to the top of results.
const HIGH_VALUE_CATEGORIES: string[] = [
  '蓝牙耳机',       // Bluetooth earphones (¥38 avg, tech)
  '太阳镜',         // Sunglasses (¥21 avg, fashion)
  'USB风扇',        // USB fans (¥24 avg, gadgets)
  '玻璃杯',         // Glass cups (¥18 avg, home)
  '男式T恤',        // Men's T-shirts (¥43 avg, clothing)
  '男式休闲裤',     // Men's casual pants (¥69 avg, clothing)
];

// Scoring multipliers for relevance sorting
const HIGH_VALUE_BONUS = 2.0;   // 2x boost for high-value categories
const COMMODITY_PENALTY = 0.2;  // 5x penalty for commodity categories

/**
 * Build a SQL CASE expression for category-based relevance scoring.
 * Used in ORDER BY clauses to boost high-value products and deprioritize commodities.
 *
 * Formula: (repurchase_rate * COALESCE(sales_volume_estimate, 0)) * multiplier
 */
function categoryRelevanceSQL(): string {
  const bonus = String(HIGH_VALUE_BONUS);
  const penalty = String(COMMODITY_PENALTY);

  const highCases = HIGH_VALUE_CATEGORIES
    .map(cat => `WHEN category_label = '${cat}' THEN ${bonus}`)
    .join('\n            ');
  const commodityCases = COMMODITY_CATEGORIES
    .map(cat => `WHEN category_label = '${cat}' THEN ${penalty}`)
    .join('\n            ');

  return `
      (repurchase_rate * COALESCE(sales_volume_estimate, 0))
      * CASE
            ${highCases}
            ${commodityCases}
            ELSE 1.0
        END
  `.trim();
}

/**
 * Build a SQL WHERE fragment to exclude commodity categories.
 * Use for broad/exploratory queries where commodities add noise.
 */
function commodityExcludeSQL(alias?: string): string {
  const prefix = alias ? `${alias}.` : '';
  const cats = COMMODITY_CATEGORIES.map(c => `'${c}'`).join(', ');
  return `${prefix}category_label NOT IN (${cats})`;
}

// ─── Public API ───

/**
 * Search categories by keyword (Chinese or Portuguese).
 * Excludes commodity categories; high-value categories sort first.
 */
export async function searchCategories(queryStr: string): Promise<ScoutCategory[]> {
  const q = `%${queryStr.toLowerCase()}%`;
  return query<ScoutCategory>(`
    SELECT
      category_label,
      category_label_pt,
      COUNT(*) as product_count,
      AVG(repurchase_rate)::integer as avg_repurchase,
      AVG(price_min)::numeric(10,2) as avg_price,
      SUM(sales_volume_estimate) as total_sales
    FROM listing_products
    WHERE (
      LOWER(category_label) LIKE $1
      OR LOWER(category_label_pt) LIKE $1
      OR LOWER(title) LIKE $1
      OR LOWER(title_pt) LIKE $1
    )
    AND repurchase_rate IS NOT NULL
    AND ${commodityExcludeSQL()}
    GROUP BY category_label, category_label_pt
    ORDER BY
      CASE WHEN category_label IN (${HIGH_VALUE_CATEGORIES.map(c => `'${c}'`).join(',')}) THEN 0 ELSE 1 END,
      avg_repurchase DESC, total_sales DESC
    LIMIT 10
  `, [q]);
}

/**
 * Get top products from specific categories, ranked by relevance.
 * High-value categories get boosted; commodity categories get penalized.
 */
export async function getTopProducts(
  categoryLabels: string[],
  limit: number = 30
): Promise<ScoutProduct[]> {
  if (categoryLabels.length === 0) return [];
  const relevance = categoryRelevanceSQL();
  return query<ScoutProduct>(`
    SELECT
      title, title_pt, price_min, repurchase_rate,
      sales_volume_estimate, moq_raw, supplier_name,
      category_label, category_label_pt, image_url, offer_id
    FROM listing_products
    WHERE category_label = ANY($1)
      AND repurchase_rate IS NOT NULL
      AND price_min IS NOT NULL
      AND price_min > 0
    ORDER BY ${relevance} DESC
    LIMIT $2
  `, [categoryLabels, limit]);
}

/**
 * Get all categories with summary stats for context.
 * Excludes commodity categories; high-value categories sort first.
 */
export async function getAllCategories(): Promise<ScoutCategory[]> {
  return query<ScoutCategory>(`
    SELECT
      category_label,
      category_label_pt,
      COUNT(*) as product_count,
      AVG(repurchase_rate)::integer as avg_repurchase,
      AVG(price_min)::numeric(10,2) as avg_price,
      SUM(sales_volume_estimate) as total_sales
    FROM listing_products
    WHERE repurchase_rate IS NOT NULL
      AND ${commodityExcludeSQL()}
    GROUP BY category_label, category_label_pt
    ORDER BY
      CASE WHEN category_label IN (${HIGH_VALUE_CATEGORIES.map(c => `'${c}'`).join(',')}) THEN 0 ELSE 1 END,
      total_sales DESC
  `);
}

/**
 * Free-text product search — searches titles with category relevance boosting.
 * High-value categories rank higher; commodity categories rank lower.
 */
export async function searchProducts(queryStr: string, limit: number = 20): Promise<ScoutProduct[]> {
  const q = `%${queryStr.toLowerCase()}%`;
  const relevance = categoryRelevanceSQL();
  return query<ScoutProduct>(`
    SELECT
      title, title_pt, price_min, repurchase_rate,
      sales_volume_estimate, moq_raw, supplier_name,
      category_label, category_label_pt, image_url, offer_id
    FROM listing_products
    WHERE (
      LOWER(title) LIKE $1
      OR LOWER(title_pt) LIKE $1
    )
    AND repurchase_rate IS NOT NULL
    ORDER BY ${relevance} DESC
    LIMIT $2
  `, [q, limit]);
}

// ─── Time-series / Velocity ───

/**
 * Save a snapshot of products for time-series tracking.
 * Call this after each scrape run to enable velocity computation.
 *
 * Uses ON CONFLICT to avoid duplicates (same offer_id + scraped_at).
 */
export async function saveProductSnapshot(
  products: Array<{
    offer_id: string;
    title?: string | null;
    sales_volume_estimate?: number | null;
    price_min?: number | null;
    repurchase_rate?: number | null;
    category_label?: string | null;
    supplier_name?: string | null;
  }>,
  snapshotSource: string = 'scrape'
): Promise<number> {
  if (products.length === 0) return 0;

  const values: any[] = [];
  const placeholders: string[] = [];
  let idx = 1;

  for (const p of products) {
    if (!p.offer_id) continue;
    placeholders.push(`($${idx}, $${idx+1}, $${idx+2}, $${idx+3}, $${idx+4}, $${idx+5}, $${idx+6}, NOW(), $${idx+7})`);
    values.push(
      p.offer_id,
      p.title || null,
      p.sales_volume_estimate ?? null,
      p.price_min ?? null,
      p.repurchase_rate ?? null,
      p.category_label || null,
      p.supplier_name || null,
      snapshotSource
    );
    idx += 8;
  }

  if (placeholders.length === 0) return 0;

  const sql = `
    INSERT INTO product_snapshots
      (offer_id, title, sales_volume_estimate, price_min, repurchase_rate, category_label, supplier_name, scraped_at, snapshot_source)
    VALUES ${placeholders.join(', ')}
    ON CONFLICT (offer_id, scraped_at) DO NOTHING
  `;

  const result = await query(sql, values);
  return placeholders.length;
}

/**
 * Get velocity data for specific products (by offer_id).
 * Returns products that have at least 2 snapshots.
 */
export async function getProductVelocity(
  offerIds: string[]
): Promise<Map<string, ProductVelocity>> {
  if (offerIds.length === 0) return new Map();

  const rows = await query<ProductVelocity>(`
    SELECT * FROM product_velocity
    WHERE offer_id = ANY($1)
      AND daily_velocity IS NOT NULL
  `, [offerIds]);

  const map = new Map<string, ProductVelocity>();
  for (const row of rows) {
    map.set(row.offer_id, row);
  }
  return map;
}

/**
 * Get trending products — those with highest positive velocity.
 * Only returns products with ≥2 snapshots and positive delta.
 */
export async function getTrendingProducts(
  limit: number = 10
): Promise<Array<ProductVelocity & { title: string; category_label: string }>> {
  return query(`
    SELECT
      v.offer_id,
      v.current_sales,
      v.previous_sales,
      v.sales_delta,
      v.days_between,
      v.daily_velocity,
      v.latest_scrape,
      v.previous_scrape,
      lp.title,
      lp.category_label
    FROM product_velocity v
    JOIN listing_products lp ON lp.offer_id = v.offer_id
    WHERE v.daily_velocity IS NOT NULL
      AND v.sales_delta > 0
    ORDER BY v.daily_velocity DESC
    LIMIT $1
  `, [limit]);
}

/**
 * Get velocity context summary for the Scout prompt.
 * Returns a human-readable string summarizing time-series data availability.
 */
export async function getVelocityContext(): Promise<{
  hasVelocityData: boolean;
  totalSnapshots: number;
  uniqueProducts: number;
  latestScrapeDate: string | null;
  productsWithVelocity: number;
  topTrending: Array<{ offer_id: string; title: string; daily_velocity: number; sales_delta: number }>;
}> {
  const stats = await queryOne<{
    total_snapshots: number;
    unique_products: number;
    latest_scrape: string | null;
  }>(`
    SELECT
      COUNT(*) as total_snapshots,
      COUNT(DISTINCT offer_id) as unique_products,
      MAX(scraped_at)::text as latest_scrape
    FROM product_snapshots
  `);

  const velocityCount = await queryOne<{ count: number }>(`
    SELECT COUNT(*) as count FROM product_velocity WHERE daily_velocity IS NOT NULL
  `);

  const topTrending = await query<{
    offer_id: string;
    title: string;
    daily_velocity: number;
    sales_delta: number;
  }>(`
    SELECT v.offer_id, lp.title, v.daily_velocity, v.sales_delta
    FROM product_velocity v
    JOIN listing_products lp ON lp.offer_id = v.offer_id
    WHERE v.daily_velocity IS NOT NULL AND v.sales_delta > 0
    ORDER BY v.daily_velocity DESC
    LIMIT 5
  `);

  return {
    hasVelocityData: (velocityCount?.count ?? 0) > 0,
    totalSnapshots: stats?.total_snapshots ?? 0,
    uniqueProducts: stats?.unique_products ?? 0,
    latestScrapeDate: stats?.latest_scrape ?? null,
    productsWithVelocity: velocityCount?.count ?? 0,
    topTrending,
  };
}
