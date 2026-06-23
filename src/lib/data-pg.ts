import * as fs from 'fs';
import * as path from 'path';
import { query, queryOne } from './db-pg';
import type {
  ListingProduct,
  RankedStore,
  RunInfo,
  RunSummary,
  SupplierProfile,
} from '@/types';

// ─── helpers (same as data.ts, no DB calls) ───

const CATEGORY_ID_TO_LABEL: Record<string, string> = {
  '315': '男式T恤',
  '1753': '饰品配件',
  '1829': '成人帽',
  '10340': '钥匙扣配件',
  '1031871': '休闲裤',
  '1031890': '男式休闲裤',
  '1031910': '连衣裙',
  '1031912': '半身裙',
  '1031918': '女式衬衫',
  '1031919': '女式T恤',
  '1031920': '背心吊带抹胸',
  '1031922': '太阳镜',
  '1033007': '纸箱',
  '1033762': '温室大棚',
  '1034008': '手机数据线',
  '1035635': '垃圾袋',
  '1036894': '收纳袋收纳包',
  '1037192': '童套装',
  '1037268': '手链',
  '1037271': '耳钉',
  '1037275': '项链',
  '1037859': '女士三角裤',
  '1042207': '手机保护套',
  '1043982': '收纳盒',
  '1045066': 'USB风扇',
  '1048186': '蓝牙耳机',
  '1048256': '时尚休闲套装',
  '122328006': '衣架',
  '122398006': '抽纸',
  '122438003': '运动休闲棉袜',
  '122452001': '男士平角裤',
  '122700006': '耳环',
  '122706005': '戒指',
  '122710002': '发圈',
  '122722001': '发夹',
  '122986002': '毛绒公仔',
  '125278007': '玻璃杯',
  '201548713': 'EVA拖鞋',
  '201554511': '女士单肩包',
  '1031872': '女士家居服',
  '1048282': '女式连衣裙',
};

function findProjectRoot(): string {
  if (fs.existsSync(path.join(process.cwd(), 'scripts'))) {
    return process.cwd();
  }
  return path.resolve(process.cwd(), '..', '..');
}

function findDataRoot(): string {
  if (process.env.DATA_DIR) {
    return process.env.DATA_DIR;
  }
  const projectRoot = findProjectRoot();
  const candidates = [path.join(projectRoot, 'data', '1688')];
  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) return candidate;
  }
  return path.join(projectRoot, 'data', '1688');
}

export function dataRoot(): string {
  return findDataRoot();
}

function loadTranslations(): {
  products: Record<string, string>;
  suppliers: Record<string, string>;
} {
  const p = path.join(dataRoot(), 'rankings', 'translations.json');
  try {
    const raw = JSON.parse(fs.readFileSync(p, 'utf-8'));
    return { products: raw.products ?? {}, suppliers: raw.suppliers ?? {} };
  } catch {
    return { products: {}, suppliers: {} };
  }
}

function normalizeText(value: unknown): string {
  return typeof value === 'string' ? value.trim() : '';
}

function toStringOrNull(value: unknown): string | null {
  return typeof value === 'string' && value.trim() ? value : null;
}

