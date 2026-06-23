import { NextResponse } from 'next/server';
import { getProductRows, getBestsellers, getFactoryProducts, extractProvince, getBulkProductVelocity, getVelocitySummary, getVelocityTimeStats } from '@/lib/data-pg';

type ProductRow = {
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
  // v1.5 enrichment fields (may be null)
  all_images?: string[] | null;
  city?: string | null;
  certifications?: string[] | null;
  ranking_badges?: string[] | null;
  main_specification?: string | null;
  models?: string[] | null;
  specifications?: string[] | null;
  variant_prices?: string[] | null;
  video_url?: string | null;
  enrichment_status?: 'complete' | 'partial' | 'none';
  // Velocity fields (T12: time dimension)
  velocity_daily?: number | null;
  velocity_weekly?: number | null;
  sales_delta?: number | null;
  velocity_days_between?: number | null;
  latest_scrape?: string | null;
};

export const dynamic = 'force-dynamic';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  
  // Pagination
  const page = Math.max(1, parseInt(searchParams.get('page') || '1', 10));
  const limit = Math.min(5000, Math.max(1, parseInt(searchParams.get('limit') || '2040', 10)));
  
  // Filters
  const search = searchParams.get('search')?.toLowerCase() || '';
  const categories = searchParams.get('categories')?.split(',').filter(Boolean) || [];
  const regions = searchParams.get('regions')?.split(',').filter(Boolean) || [];
  const priceMin = searchParams.get('priceMin') ? parseFloat(searchParams.get('priceMin')!) : null;
  const priceMax = searchParams.get('priceMax') ? parseFloat(searchParams.get('priceMax')!) : null;
  const sources = searchParams.get('sources')?.split(',').filter(Boolean) || [];
  const enrichmentFilter = searchParams.get('enrichment')?.split(',').filter(Boolean) || [];

  // Fetch raw data
  const [rankedRaw, bestsellerRaw, factoryRaw] = await Promise.all([
    getProductRows(),
    getBestsellers(),
    getFactoryProducts(),
  ]);

  // Unify
  const ranked: ProductRow[] = rankedRaw.map(r => ({
    ...r,
    source: 'ranked' as const,
  }));
  const bestseller: ProductRow[] = bestsellerRaw.map(p => ({
    product_id: p.offer_id ?? p.product_id ?? null,
    title: p.title ?? null,
    title_pt: p.title_pt ?? null,
    image_url: p.image_url ?? null,
    price: p.price_min ?? null,
    sales: p.sales_volume ?? null,
    category_label: p.category_label ?? p.category_name ?? null,
    category_label_pt: p.category_label_pt ?? null,
    category_id: p.category_ids ?? null,
    source_url: p.source_url ?? p.supplier_url ?? null,
    supplier_name: p.supplier_name ?? 'Unknown',
    supplier_name_pt: p.supplier_name_pt ?? null,
    supplier_href: p.supplier_url ? `/suppliers/${encodeURIComponent(p.supplier_url)}` : null,
    region: p.region ?? null,
    years_in_operation: null,
    repurchase_rate: p.repurchase_rate ?? null,
    ranking_type: p.ranking_badge ?? null,
    rank: null,
    source: 'bestseller' as const,
  }));
  const factory: ProductRow[] = factoryRaw.map(p => ({
    product_id: p.offer_id ?? null,
    title: p.title ?? null,
    title_pt: null,
    image_url: p.imageUrl ?? null,
    price: p.price != null ? parseFloat(String(p.price)) : null,
    sales: p.sales,
    category_label: p.product_category ?? p.supplier_category ?? p.category ?? null,
    category_label_pt: p.product_category_pt ?? null,
    category_id: null,
    source_url: p.offer_id ? `https://detail.1688.com/offer/${p.offer_id}.html` : null,
    supplier_name: p.supplier_name ?? 'Unknown',
    supplier_name_pt: null,
    supplier_href: p.supplier_url && p.supplier_url.startsWith('http')
      ? p.supplier_url
      : (p.supplier_url ? `/suppliers/${encodeURIComponent(p.supplier_url)}` : null),
    region: p.region ?? extractProvince(p.supplier_name),
    years_in_operation: null,
    repurchase_rate: null,
    ranking_type: null,
    rank: null,
    source: 'factory' as const,
    // v1.5 enrichment
    all_images: p.all_images ?? [],
    city: p.city ?? null,
    certifications: p.certifications ?? null,
    ranking_badges: p.ranking_badges ?? null,
    main_specification: p.main_spec ?? null,
    specifications: p.specifications ?? null,
    models: p.models ?? null,
    variant_prices: p.variant_prices ?? null,
    video_url: p.video_url ?? null,
  }));

  // Merge + dedup
  const seen = new Set<string>();
  const merged: ProductRow[] = [];
  for (const p of [...ranked, ...bestseller, ...factory]) {
    const key = `${p.title ?? ''}|${p.supplier_name}`;
    if (seen.has(key)) continue;
    seen.add(key);
    // Compute enrichment status for each product
    p.enrichment_status = computeEnrichmentStatus(p);
    merged.push(p);
  }

  // Apply filters (server-side)
  const filtered = merged.filter(p => {
    if (search && !(p.title?.toLowerCase().includes(search) || p.title_pt?.toLowerCase().includes(search) || p.supplier_name?.toLowerCase().includes(search) || p.supplier_name_pt?.toLowerCase().includes(search))) return false;
    if (categories.length) {
      const catLabel = p.category_label_pt || p.category_label || '';
      if (!categories.some(c => catLabel.toLowerCase().includes(c.toLowerCase()))) return false;
    }
    if (regions.length && p.region && !regions.some(r => p.region!.toLowerCase().includes(r.toLowerCase()))) return false;
    if (priceMin != null && (p.price == null || p.price < priceMin)) return false;
    if (priceMax != null && (p.price == null || p.price > priceMax)) return false;
    if (sources.length && !sources.includes(p.source)) return false;
    if (enrichmentFilter.length && !enrichmentFilter.includes(p.enrichment_status ?? 'none')) return false;
    return true;
  });

  // Compute stats on full filtered set (before pagination)
  const stats = computeStats(filtered);

  // Velocity data -- attach per-product velocity and summary stats
  const allProductIds = filtered
    .map(p => p.product_id)
    .filter((id): id is string => !!id);

  const [velocityMap, velocitySummary, velocityTime] = await Promise.all([
    getBulkProductVelocity(allProductIds),
    getVelocitySummary(),
    getVelocityTimeStats(),
  ]);

  // Attach velocity fields to each row
  const withVelocity = filtered.map(p => {
    const vel = p.product_id ? velocityMap.get(p.product_id) : undefined;
    return {
      ...p,
      velocity_daily: vel?.daily_velocity ?? null,
      velocity_weekly: vel?.daily_velocity != null ? Math.round(vel.daily_velocity * 7) : null,
      sales_delta: vel?.sales_delta ?? null,
      velocity_days_between: vel?.days_between ?? null,
      latest_scrape: vel?.latest_scrape ?? null,
    };
  });

  // Add velocity stats to the response stats
  const statsWithVelocity = {
    ...stats,
    velocity: velocitySummary ? {
      has_data: velocitySummary.has_velocity_data,
      products_with_velocity: velocitySummary.unique_products_with_velocity,
      total_snapshots: velocitySummary.total_snapshots,
      unique_snapshot_dates: velocitySummary.unique_snapshot_dates,
      products_trending_up: velocitySummary.products_trending_up,
      products_trending_down: velocitySummary.products_trending_down,
      latest_scrape: velocitySummary.latest_scrape_date,
      avg_daily_velocity: velocitySummary.avg_daily_velocity,
      snapshot_dates: velocitySummary.snapshot_dates,
    } : null,
    velocityTime: velocityTime ? {
      products_with_velocity: velocityTime.products_with_velocity,
      products_gaining: velocityTime.products_gaining,
      products_stable: velocityTime.products_stable,
      products_declining: velocityTime.products_declining,
      avg_weekly_velocity: velocityTime.avg_weekly_velocity,
      estimated_weekly_sales: velocityTime.estimated_weekly_sales,
      snapshot_span_days: velocityTime.snapshot_span_days,
      latest_snapshot_date: velocityTime.latest_snapshot_date,
      previous_snapshot_date: velocityTime.previous_snapshot_date,
    } : null,
  };

  // Paginate (use withVelocity so velocity fields are on each row)
  const total = withVelocity.length;
  const start = (page - 1) * limit;
  const pageData = withVelocity.slice(start, start + limit);

  return NextResponse.json({
    data: pageData,
    total,
    page,
    limit,
    hasMore: start + limit < total,
    stats: statsWithVelocity,
  });
}