function dedupeBy<T>(items: T[], keyFn: (item: T) => string): T[] {
  const seen = new Set<string>();
  return items.filter((item) => {
    const key = keyFn(item);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function uniqueStrings(
  values: Array<string | null | undefined>
): string[] {
  return Array.from(
    new Set(
      values.filter((value): value is string => Boolean(value && value.trim()))
    )
  );
}

function formatSalesValue(value: unknown): string | null {
  if (typeof value === 'number' && Number.isFinite(value)) return String(value);
  if (typeof value !== 'string' || !value.trim()) return null;
  const cleaned = value.replace(/^热销/, '');
  const wanMatch = cleaned.match(/^(\d+(?:\.\d+)?)万(\+?)$/);
  if (wanMatch) {
    const num = Math.round(parseFloat(wanMatch[1]) * 10000);
    return `${num.toLocaleString('en-US')}${wanMatch[2]}`;
  }
  if (/^\d+\+?$/.test(cleaned)) return cleaned;
  return value;
}

const CITY_TO_PROVINCE: Record<string, string> = {
  东莞: '广东',
  义乌: '浙江',
  青岛: '山东',
  湖州: '浙江',
  浙江: '浙江',
  汕头: '广东',
  广州: '广东',
  商丘: '河南',
  杭州: '浙江',
  普宁: '广东',
  广东: '广东',
  嘉兴: '浙江',
  中山: '广东',
  苏州: '江苏',
  深圳: '广东',
  桐乡: '浙江',
  安阳: '河南',
  东阳: '浙江',
  长沙: '湖南',
  绍兴: '浙江',
  湖北: '湖北',
  海丰: '广东',
  河南: '河南',
  昆山: '江苏',
  无锡: '江苏',
  常州: '江苏',
  天台: '浙江',
  厦门: '福建',
  佛山: '广东',
  上海: '上海',
};

const CHINESE_PROVINCE_TO_EN: Record<string, string> = {
  北京: 'Beijing',
  天津: 'Tianjin',
  上海: 'Shanghai',
  重庆: 'Chongqing',
  河北: 'Hebei',
  山西: 'Shanxi',
  辽宁: 'Liaoning',
  吉林: 'Jilin',
  黑龙江: 'Heilongjiang',
  江苏: 'Jiangsu',
  浙江: 'Zhejiang',
  安徽: 'Anhui',
  福建: 'Fujian',
  江西: 'Jiangxi',
  山东: 'Shandong',
  河南: 'Henan',
  湖北: 'Hubei',
  湖南: 'Hunan',
  广东: 'Guangdong',
  海南: 'Hainan',
  四川: 'Sichuan',
  贵州: 'Guizhou',
  云南: 'Yunnan',
  陕西: 'Shaanxi',
  甘肃: 'Gansu',
  青海: 'Qinghai',
  台湾: 'Taiwan',
  内蒙古: 'Inner Mongolia',
  广西: 'Guangxi',
  西藏: 'Tibet',
  宁夏: 'Ningxia',
  新疆: 'Xinjiang',
  香港: 'Hong Kong',
  澳门: 'Macau',
};

export function extractProvince(supplierName: string | null): string | null {
  if (!supplierName || supplierName === 'Unknown') return null;
  for (const [city, province] of Object.entries(CITY_TO_PROVINCE)) {
    if (supplierName.startsWith(city)) {
      const provinceEn = CHINESE_PROVINCE_TO_EN[province] ?? province;
      return provinceEn;
    }
  }
  return null;
}

function cleanBadge(badge: string): string {
  const idx = badge.indexOf('](');
  return idx >= 0 ? badge.slice(0, idx) : badge;
}

const BADGE_TO_RANK_TYPE: Record<string, string> = {
  实力榜: 'power',
  热度榜: 'hot',
  服务榜: 'serve',
  新晋榜: 'new',
};

function rankingKey(row: RankedStore): string {
  return row.supplier_id ?? row.member_id ?? row.supplier_name;
}

function productKey(row: ListingProduct): string {
  return (
    row.offer_id ??
    `${row.title ?? ''}|${row.supplier_name ?? ''}|${row.keyword ?? ''}`
  );
}

// ─── DB-backed Data fetchers (PostgreSQL async versions) ───

export async function listRankingRuns(): Promise<RunInfo[]> {
  const rows = await query(
    `SELECT * FROM runs WHERE kind = 'rankings' ORDER BY id DESC`
  );
  return rows.map((row) => ({
    id: row.id,
    path: row.path,
    updated_at: row.updated_at,
    count: row.count,
    summary: row.summary_json ? (() => { try { return JSON.parse(row.summary_json); } catch { return null; } })() : null,
  }));
}

export async function listBestsellerRuns(): Promise<RunInfo[]> {
  const rows = await query(
    `SELECT * FROM runs WHERE kind = 'bestsellers' ORDER BY id DESC`
  );
  return rows.map((row) => ({
    id: row.id,
    path: row.path,
    updated_at: row.updated_at,
    count: row.count,
    summary: row.summary_json ? (() => { try { return JSON.parse(row.summary_json); } catch { return null; } })() : null,
  }));
}

export async function getRankings(
  runId?: string | null
): Promise<RankedStore[]> {
  let targetRunId = runId;
  if (!targetRunId) {
    const runs = await listRankingRuns();
    targetRunId = runs.length > 0 ? runs[0].id : null;
  }

  if (!targetRunId) return [];

  // Build title→title_pt lookup from listing_products (DB has 2027/2040 populated)
  const titlePtRows = await query(
    `SELECT DISTINCT title, title_pt FROM listing_products WHERE title_pt IS NOT NULL AND title_pt != ''`
  );
  const titlePtMap = new Map<string, string>(
    titlePtRows.map((r: any) => [r.title, r.title_pt])
  );

  const rows = await query(
    `SELECT * FROM ranked_suppliers
     WHERE run_id = $1 AND run_kind = 'rankings'
     ORDER BY rank_position ASC`,
    [targetRunId]
  );

  return rows.map((row) => {
    const top_products = row.top_products_json
      ? JSON.parse(row.top_products_json)
      : [];
    return {
      rank: row.rank_position,
      consecutive_years: row.consecutive_years,
      supplier_name: row.supplier_name,
      supplier_name_pt: null,
      ranking_type: row.ranking_type ?? null,
      category_label: row.category_label ?? null,
      category_label_pt: row.category_label_pt ?? null,
      category_id: row.category_id ?? null,
      region: row.region ?? null,
      supplier_id: row.supplier_key,
      member_id: row.supplier_key,
      source_method: null,
      years_in_operation: row.years_in_operation,
      repurchase_rate: row.repurchase_rate,
      response_rate: row.response_rate,
      monthly_sales: row.monthly_sales_raw,
      top_products: top_products.map((p: any) => ({
        ...p,
        title: p.title ?? null,
        title_pt: (p.title && titlePtMap.get(p.title)) ?? p.title_pt ?? null,
      })),
      review_snippet: row.review_snippet,
      source_url: row.source_url,
      source_label: null,
      page_title: row.page_title,
      scraped_at: row.scraped_at,
    };
  });
}

export async function getBestsellers(
  runId?: string | null
): Promise<ListingProduct[]> {
  let targetRunId = runId;
  if (!targetRunId) {
    const runs = await listBestsellerRuns();
    targetRunId = runs.length > 0 ? runs[0].id : null;
  }

  if (!targetRunId) return [];

  const rows = await query(
    `SELECT * FROM listing_products
     WHERE run_id = $1 AND run_kind = 'bestsellers'`,
    [targetRunId]
  );

  const products = rows.map((row) => ({
    row_id: Number(row.row_id),
    offer_id: row.offer_id,
    title: row.title,
    title_pt: row.title_pt ?? null,
    product_id: row.offer_id,
    price_min: Number.isFinite(Number(row.price_min)) ? Number(row.price_min) : null,
    price_raw: row.price_raw,
    moq_raw: row.moq_raw,
    image_url: row.image_url,
    supplier_name: row.supplier_name,
    supplier_name_pt: null,
    supplier_url: row.supplier_url,
    supplier_id: null,
    region: null,
    category_label: row.category_label ?? null,
    category_label_pt: row.category_label_pt ?? null,
    category_name: null,
    product_url: row.supplier_url,
    sales_volume: row.sales_volume_raw,
    repurchase_rate: row.repurchase_rate,
    rating: null,
    category: null,
    main_specification: null,
    models: null,
    specifications: null,
    model_options: null,
    variant_prices: null,
    moq: row.moq_raw,
    source_url: row.supplier_url,
    ranking_badge: row.ranking_badge,
    category_ids: row.category_ids,
    keyword: row.keyword,
    page: row.page,
    sort: row.sort,
    scraped_at: row.scraped_at,
  }));

  return dedupeBy(
    products,
    (item) =>
      item.offer_id ??
      `${item.title ?? ''}|${item.supplier_name ?? ''}|${item.keyword ?? ''}`
  );
}


// ============================================================================
// Phase 2 — /products UI upgrade helpers
// ============================================================================

export async function listAllCategories(): Promise<Array<{label: string; label_pt: string | null; count: number}>> {
  const sql = `
    SELECT label, label_pt, SUM(count) as count
    FROM (
      -- Listing products (curated categories with PT)
      SELECT 
        category_label as label,
        category_label_pt as label_pt,
        COUNT(*) as count
      FROM listing_products
      WHERE category_label IS NOT NULL AND TRIM(category_label) != ''
      GROUP BY category_label, category_label_pt

      UNION ALL

      -- Factory products (raw categories, now PT-translated)
      SELECT 
        product_category as label,
        product_category_pt as label_pt,
        COUNT(*) as count
      FROM factory_products
      WHERE product_category IS NOT NULL AND TRIM(product_category) != ''
      GROUP BY product_category, product_category_pt
    ) combined
    GROUP BY label, label_pt
    ORDER BY count DESC
  `;
  const raw = query(sql) as Promise<Array<{label: string; label_pt: string | null; count: number}>>;
  return (await raw).map(r => ({ label: r.label, label_pt: r.label_pt, count: r.count }));
}

export async function getCategoryStats(categoryId?: string): Promise<Array<{
  category_label: string;
  category_label_pt: string;
  product_count: number;
  supplier_count: number;
  avg_price_min: number | null;
  avg_sales_volume: number | null;
  avg_repurchase_rate: number | null;
}>> {
  const statsSql = `
    SELECT
      category_label,
      category_label_pt,
      COUNT(*) as product_count,
      COUNT(DISTINCT supplier_name) as supplier_count,
      ROUND(AVG(price_min), 2) as avg_price_min,
      ROUND(AVG(sales_volume_estimate), 2) as avg_sales_volume,
      ROUND(AVG(repurchase_rate), 1) as avg_repurchase_rate
    FROM listing_products
    WHERE category_label IS NOT NULL AND TRIM(category_label) != ''
      AND price_min IS NOT NULL AND price_min != 'NaN'::numeric
  `;

  if (categoryId) {
    const sql = statsSql + ` AND category_label = $1 GROUP BY category_label, category_label_pt`;
    return query(sql, [categoryId]) as Promise<Array<{
      category_label: string;
      category_label_pt: string;
      product_count: number;
      supplier_count: number;
      avg_price_min: number | null;
      avg_sales_volume: number | null;
      avg_repurchase_rate: number | null;
    }>>;
  }

  const sql = statsSql + ` GROUP BY category_label, category_label_pt ORDER BY product_count DESC`;
  return query(sql) as Promise<Array<{
    category_label: string;
    category_label_pt: string;
    product_count: number;
    supplier_count: number;
    avg_price_min: number | null;
    avg_sales_volume: number | null;
    avg_repurchase_rate: number | null;
  }>>;
}

export async function listRegions(_groupByProvince?: boolean): Promise<Array<{region: string; count: number; province?: string}>> {
  // Always return region-level counts; if province grouping is desired, the caller can aggregate client-side
  const sql = `
    SELECT region, COUNT(*) as count
    FROM ranked_suppliers
    WHERE region IS NOT NULL AND TRIM(region) != ''
    GROUP BY region
    ORDER BY region
  `;
  return query(sql) as Promise<Array<{region: string; count: number}>>;
}

// Enrichment queue: products with null or garbage titles
export async function getEnrichmentQueue(): Promise<(ListingProduct & { row_id: number })[]> {
  // Use latest bestsellers run (most relevant for product titles)
  const runs = await listBestsellerRuns();
  const targetRunId = runs.length > 0 ? runs[0].id : null;
  if (!targetRunId) return [];

  const rows = await query(
    `SELECT * FROM listing_products
     WHERE run_id = $1 AND run_kind = 'bestsellers'
       AND (title IS NULL OR title = '全球领先的采购批发平台,批发网')
     ORDER BY row_id ASC`,
    [targetRunId]
  );

  return rows.map((row) => ({
    row_id: Number(row.row_id), // row_id stored as TEXT but numeric
    offer_id: row.offer_id,
    title: row.title,
    title_pt: row.title_pt ?? null,
    product_id: row.offer_id,
    price_min: Number.isFinite(Number(row.price_min)) ? Number(row.price_min) : null,
    price_raw: row.price_raw,
    moq_raw: row.moq_raw,
    image_url: row.image_url,
    supplier_name: row.supplier_name,
    supplier_name_pt: null,
    supplier_url: row.supplier_url,
    supplier_id: null,
    region: null,
    category_label: row.category_label ?? null,
    category_label_pt: row.category_label_pt ?? null,
    category_name: null,
    product_url: row.supplier_url,
    sales_volume: row.sales_volume_raw,
    repurchase_rate: row.repurchase_rate,
    rating: null,
    category: null,
    main_specification: null,
    models: null,
    specifications: null,
    model_options: null,
    variant_prices: null,
    moq: row.moq_raw,
    source_url: row.supplier_url,
    ranking_badge: row.ranking_badge,
    category_ids: row.category_ids,
    keyword: row.keyword,
    page: row.page,
    sort: row.sort,
    scraped_at: row.scraped_at,
  }));
}

export async function getMeta() {
  let rankingRuns: RunInfo[] = [];
  let bestsellerRuns: RunInfo[] = [];
  let categories: Array<{label: string; label_pt: string | null; count: number}> = [];
  let regions: Array<{region: string; count: number; province?: string}> = [];

  try {
    rankingRuns = await listRankingRuns();
  } catch (e) { console.error('listRankingRuns failed:', e); }
  try {
    bestsellerRuns = await listBestsellerRuns();
  } catch (e) { console.error('listBestsellerRuns failed:', e); }
  try {
    categories = await listAllCategories();
  } catch (e) { console.error('listAllCategories failed:', e); }
  try {
    regions = await listRegions(false);
  } catch (e) { console.error('listRegions failed:', e); }

  return {
    service: '1688-intel',
    data_root: dataRoot(),
    rankings: {
      runs: rankingRuns.length,
      latest_run: rankingRuns[0] ?? null,
      total_records_latest: rankingRuns[0]?.count ?? 0,
      top_ranking_types: [],
      top_categories: [],
    },
    bestsellers: {
      runs: bestsellerRuns.length,
      latest_run: bestsellerRuns[0] ?? null,
      total_records_latest: bestsellerRuns[0]?.count ?? 0,
      sample_keywords: [],
    },
    categories,
    regions,
  };
}

export function listValidCategories(): { cn: string; pt: string }[] {
  return [
    { cn: '抽纸', pt: 'Lenços de papel' },
    { cn: '连衣裙', pt: 'Vestidos' },
    { cn: '饰品配件', pt: 'Acessórios de bijuteria' },
    { cn: '女式T恤', pt: 'Camisetas femininas' },
    { cn: '女士三角裤', pt: 'Calcinha feminina' },
    { cn: '项链', pt: 'Colares' },
    { cn: '发夹', pt: 'Presilhas de cabelo' },
    { cn: '休闲裤', pt: 'Calças casuais' },
    { cn: 'USB风扇', pt: 'Ventilador USB' },
    { cn: '成人帽', pt: 'Chapéus adultos' },
    { cn: '男式T恤', pt: 'Camisetas masculinas' },
    { cn: '手链', pt: 'Pulseiras' },
    { cn: '运动休闲棉袜', pt: 'Meias de algodão esportivas/casuais' },
    { cn: '蓝牙耳机', pt: 'Fones Bluetooth' },
    { cn: '收纳盒', pt: 'Caixas organizadoras' },
    { cn: '垃圾袋', pt: 'Sacos de lixo' },
    { cn: '女士单肩包', pt: 'Bolsas femininas de ombro' },
    { cn: '女式衬衫', pt: 'Camisas femininas' },
    { cn: '男式休闲裤', pt: 'Calças casuais masculinas' },
    { cn: '耳钉', pt: 'Brincos tipo pino' },
    { cn: '毛绒公仔', pt: 'Pelúcias' },
    { cn: '耳环', pt: 'Brincos' },
    { cn: '时尚休闲套装', pt: 'Conjuntos casuais fashion' },
    { cn: '半身裙', pt: 'Saias' },
    { cn: '收纳袋收纳包', pt: 'Sacolas e bolsas organizadoras' },
    { cn: '手机数据线', pt: 'Cabos de dados para celular' },
    { cn: '背心吊带抹胸', pt: 'Regatas, tops e bustiês' },
    { cn: '钥匙扣配件', pt: 'Acessórios para chaveiros' },
    { cn: '戒指', pt: 'Anéis' },
    { cn: '衣架', pt: 'Cabides' },
    { cn: '童套装', pt: 'Conjuntos infantis' },
    { cn: '男士平角裤', pt: 'Cuecas boxer masculinas' },
    { cn: '发圈', pt: 'Elásticos de cabelo' },
    { cn: '手机保护套', pt: 'Capas de celular' },
    { cn: 'EVA拖鞋', pt: 'Chinelos EVA' },
    { cn: '玻璃杯', pt: 'Copos de vidro' },
    { cn: '纸箱', pt: 'Caixas de papelão' },
    { cn: '女士家居服', pt: 'Roupas para casa femininas' },
    { cn: '太阳镜', pt: 'Óculos de sol' },
    { cn: '温室大棚', pt: 'Estufas agrícolas' },
  ];
}

export async function listRankingCategories(
  runId?: string | null
): Promise<string[]> {
  const fromData = uniqueStrings(
    (await getRankings(runId)).map((row) => row.category_label)
  );
  const fromCsv = listValidCategories().map((c) => c.cn);
  return uniqueStrings([...fromData, ...fromCsv]);
}

export async function listRankingRegions(
  runId?: string | null
): Promise<string[]> {
  return uniqueStrings((await getRankings(runId)).map((row) => row.region));
}

export async function listBestsellerCategories(
  runId?: string | null
): Promise<string[]> {
  return uniqueStrings(
    (await getBestsellers(runId)).flatMap((row) => [
      row.category_label,
      row.category_name,
      row.category_ids,
    ])
  );
}

export async function listBestsellerRegions(
  runId?: string | null
): Promise<string[]> {
  return uniqueStrings((await getBestsellers(runId)).map((row) => row.region));
}

export async function getSupplierProfile(
  supplierIdOrName: string
): Promise<SupplierProfile> {
  const normalized = normalizeText(supplierIdOrName).toLowerCase();
  const rankings = await getRankings();
  const products = await getBestsellers();

  let ranking: RankedStore | null = null;
  const catRankMatch = /^(\d+)_(\d+)$/.exec(supplierIdOrName);
  if (catRankMatch) {
    const catId = catRankMatch[1];
    const rank = Number(catRankMatch[2]);
    ranking =
      rankings.find(
        (row) => row.category_id === catId && row.rank === rank
      ) ?? null;
  } else {
    ranking =
      rankings.find(
        (row) =>
          rankingKey(row).toLowerCase() === normalized ||
          row.supplier_name.toLowerCase() === normalized
      ) ?? null;
  }
  const matchedProducts = products.filter((product) => {
    const supplierMatch =
      normalizeText(product.supplier_name).toLowerCase() === normalized;
    const idMatch =
      normalizeText(product.supplier_id).toLowerCase() === normalized;
    return supplierMatch || idMatch;
  });

  return {
    id: rankingKey(
      ranking ?? {
        rank: 0,
        consecutive_years: null,
        supplier_name: supplierIdOrName,
        years_in_operation: null,
        repurchase_rate: null,
        response_rate: null,
        monthly_sales: null,
        top_products: [],
        review_snippet: null,
        source_url: '',
        page_title: null,
        scraped_at: '',
      }
    ),
    name:
      ranking?.supplier_name ??
      matchedProducts[0]?.supplier_name ??
      supplierIdOrName,
    region: ranking?.region ?? matchedProducts[0]?.region ?? null,
    category_labels: uniqueStrings([
      ranking?.category_label,
      ...matchedProducts.map((product) => product.category_label),
      ...matchedProducts.map((product) => product.category_name),
    ]),
    category_ids: uniqueStrings([
      ranking?.category_id,
      ...matchedProducts.map((product) => product.category_ids),
    ]),
    ranking,
    products: dedupeBy(matchedProducts, productKey),
    source_urls: uniqueStrings([
      ranking?.source_url,
      ...matchedProducts.map((product) => product.supplier_url),
    ]),
    supplier_url:
      ranking?.source_url ?? matchedProducts[0]?.supplier_url ?? null,
  };
}

export async function getSupplierProfiles(): Promise<SupplierProfile[]> {
  const rankings = await getRankings();
  const products = await getBestsellers();
  const supplierKeys = uniqueStrings([
    ...rankings.map((row) => rankingKey(row)),
    ...products.map(
      (product) => product.supplier_id ?? product.supplier_name
    ),
  ]);

  return Promise.all(supplierKeys.map((key) => getSupplierProfile(key)));
}

export async function getProductProfile(
  productIdOrTitle: string
): Promise<ListingProduct | null> {
  const normalized = normalizeText(productIdOrTitle).toLowerCase();

  // 1. Search bestsellers (listing_products)
  const bestsellers = await getBestsellers();
  const bestMatch = bestsellers.find((product) => {
    const keys = [
      product.offer_id,
      product.product_id,
      product.title,
      product.keyword,
      product.source_url,
    ].filter((value): value is string => Boolean(value));
    return keys.some((value) => value.toLowerCase() === normalized);
  });
  if (bestMatch) return bestMatch;

  // 2. Search ranked suppliers' top_products (from all ranking runs)
  const stores = await getRankings(); // latest run by default
  for (const store of stores) {
    const rankedMatch = store.top_products.find((p: any) => {
      const keys = [p.source_url, p.title, p.category_label].filter(
        (v): v is string => Boolean(v)
      );
      return keys.some((v) => normalizeText(v).toLowerCase() === normalized);
    });
    if (rankedMatch) {
      // Map StoreProduct → ListingProduct
      const p = rankedMatch as any;
      const priceNum =
        typeof p.price === 'string'
          ? parseFloat(p.price.replace(/[^0-9.]/g, ''))
          : null;
      return {
        row_id: 0,
        offer_id: null,
        product_id: null,
        title: p.title ?? null,
        title_pt: p.title_pt ?? null,
        price_min: Number.isFinite(priceNum) ? priceNum : null,
        price_raw: p.price ?? null,
        moq_raw: null,
        image_url: p.image_url ?? null,
        supplier_name: store.supplier_name,
        supplier_name_pt: store.supplier_name_pt,
        supplier_url: store.source_url,
        supplier_id: store.supplier_id ?? store.member_id ?? null,
        region: store.region ?? null,
        category_label: p.category_label ?? store.category_label ?? null,
        category_label_pt: (p as any).category_label_pt ?? store.category_label_pt ?? null,
        category_name: null,
        product_url: p.source_url ?? null,
        sales_volume: p.sales ?? null,
        repurchase_rate: store.repurchase_rate,
        rating: null,
        category: p.category_label ?? store.category_label ?? null,
        main_specification: null,
        models: null,
        specifications: null,
        model_options: null,
        variant_prices: null,
        moq: null,
        source_url: p.source_url ?? null,
        ranking_badge: store.ranking_type ?? null,
        category_ids: p.category_id ?? null,
        keyword: null,
        page: 0,
        sort: '',
        scraped_at: p.source_url ? new Date().toISOString() : store.scraped_at,
      } as ListingProduct;
    }
  }

  // 3. Search factory_products
  const factoryProducts = await getFactoryProducts();
  const factoryMatch = factoryProducts.find((p: any) => {
    const keys = [p.offer_id, p.title, p.supplier_name].filter(
      (v): v is string => Boolean(v)
    );
    return keys.some((v) => normalizeText(v).toLowerCase() === normalized);
  });
  if (factoryMatch) {
    const p = factoryMatch as any;
    const priceNum =
      p.price != null ? parseFloat(String(p.price).replace(/[^0-9.]/g, '')) : null;
    return {
      row_id: 0,
      offer_id: p.offer_id ?? null,
      product_id: p.offer_id ?? null,
      title: p.title ?? null,
      title_pt: null,
      price_min: Number.isFinite(priceNum) ? priceNum : null,
      price_raw: p.price != null ? String(p.price) : null,
      moq_raw: null,
        image_url: p.imageUrl ?? null,
        all_images: p.all_images ?? [],
        video_url: p.video_url ?? null,
      supplier_name: p.supplier_name ?? 'Unknown',
      supplier_name_pt: null,
      supplier_url: p.supplier_url ?? null,
      supplier_id: null,
      region: p.region ?? p.province ?? null,
      city: p.city ?? null,
      certifications: p.certifications ?? null,
      ranking_badges: p.ranking_badges ?? null,
      category_label: p.product_category ?? p.category ?? null,
      category_label_pt: p.product_category_pt ?? null,
      category_name: null,
      product_url:
        p.offer_id && p.offer_id.startsWith('http') === false
          ? `https://detail.1688.com/offer/${p.offer_id}.html`
          : p.supplier_url,
      sales_volume: p.sales ?? null,
      repurchase_rate: null,
      rating: null,
      category: p.product_category ?? p.category ?? null,
      main_specification: null,
      models: null,
      specifications: null,
      model_options: null,
      variant_prices: null,
      moq: null,
      source_url: p.supplier_url ?? null,
      ranking_badge: null,
      category_ids: null,
      keyword: null,
      page: 0,
      sort: '',
      scraped_at: new Date().toISOString(),
    } as ListingProduct;
  }

  return null;
}

// ─── Types for factory data ───

export interface FactoryRow {
  name: string;
  province: string | null;
  employees: number | null;
  area: number | null;
  certifications: string[];
  ranking_badges: string[];
  supplier_category: string | null;
  rank_type: string | null;
  responseRate: number | null;
  repurchaseRate: number | null;
  onTimeRate: number | null;
  supplier_url: string | null;
}

export interface FactoryProductRow {
  title: string | null;
  price: number | null;
  imageUrl: string | null;
  all_images: string[];
  supplier_name: string;
  supplier_url: string | null;
  product_category: string | null;
  supplier_category: string | null;
  category: string | null;
  product_category_pt: string | null;
  offer_id: string | null;
  sales: string | null;
  city?: string | null;
  certifications?: string[] | null;
  ranking_badges?: string[] | null;
  region?: string | null;
  main_spec?: string | null;
  specifications?: string[] | null;
  models?: string[] | null;
  variant_prices?: string[] | null;
  video_url?: string | null;
}

export async function getFactories(): Promise<FactoryRow[]> {
  const rows = await query(`
    SELECT
      supplier_name,
      MAX(supplier_url) as supplier_url,
      MAX(factory_area) as factory_area,
      MAX(factory_employees) as factory_employees,
      MAX(certifications) as certifications,
      MAX(ranking_badges) as ranking_badges,
      MAX(COALESCE(supplier_category, category)) as supplier_category,
      MAX(rank_type) as rank_type
    FROM factory_products
    GROUP BY supplier_name
    HAVING supplier_name IS NOT NULL AND supplier_name != ''
  `);

  const result: FactoryRow[] = [];

  for (const row of rows) {
    const name = row.supplier_name ?? 'Unknown';

    let certs: string[] = [];
    try {
      const parsed = JSON.parse(row.certifications ?? '[]');
      if (Array.isArray(parsed))
        certs = parsed.filter((c: unknown) => typeof c === 'string');
    } catch {
      /* ignore */
    }

    let badges: string[] = [];
    try {
      const parsed = JSON.parse(row.ranking_badges ?? '[]');
      if (Array.isArray(parsed)) {
        badges = parsed
          .filter((b: unknown) => typeof b === 'string')
          .map(cleanBadge)
          .filter((b: string) => b.length > 0);
      }
    } catch {
      /* ignore */
    }

    const rankTypeCn = badges.find((b) => BADGE_TO_RANK_TYPE[b]);
    const rankType = rankTypeCn
      ? BADGE_TO_RANK_TYPE[rankTypeCn]
      : (row.rank_type ?? null);

    result.push({
      name,
      province: extractProvince(name),
      employees: row.factory_employees ?? null,
      area: row.factory_area ?? null,
      certifications: certs,
      ranking_badges: badges,
      supplier_category: row.supplier_category ?? null,
      rank_type: rankType,
      responseRate: null,
      repurchaseRate: null,
      onTimeRate: null,
      supplier_url: row.supplier_url ?? null,
    });
  }

  return result;
}

export async function getFactoryProducts(): Promise<FactoryProductRow[]> {
  const rows = await query(`\n    SELECT\n      p.title, p.price, p.images, p.supplier_name, p.offer_id, p.sales_count,\n      p.region, p.city, p.certifications, p.ranking_badges,\n      p.main_spec, p.specifications, p.models, p.variant_prices, p.video_url,\n      COALESCE(p.supplier_url, s.supplier_url) as supplier_url,\n      p.product_category, p.product_category_pt, p.supplier_category, p.category\n    FROM factory_products p\n    LEFT JOIN factory_products s\n      ON s.supplier_name = p.supplier_name\n      AND (s.offer_id IS NULL OR s.offer_id = '')\n    WHERE p.offer_id IS NOT NULL AND p.offer_id != ''\n  `);

  return rows.map((row) => {
    let imageUrl: string | null = null;
    let allImages: string[] = [];
    try {
      const parsed = JSON.parse(row.images ?? '[]');
      if (Array.isArray(parsed)) {
        allImages = parsed.filter((img): img is string => typeof img === 'string');
        if (allImages.length > 0) imageUrl = allImages[0];
      }
    } catch {
      /* ignore */
    }

    let salesStr: string | null = null;
    if (row.sales_count != null) {
      const n = Number(row.sales_count);
      if (n >= 10000) {
        salesStr = `热销${(n / 10000).toFixed(1)}万+`;
      } else {
        salesStr = `热销${n}+`;
      }
    }

    // Parse certifications JSON array
    let certs: string[] = [];
    try {
      const parsed = JSON.parse(row.certifications ?? '[]');
      if (Array.isArray(parsed)) {
        certs = parsed.filter((c: unknown) => typeof c === 'string');
      }
    } catch {
      /* ignore */
    }

    // Parse ranking_badges and clean
    let badges: string[] = [];
    try {
      const parsed = JSON.parse(row.ranking_badges ?? '[]');
      if (Array.isArray(parsed)) {
        badges = parsed
          .filter((b: unknown) => typeof b === 'string')
          .map(cleanBadge)
          .filter((b: string) => b.length > 0);
      }
    } catch {
      /* ignore */
    }

    return {
      title: row.title ?? null,
      price: Number.isFinite(Number(row.price)) ? Number(row.price) : null,
      imageUrl,
      all_images: allImages,
      supplier_name: row.supplier_name ?? 'Unknown',
      supplier_url: row.supplier_url ?? null,
      product_category: row.product_category ?? null,
      supplier_category: row.supplier_category ?? null,
      category: row.product_category ?? row.category ?? null,
      product_category_pt: row.product_category_pt ?? null,
      offer_id: row.offer_id ?? null,
      sales: salesStr,
      city: row.city ?? null,
      certifications: certs,
      ranking_badges: badges,
      region: row.region ?? null,
      main_spec: row.main_spec ?? null,
      specifications: row.specifications ? (() => { try { return JSON.parse(row.specifications); } catch { return null; } })() : null,
      models: row.models ? (() => { try { return JSON.parse(row.models); } catch { return null; } })() : null,
      variant_prices: row.variant_prices ? (() => { try { return JSON.parse(row.variant_prices); } catch { return null; } })() : null,
      video_url: row.video_url ?? null,
    };
  });
}

export interface ProductRow {
  product_id: string | null;
  title: string | null;
  title_pt: string | null;
  image_url: string | null;
  price: number | null;
  sales: string | null;
  category_label: string | null;
  category_label_pt: string | null;
  category_id: string | null;
  source_url: string | null;
  supplier_name: string;
  supplier_name_pt: string | null;
  supplier_href: string;
  region: string | null;
  years_in_operation: number | null;
  repurchase_rate: number | null;
  ranking_type: string | null;
  rank: number;
}

// ─── Category-scoped product queries ───

/** Digital accessory categories (CN labels) used for the /category/digital-accessories route */
export const DIGITAL_ACCESSORY_CATEGORIES = [
  '蓝牙耳机',
  '手机数据线',
  '手机保护套',
  'USB风扇',
  '钥匙扣配件',
] as const;

/** Unified row type for category pages — standalone (not extending ProductRow) to allow nullable fields */
export interface CategoryProductRow {
  product_id: string | null;
  title: string | null;
  title_pt: string | null;
  image_url: string | null;
  price: number | null;
  sales: string | null;
  category_label: string | null;
  category_label_pt: string | null;
  category_id: string | null;
  source_url: string | null;
  supplier_name: string;
  supplier_name_pt: string | null;
  supplier_href: string | null;
  region: string | null;
  years_in_operation: number | null;
  repurchase_rate: number | null;
  ranking_type: string | null;
  rank: number | null;
  source: 'ranked' | 'bestseller' | 'factory';
  certifications?: string[] | null;
}

/**
 * Returns products filtered by one or more category labels.
 * Sources from ranked + bestseller + factory, deduped, sorted by sales desc.
 */
export async function getCategoryProducts(
  categoryLabels: string[]
): Promise<CategoryProductRow[]> {
  if (categoryLabels.length === 0) return [];

  const [ranked, bestseller, factory] = await Promise.all([
    getProductRows(),
    getBestsellers(),
    getFactoryProducts(),
  ]);

  const labelSet = new Set(categoryLabels.map(l => l.toLowerCase()));
  const matches = (c: string | null) => c && labelSet.has(c.toLowerCase());

  const rows: CategoryProductRow[] = [];
  const seen = new Set<string>();

  for (const r of ranked) {
    if (!matches(r.category_label)) continue;
    const key = `${r.supplier_name}-${r.title}-${r.price}`;
    if (seen.has(key)) continue;
    seen.add(key);
    rows.push({
      product_id: r.product_id ?? null,
      title: r.title ?? null,
      title_pt: r.title_pt ?? null,
      image_url: r.image_url ?? null,
      price: (r.price != null && !Number.isNaN(r.price)) ? r.price : null,
      sales: r.sales ?? null,
      category_label: r.category_label ?? null,
      category_label_pt: r.category_label_pt ?? null,
      category_id: r.category_id ?? null,
      source_url: r.source_url ?? null,
      supplier_name: r.supplier_name,
      supplier_name_pt: r.supplier_name_pt ?? null,
      supplier_href: r.supplier_href ?? null,
      region: r.region ?? null,
      years_in_operation: r.years_in_operation ?? null,
      repurchase_rate: r.repurchase_rate ?? null,
      ranking_type: r.ranking_type ?? null,
      rank: r.rank ?? null,
      source: 'ranked',
    });
  }

  for (const b of bestseller) {
    const cat = (b.category_label ?? b.category_name) ?? null;
    if (!matches(cat)) continue;
    const key = `${b.supplier_name}-${b.title}-${b.price_min}`;
    if (seen.has(key)) continue;
    seen.add(key);
    rows.push({
      product_id: b.offer_id ?? b.product_id ?? null,
      title: b.title ?? null,
      title_pt: b.title_pt ?? null,
      image_url: b.image_url ?? null,
      price: b.price_min != null ? Number(b.price_min) : null,
      sales: b.sales_volume ?? null,
      category_label: cat ?? null,
      category_label_pt: b.category_label_pt ?? null,
      category_id: b.category_ids ?? null,
      source_url: b.source_url ?? b.supplier_url ?? null,
      supplier_name: b.supplier_name ?? 'Unknown',
      supplier_name_pt: b.supplier_name_pt ?? null,
      supplier_href: b.supplier_url
        ? `/suppliers/${encodeURIComponent(b.supplier_url)}`
        : null,
      region: b.region ?? null,
      years_in_operation: null,
      repurchase_rate: b.repurchase_rate ?? null,
      ranking_type: null,
      rank: null,
      source: 'bestseller',
    });
  }

  for (const f of factory) {
    if (!matches(f.product_category)) continue;
    const key = `${f.supplier_name}-${f.title}-${f.price}`;
    if (seen.has(key)) continue;
    seen.add(key);
    rows.push({
      product_id: f.offer_id ?? null,
      title: f.title ?? null,
      title_pt: null,
      image_url: f.imageUrl ?? null,
      price: (f.price != null && !Number.isNaN(f.price)) ? f.price : null,
      sales: f.sales ?? null,
      category_label: f.product_category ?? null,
      category_label_pt: f.product_category_pt ?? null,
      category_id: null,
      source_url: f.supplier_url ?? null,
      supplier_name: f.supplier_name ?? 'Unknown',
      supplier_name_pt: null,
      supplier_href: f.supplier_url
        ? `/suppliers/${encodeURIComponent(f.supplier_url)}`
        : null,
      region: f.region ?? null,
      years_in_operation: null,
      repurchase_rate: null,
      ranking_type: null,
      rank: null,
      source: 'factory',
      certifications: f.certifications ?? null,
    });
  }

  // Sort by sales (desc), then by price
  rows.sort((a, b) => {
    const salesA = parseSalesNumber(a.sales);
    const salesB = parseSalesNumber(b.sales);
    if (salesB !== salesA) return salesB - salesA;
    return (b.price ?? 0) - (a.price ?? 0);
  });

  return rows;
}

function parseSalesNumber(s: string | null): number {
  if (!s) return 0;
  const m = s.match(/([\d.]+)\s*万/);
  if (m) return parseFloat(m[1]) * 10000;
  const n = s.replace(/[^0-9]/g, '');
  return n ? parseInt(n, 10) : 0;
}

export async function getProductRows(
  runId?: string | null
): Promise<ProductRow[]> {
  const stores = await getRankings(runId);
  const rows: ProductRow[] = [];
  const seen = new Set<string>();

  for (const store of stores) {
    const supplierHref =
      store.category_id && store.rank != null
        ? `${store.category_id}_${store.rank}`
        : encodeURIComponent(
            (store.supplier_id ?? store.member_id ?? store.supplier_name).replace(
              /\//g,
              '-'
            )
          );

    for (const p of store.top_products) {
      const key = `${p.source_url ?? p.image_url ?? store.supplier_name}-${p.price}`;
      if (seen.has(key)) continue;
      seen.add(key);
      const priceNum =
        typeof p.price === 'string'
          ? parseFloat(p.price.replace(/[^\d.]/g, ''))
          : null;
      rows.push({
        product_id: null,
        title: p.title ?? null,
        title_pt: p.title_pt ?? null,
        image_url: p.image_url ?? null,
        price: Number.isFinite(priceNum) ? priceNum : null,
        sales: formatSalesValue(p.sales ?? null),
        category_label: p.category_label ?? store.category_label ?? null,
        category_label_pt: (p as any).category_label_pt ?? store.category_label_pt ?? null,
        category_id: p.category_id ?? store.category_id ?? null,
        source_url: p.source_url ?? null,
        supplier_name: store.supplier_name,
        supplier_name_pt: null,
        supplier_href: `/suppliers/${supplierHref}`,
        region: store.region ?? null,
        years_in_operation: store.years_in_operation ?? null,
        repurchase_rate: store.repurchase_rate ?? null,
        ranking_type: store.ranking_type ?? null,
        rank: store.rank,
      });
    }
  }
  return rows;
}

/**
 * Returns ML bestseller info for a set of product titles.
 * Used to enrich dashboard product listings with ML bestseller badges.
 */
export async function getMlBestsellerMatches(
  titles: string[]
): Promise<Map<string, { position: number; total_sales: number | null; sales_velocity: number | null; category_name: string | null }>> {
  if (titles.length === 0) return new Map();

  const rows = await query(
    `SELECT title, position, total_sales, sales_velocity, category_name
     FROM ml_bestsellers
     WHERE LOWER(title) = ANY($1::text[])
     ORDER BY position ASC NULLS LAST`,
    [titles.map(t => t.toLowerCase().trim())]
  );

  const matches = new Map<string, { position: number; total_sales: number | null; sales_velocity: number | null; category_name: string | null }>();
  for (const row of rows as any[]) {
    if (row.title) {
      matches.set(row.title.toLowerCase().trim(), {
        position: row.position,
        total_sales: row.total_sales,
        sales_velocity: row.sales_velocity,
        category_name: row.category_name,
      });
    }
  }
  return matches;
}

/**
 * Returns ML bestsellers that do NOT have a matching 1688 product (no China supply).
 * Joins ml_bestsellers against listing_products and factory_products by title similarity.
 * Sorted by sales_velocity descending — highest demand first.
 */
export async function getMlUnmatchedBestsellers(): Promise<Array<{
  ml_item_id: string;
  title: string;
  price_brl: number | null;
  total_sales: number | null;
  sales_velocity: number | null;
  category_name: string | null;
  category_code: string | null;
  seller_name: string | null;
  free_shipping: boolean | null;
  position: number | null;
}>> {
  return query(`
    SELECT mb.ml_item_id, mb.title, mb.price_brl, mb.total_sales,
           mb.sales_velocity, mb.category_name, mb.category_code,
           mb.seller_name, mb.free_shipping, mb.position
    FROM ml_bestsellers mb
    WHERE NOT EXISTS (
      SELECT 1 FROM listing_products lp
      WHERE lp.title ILIKE '%' || LEFT(mb.title, 20) || '%'
         OR mb.title ILIKE '%' || LEFT(lp.title, 20) || '%'
    )
    AND NOT EXISTS (
      SELECT 1 FROM factory_products fp
      WHERE fp.title ILIKE '%' || LEFT(mb.title, 20) || '%'
         OR mb.title ILIKE '%' || LEFT(fp.title, 20) || '%'
    )
    AND mb.sales_velocity IS NOT NULL
    ORDER BY mb.sales_velocity DESC
    LIMIT 50
  `) as Promise<any[]>;
}

/**
 * Returns ML demand summary by category from silver_products.
 * Uses ml_category + ml_sales_volume to show which ML categories have highest demand
 * across our 1688 product catalog. Useful as a demand signal even before ml_bestsellers is populated.
 */
export async function getMlDemandByCategory(): Promise<Array<{
  ml_category: string;
  product_count: number;
  total_ml_sales: number;
  avg_ml_sales: number;
  avg_price_cny: number | null;
}>> {
  return query(`
    SELECT
      ml_category,
      COUNT(*) AS product_count,
      SUM(ml_sales_volume) AS total_ml_sales,
      ROUND(AVG(ml_sales_volume)) AS avg_ml_sales,
      ROUND(AVG(price_cny), 2) AS avg_price_cny
    FROM silver_products
    WHERE ml_category IS NOT NULL
      AND ml_sales_volume IS NOT NULL
      AND ml_sales_volume > 0
    GROUP BY ml_category
    ORDER BY total_ml_sales DESC
    LIMIT 15
  `) as Promise<any[]>;
}

// ─── China Bestsellers Not Yet in Brazil ───

export interface ChinaBestsellerOpportunity {
  row_id: string;
  offer_id: string | null;
  title: string | null;
  title_pt: string | null;
  price_min: number | null;
  sales_volume_estimate: number | null;
  supplier_name: string | null;
  image_url: string | null;
  category_label_pt: string | null;
  repurchase_rate: number | null;
  opportunity_score: number;  // computed: sales_volume / price (higher = better)
}

/**
 * Returns Chinese bestseller products from listing_products that have NOT been
 * matched to Mercado Livre (Brazil) — identified by silver_products.ml_sales_volume IS NULL.
 * Sorted by opportunity_score descending (sales_volume / price_cny).
 *
 * These represent products that sell well on 1688.com but don't yet have
 * a corresponding ML listing — import opportunities for Brazil market.
 */
export async function getChinaBestsellersNotInBrazil(
  limit = 50
): Promise<ChinaBestsellerOpportunity[]> {
  const rows = await query(`
    SELECT
      lp.row_id,
      lp.offer_id,
      lp.title,
      lp.title_pt,
      lp.price_min,
      lp.sales_volume_estimate,
      lp.supplier_name,
      lp.image_url,
      lp.category_label_pt,
      lp.repurchase_rate
    FROM listing_products lp
    LEFT JOIN silver_products sp ON sp.title = lp.title AND sp.bronze_source = 'listing'
    WHERE sp.ml_sales_volume IS NULL OR sp.id IS NULL
    ORDER BY
      COALESCE(lp.sales_volume_estimate, 0) DESC,
      lp.price_min ASC NULLS LAST
    LIMIT $1
  `, [limit]);

  return rows.map((row: any) => {
    const sales = row.sales_volume_estimate ?? 0;
    const price = row.price_min ?? 0;
    // Opportunity score: sales volume per CNY of price (higher = better opportunity)
    // If price is 0, fall back to raw sales volume
    const opportunity_score = price > 0
      ? Math.round((sales / price) * 10) / 10
      : sales;

    return {
      row_id: String(row.row_id),
      offer_id: row.offer_id,
      title: row.title,
      title_pt: row.title_pt,
      price_min: row.price_min != null ? Number(row.price_min) : null,
      sales_volume_estimate: row.sales_volume_estimate ?? null,
      supplier_name: row.supplier_name,
      image_url: row.image_url,
      category_label_pt: row.category_label_pt,
      repurchase_rate: row.repurchase_rate,
      opportunity_score,
    };
  });
}

/**
 * Summary stats for China bestsellers not yet in Brazil.
 */
export async function getChinaBestsellerOpportunityStats(): Promise<{
  total_products: number;
  avg_price: number | null;
  avg_sales: number | null;
  top_category: string | null;
  top_category_count: number;
}> {
  const stats = await queryOne(`
    SELECT
      COUNT(*) as total_products,
      ROUND(AVG(lp.price_min), 2) as avg_price,
      ROUND(AVG(lp.sales_volume_estimate), 0) as avg_sales
    FROM listing_products lp
    LEFT JOIN silver_products sp ON sp.title = lp.title AND sp.bronze_source = 'listing'
    WHERE sp.ml_sales_volume IS NULL OR sp.id IS NULL
  `);

  const topCat = await queryOne(`
    SELECT lp.category_label_pt as top_category, COUNT(*) as top_category_count
    FROM listing_products lp
    LEFT JOIN silver_products sp ON sp.title = lp.title AND sp.bronze_source = 'listing'
    WHERE (sp.ml_sales_volume IS NULL OR sp.id IS NULL)
      AND lp.category_label_pt IS NOT NULL AND TRIM(lp.category_label_pt) != ''
    GROUP BY lp.category_label_pt
    ORDER BY COUNT(*) DESC
    LIMIT 1
  `);

  return {
    total_products: Number(stats?.total_products ?? 0),
    avg_price: stats?.avg_price != null ? Number(stats.avg_price) : null,
    avg_sales: stats?.avg_sales != null ? Number(stats.avg_sales) : null,
    top_category: topCat?.top_category ?? null,
    top_category_count: Number(topCat?.top_category_count ?? 0),
  };
}


// ─── Velocity / Time-Dimension ─────────────────────────────────────────────

export interface ProductVelocityInfo {
  offer_id: string;
  current_sales: number | null;
  previous_sales: number | null;
  sales_delta: number | null;
  days_between: number | null;
  daily_velocity: number | null;
  latest_scrape: string | null;
  previous_scrape: string | null;
}

/**
 * Bulk velocity lookup — returns velocity data for products with ≥2 snapshots.
 * Queries the product_velocity view (defined in migration 005).
 */
export async function getBulkProductVelocity(
  offerIds: string[]
): Promise<Map<string, ProductVelocityInfo>> {
  if (offerIds.length === 0) return new Map();

  const rows = await query<{
    offer_id: string;
    current_sales: number | null;
    previous_sales: number | null;
    sales_delta: number | null;
    days_between: number | null;
    daily_velocity: number | null;
    latest_scrape: string | null;
    previous_scrape: string | null;
  }>(`
    SELECT
      v.offer_id,
      v.current_sales,
      v.previous_sales,
      v.sales_delta,
      v.days_between,
      v.daily_velocity,
      v.latest_scrape::text,
      v.previous_scrape::text
    FROM product_velocity v
    WHERE v.offer_id = ANY($1::text[])
  `, [offerIds]);

  const map = new Map<string, ProductVelocityInfo>();
  for (const row of rows) {
    map.set(row.offer_id, {
      offer_id: row.offer_id,
      current_sales: row.current_sales != null ? Number(row.current_sales) : null,
      previous_sales: row.previous_sales != null ? Number(row.previous_sales) : null,
      sales_delta: row.sales_delta != null ? Number(row.sales_delta) : null,
      days_between: row.days_between != null ? Number(row.days_between) : null,
      daily_velocity: row.daily_velocity != null ? Number(row.daily_velocity) : null,
      latest_scrape: row.latest_scrape,
      previous_scrape: row.previous_scrape,
    });
  }
  return map;
}

/**
 * Global velocity summary — snapshot and velocity stats for KPI cards.
 */
export async function getVelocitySummary(): Promise<{
  has_velocity_data: boolean;
  total_snapshots: number;
  unique_products_with_velocity: number;
  unique_snapshot_dates: number;
  products_trending_up: number;
  products_trending_down: number;
  total_sales_delta: number | null;
  latest_scrape_date: string | null;
  avg_daily_velocity: number | null;
  snapshot_dates: Array<{ date: string; product_count: number }>;
}> {
  const stats = await queryOne<{
    total_snapshots: number;
    latest_scrape: string | null;
  }>(`
    SELECT COUNT(*) as total_snapshots, MAX(scraped_at)::text as latest_scrape
    FROM product_snapshots
  `);

  const vel = await queryOne<{
    count: number;
    count_positive: number;
    count_negative: number;
    avg_velocity: number | null;
    total_sales_delta: number | null;
  }>(`
    SELECT
      COUNT(*) as count,
      COUNT(*) FILTER (WHERE daily_velocity > 0) as count_positive,
      COUNT(*) FILTER (WHERE daily_velocity < 0) as count_negative,
      ROUND(AVG(daily_velocity), 1) as avg_velocity,
      SUM(sales_delta) as total_sales_delta
    FROM product_velocity
    WHERE daily_velocity IS NOT NULL
  `);

  const snapDates = await query<{
    snap_date: string;
    product_count: number;
  }>(`
    SELECT scraped_at::date::text as snap_date, COUNT(DISTINCT offer_id) as product_count
    FROM product_snapshots
    GROUP BY scraped_at::date
    ORDER BY snap_date
  `);

  return {
    has_velocity_data: (vel?.count ?? 0) > 0,
    total_snapshots: Number(stats?.total_snapshots ?? 0),
    unique_products_with_velocity: Number(vel?.count ?? 0),
    unique_snapshot_dates: snapDates.length,
    products_trending_up: Number(vel?.count_positive ?? 0),
    products_trending_down: Number(vel?.count_negative ?? 0),
    total_sales_delta: vel?.total_sales_delta != null ? Number(vel.total_sales_delta) : null,
    latest_scrape_date: stats?.latest_scrape ?? null,
    avg_daily_velocity: vel?.avg_velocity != null ? Number(vel.avg_velocity) : null,
    snapshot_dates: snapDates.map(d => ({
      date: d.snap_date,
      product_count: Number(d.product_count),
    })),
  };
}

/**
 * Trending products — top N by absolute velocity.
 */
export async function getTrendingProducts(
  limit: number = 10,
  direction: 'up' | 'down' | 'any' = 'any'
): Promise<Array<{
  offer_id: string;
  title: string;
  category_label: string | null;
  current_sales: number | null;
  previous_sales: number | null;
  sales_delta: number | null;
  daily_velocity: number | null;
  weekly_velocity: number | null;
  days_between: number | null;
  price_min: number | null;
  repurchase_rate: number | null;
  supplier_name: string | null;
}>> {
  const dirFilter = direction === 'up'
    ? 'AND v.daily_velocity > 0'
    : direction === 'down'
      ? 'AND v.daily_velocity < 0'
      : '';

  return query(`
    SELECT
      v.offer_id,
      lp.title,
      lp.category_label,
      v.current_sales,
      v.previous_sales,
      v.sales_delta,
      v.daily_velocity,
      ROUND(v.daily_velocity * 7, 1) as weekly_velocity,
      v.days_between,
      lp.price_min,
      lp.repurchase_rate,
      lp.supplier_name
    FROM product_velocity v
    JOIN listing_products lp ON lp.offer_id = v.offer_id
    WHERE v.daily_velocity IS NOT NULL ${dirFilter}
    ORDER BY ABS(v.daily_velocity) DESC
    LIMIT $1
  `, [limit]);
}

/**
 * Time-dimension breakdown: velocity distribution and estimated weekly sales.
 */
export async function getVelocityTimeStats(): Promise<{
  products_with_velocity: number;
  products_gaining: number;
  products_stable: number;
  products_declining: number;
  avg_weekly_velocity: number | null;
  estimated_weekly_sales: number | null;
  snapshot_span_days: number | null;
  latest_snapshot_date: string | null;
  previous_snapshot_date: string | null;
}> {
  const stats = await queryOne<{
    total: number;
    gaining: number;
    stable: number;
    declining: number;
    avg_weekly: number | null;
    total_weekly: number | null;
  }>(`
    SELECT
      COUNT(*) as total,
      COUNT(*) FILTER (WHERE daily_velocity > 0) as gaining,
      COUNT(*) FILTER (WHERE daily_velocity = 0) as stable,
      COUNT(*) FILTER (WHERE daily_velocity < 0) as declining,
      ROUND(AVG(daily_velocity * 7), 0) as avg_weekly,
      SUM(daily_velocity * 7) as total_weekly
    FROM product_velocity
    WHERE daily_velocity IS NOT NULL
  `);

  const dates = await query<{ snap_date: string }>(`
    SELECT DISTINCT scraped_at::date::text as snap_date
    FROM product_snapshots
    ORDER BY snap_date DESC
    LIMIT 2
  `);

  const latestDate = dates[0]?.snap_date ?? null;
  const prevDate = dates[1]?.snap_date ?? null;

  let spanDays: number | null = null;
  if (latestDate && prevDate) {
    spanDays = Math.round(
      (new Date(latestDate).getTime() - new Date(prevDate).getTime()) / (1000 * 60 * 60 * 24)
    );
  }

  return {
    products_with_velocity: Number(stats?.total ?? 0),
    products_gaining: Number(stats?.gaining ?? 0),
    products_stable: Number(stats?.stable ?? 0),
    products_declining: Number(stats?.declining ?? 0),
    avg_weekly_velocity: stats?.avg_weekly != null ? Number(stats.avg_weekly) : null,
    estimated_weekly_sales: stats?.total_weekly != null ? Number(stats.total_weekly) : null,
    snapshot_span_days: spanDays,
    latest_snapshot_date: latestDate,
    previous_snapshot_date: prevDate,
  };
}