function computeEnrichmentStatus(p: ProductRow): 'complete' | 'partial' | 'none' {
  const hasVideo = !!p.video_url;
  const hasSpecs = !!p.main_specification || (Array.isArray(p.specifications) && p.specifications.length > 0);
  const hasModels = Array.isArray(p.models) && p.models.length > 0;
  const hasVariantPrices = Array.isArray(p.variant_prices) && p.variant_prices.length > 0;

  // complete: has video AND (main_spec OR specs) AND models
  if (hasVideo && hasSpecs && hasModels) return 'complete';

  // partial: any enriched field present
  if (hasVideo || hasSpecs || hasModels || hasVariantPrices) return 'partial';

  return 'none';
}

function computeStats(rows: ProductRow[]) {
  const n = rows.length;

  // Prices - exclude null, zero, negative, and non-numeric values
  const prices = rows
    .map(r => Number(r.price))
    .filter((p): p is number => Number.isFinite(p) && p > 0);
  const avgPrice = prices.length ? prices.reduce((a, b) => a + b, 0) / prices.length : null;

  // Title PT
  const withPt = rows.filter(r => r.title_pt != null && r.title_pt.trim().length > 0).length;

  // Sales
  const parseSales = (s: string | null): number | null => {
    if (!s) return null;
    const n = parseFloat(s.replace(/[^0-9.]/g, ''));
    if (s.includes('\u4e07')) return n * 10000;
    if (s.includes('+')) return n;
    return isNaN(n) ? null : n;
  };
  const salesVals = rows.map(r => parseSales(r.sales)).filter((s): s is number => s != null && s > 0);
  const avgSales = salesVals.length ? salesVals.reduce((a, b) => a + b, 0) / salesVals.length : null;

  // Distinct categories
  const distinctCategories = new Set(rows.map(r => r.category_label).filter(Boolean)).size;

  // Source counts
  const sourceCounts: Record<string, number> = { all: n, ranked: 0, bestseller: 0, factory: 0 };
  for (const r of rows) {
    if (r.source === 'ranked') sourceCounts.ranked++;
    else if (r.source === 'bestseller') sourceCounts.bestseller++;
    else if (r.source === 'factory') sourceCounts.factory++;
  }

  // Categories top 8
  const catCounts: Record<string, number> = {};
  for (const r of rows) {
    if (r.category_label) catCounts[r.category_label] = (catCounts[r.category_label] || 0) + 1;
  }
  const topCategories = Object.entries(catCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([label, count]) => ({ label, count }));

  // Regions top 8
  const regionCounts: Record<string, number> = {};
  for (const r of rows) {
    if (r.region) regionCounts[r.region] = (regionCounts[r.region] || 0) + 1;
  }
  const topRegions = Object.entries(regionCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([region, count]) => ({ region, count }));

  // Price bands
  let priceBands: { label: string; count: number }[] = [];
  let priceQuartiles: { q1: number; median: number; q3: number; max: number } | null = null;
  if (prices.length > 0) {
    prices.sort((a, b) => a - b);
    const q1 = prices[Math.floor(prices.length * 0.25)];
    const median = prices[Math.floor(prices.length * 0.5)];
    const q3 = prices[Math.floor(prices.length * 0.75)];
    const maxVal = prices[prices.length - 1];
    priceQuartiles = { q1, median, q3, max: maxVal };
    const fmt = (p: number) =>
      p >= 1000 ? (p / 1000).toFixed(1) + 'k' : Math.round(p).toString();
    priceBands = [
      { label: `< \u00a5${fmt(q1)}`, count: prices.filter(p => p < q1).length },
      { label: `\u00a5${fmt(q1)} \u2013 \u00a5${fmt(median)}`, count: prices.filter(p => p >= q1 && p < median).length },
      { label: `\u00a5${fmt(median)} \u2013 \u00a5${fmt(q3)}`, count: prices.filter(p => p >= median && p < q3).length },
      { label: `\u00a5${fmt(q3)} \u2013 \u00a5${fmt(maxVal)}`, count: prices.filter(p => p >= q3 && p < maxVal).length },
      { label: `> \u00a5${fmt(maxVal)}`, count: prices.filter(p => p >= maxVal).length },
    ];
  }

  return {
    total: n,
    avgPrice,
    withPt,
    avgSales,
    distinctCategories,
    topCategories,
    topRegions,
    priceBands,
    priceQuartiles,
    sourceCounts,
    enrichmentCounts: {
      complete: rows.filter(r => r.enrichment_status === 'complete').length,
      partial: rows.filter(r => r.enrichment_status === 'partial').length,
      none: rows.filter(r => r.enrichment_status === 'none').length,
    },
  };
}
