/**
 * 1688 Factory Product Scraper — Spec & Video Backfill
 *
 * Usage:
 *   npx tsx src/lib/scraper/1688-factory.ts --audit           # show coverage stats  // Step B-F: Unified v1.5 extraction from JSON (skuModel + gallery)
  // Navigate into the nested dataJson payload
  const dataJson = data.Root?.fields?.dataJson || {};
  const skuModel = dataJson.skuModel || {};
  const skuProps = skuModel.skuProps || [];
  const skuInfoMap = skuModel.skuInfoMap || {};

  // main_spec: combine spec property definitions (skuProps)
  let mainSpec: string | null = null;
  if (skuProps.length) {
    mainSpec = skuProps.map((p: any) => `${p.prop}: ${p.value.map((v: any) => v.name).join(', ')}`).join('; ');
  } else if (Object.keys(skuInfoMap).length) {
    mainSpec = Object.keys(skuInfoMap)[0];
  }

  // specifications: full skuProps array as structured JSON
  let specifications: any[] | null = null;
  if (skuProps.length) {
    specifications = skuProps.map((p: any) => ({
      property: p.prop,
      values: p.value.map((v: any) => ({ name: v.name, imageUrl: v.imageUrl }))
    }));
  }

  // models: variant names (keys of skuInfoMap)
  const variantNames = Object.keys(skuInfoMap);
  const models = variantNames.length ? variantNames : null;

  // variant_prices: map variant specAttrs to price info
  const vp: Record<string, any> = {};
  for (const [specAttrs, info] of Object.entries(skuInfoMap)) {
    vp[specAttrs] = {
      price: (info as any).price,
      discountPrice: (info as any).discountPrice,
      skuId: (info as any).skuId,
      specId: (info as any).specId,
      canBookCount: (info as any).canBookCount,
    };
  }
  const variant_prices = Object.keys(vp).length ? vp : null;

  // video_url: gallery.fields.video.videoUrl
  let video_url: string | null = null;
  const vf = data.gallery?.fields?.video;
  if (vf?.videoUrl) video_url = vf.videoUrl;
 --backfill --top=500  # scrape missing specs
 *
 * This scraper uses headless Chromium via xvfb-run to extract:
 *   - main_spec
 *   - specifications (array)
 *   - models (variant options)
 *   - variant_prices (array)
 *   - video_url (optional)
 *
 * Rate limiting: 5s delay between page loads; max 10 concurrent workers
 * Idempotent: skips products where fields already populated
 */

import { Pool } from 'pg';
import { exec } from 'child_process';
import { promisify } from 'util';
const execAsync = promisify(exec);
import dotenv from 'dotenv';
dotenv.config();

// ─── Site Unblocker (forward proxy) ───────────────────────────────────────────
const SU_USER = process.env.SU_USER || process.env.DECODO_USER || 'U0000398789';
const SU_PASS = (process.env.SU_PASS || process.env.DECODO_PASS || process.env.DECODO_SITEUNBLOCKER_PASSWORD) as string;
if (!SU_PASS) throw new Error('Site Unblocker password missing (SU_PASS/DECODO_PASS/DECODO_SITEUNBLOCKER_PASSWORD)');
const SU_HOST = process.env.SU_HOST || 'unblock.decodo.com';
const SU_PORT = process.env.SU_PORT || '60000';

// Fetch raw HTML via Site Unblocker using curl (no rendering, no images)
async function fetchViaSU(url: string, maxRetries = 2): Promise<string> {
  const curlCmd = [
    'curl', '-s', '-k',
    '-x', `https://${SU_HOST}:${SU_PORT}`,
    '-U', `${SU_USER}:${SU_PASS}`,
    '-H', `X-SU-User: ${SU_USER}`,
    '-H', `X-SU-Password: ${SU_PASS}`,
    '-H', 'X-SU-Geo: China',
    '-H', 'X-SU-Locale: zh-cn',
    url
  ].join(' ');

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const { stdout, stderr } = await execAsync(curlCmd, { maxBuffer: 10 * 1024 * 1024, timeout: 30000 });
      
      // Detect Site Unblocker rate-limit JSON response
      if (stdout.includes('"status":"failed"') && stdout.includes('rate limit')) {
        const err = new Error('RATE_LIMIT: Site Unblocker quota exceeded');
        (err as any).rateLimited = true;
        throw err;
      }
      
      // Detect Squid error pages
      if (stdout.includes('ERROR:') || stdout.includes('Proxy Authentication Required') || stdout.includes('ERR_CACHE_ACCESS_DENIED')) {
        throw new Error('PROXY_ERROR: ' + (stdout.match(/<title>(.*?)<\/title>/)?.[1] || 'Unknown proxy error'));
      }
      
      return stdout;
    } catch (err: any) {
      if (attempt === maxRetries) throw err;
      console.log(`   ↻ Retry ${attempt}/${maxRetries} after fetch error: ${err.message?.split('\n')[0]}`);
      await new Promise(r => setTimeout(r, 3000));
    }
  }
  throw new Error('Unreachable');
}
// ─── Extract window.context JSON from raw HTML ─────────────────────────────────

function extractContextFromHtml(html: string): any {
  // Use a simple regex to find <script> blocks, then evaluate to extract window.context
  const scriptRegex = /<script[^>]*>([\s\S]*?)<\/script>/gi;
  let match: RegExpExecArray | null;
  while ((match = scriptRegex.exec(html)) !== null) {
    const scriptContent = match[1];
    if (!scriptContent.includes('window.context')) continue;
    try {
      // Execute script with a mock window object
      const fn = new Function('window', scriptContent);
      const win: any = {};
      fn(win);
      return win.context || null;
    } catch (e) {
      console.error('extractContextFromHtml: evaluation error', e);
      return null;
    }
  }
  return null;
}





  const DB_URL = process.env.DATABASE_URL!;

interface FactoryProductRow {
  id: number;
  offer_id: string;
  title: string;
  sales_count: number | null;
  main_spec?: string | null;
  specifications?: string | null;
  models?: string | null;
  variant_prices?: string | null;
  video_url?: string | null;
}

async function getDbPool() {
  return new Pool({ connectionString: DB_URL });
}

async function auditCoverage() {
  const pool = await getDbPool();
  const result = await pool.query(`
    SELECT
      COUNT(*) AS total,
      COUNT(main_spec) AS has_main,
      COUNT(specifications) AS has_specs,
      COUNT(models) AS has_models,
      COUNT(variant_prices) AS has_variants,
      COUNT(video_url) AS has_video
    FROM factory_products
  `);
  console.table(result.rows[0]);
  await pool.end();
}

async function getProductsNeedingSpecs(limit = 500, categories?: string[]) {
  const pool = await getDbPool();
  const baseQuery = `
    SELECT id, offer_id, title, sales_count, product_category
    FROM factory_products
    WHERE (main_spec IS NULL
       OR specifications IS NULL
       OR models IS NULL
       OR variant_prices IS NULL
       OR video_url IS NULL)
  `;
  const conditions: string[] = [];
  const values: any[] = [limit];
  
  if (categories && categories.length > 0) {
    const catPlaceholders = categories.map((_, i) => `$${i + 2}`).join(',');
    conditions.push(`product_category IN (${catPlaceholders})`);
    values.push(...categories);
  }
  
  const whereClause = conditions.length ? ' AND ' + conditions.join(' AND ') : '';
  const query = `${baseQuery}${whereClause} ORDER BY sales_count DESC NULLS LAST LIMIT $1`;
  
  const result = await pool.query(query, values);
  await pool.end();
  return result.rows as Pick<FactoryProductRow, 'id' | 'offer_id' | 'title' | 'sales_count'>[];
}

async function scrapeProduct(product: Pick<FactoryProductRow, 'id' | 'offer_id' | 'title'>): Promise<any> {
  const productUrl = `https://detail.1688.com/offer/${product.offer_id}.html`;
  console.log(`   → Fetching via Site Unblocker API (no rendering)`);

  let html: string;
  try {
    html = await fetchViaSU(productUrl);
  } catch (err: any) {
    if (err.rateLimited) throw err;
    console.log(`   ⚠️  Fetch failed: ${err.message}`);
    return { main_spec: null, specifications: null, models: null, variant_prices: null, video_url: null };
  }

  const ctx = extractContextFromHtml(html);
  if (!ctx) {
    console.log(`   ⚠️  No context JSON extracted from HTML (size: ${html.length} bytes)`);
    return { main_spec: null, specifications: null, models: null, variant_prices: null, video_url: null };
  }

  const data = ctx?.result?.data || {};
  const dataJson = data.Root?.fields?.dataJson || {};
  const skuModel = dataJson.skuModel || {};
  const skuProps = skuModel.skuProps || [];
  const skuInfoMap = skuModel.skuInfoMap || {};

  // main_spec: combine spec property definitions (skuProps)
  let mainSpec: string | null = null;
  if (skuProps.length) {
    mainSpec = skuProps.map((p: any) => `${p.prop}: ${p.value.map((v: any) => v.name).join(', ')}`).join('; ');
  } else if (Object.keys(skuInfoMap).length) {
    mainSpec = Object.keys(skuInfoMap)[0];
  }

  // specifications: full skuProps array as structured JSON
  let specifications: any[] | null = null;
  if (skuProps.length) {
    specifications = skuProps.map((p: any) => ({
      property: p.prop,
      values: p.value.map((v: any) => ({ name: v.name, imageUrl: v.imageUrl }))
    }));
  }

  // models: variant names (keys of skuInfoMap)
  const variantNames = Object.keys(skuInfoMap);
  const models = variantNames.length ? variantNames : null;

  // variant_prices: map variant specAttrs to price info
  const vp: Record<string, any> = {};
  for (const [specAttrs, info] of Object.entries(skuInfoMap)) {
    vp[specAttrs] = {
      price: (info as any).price,
      discountPrice: (info as any).discountPrice,
      skuId: (info as any).skuId,
      specId: (info as any).specId,
      canBookCount: (info as any).canBookCount,
    };
  }
  const variant_prices = Object.keys(vp).length ? vp : null;

  // video_url: from gallery.fields.video.videoUrl
  let video_url: string | null = null;
  const vf = data.gallery?.fields?.video;
  if (vf?.videoUrl) video_url = vf.videoUrl;

  return { main_spec: mainSpec, specifications, models, variant_prices, video_url };
}

async function backfillSpecs(topN = 500, categories?: string[]) {
  let currentBackoff = 300000; // adaptive backoff (ms), resets after success
  const products = await getProductsNeedingSpecs(topN, categories);
  if (products.length === 0) {
    console.log('✅ No products need spec backfill');
    return;
  }

  console.log(`🔍 Starting backfill for ${products.length} products`);

  const pool = await getDbPool();

  for (let i = 0; i < products.length; i++) {
    const p = products[i];
    console.log(`[${i + 1}/${products.length}] Scraping ${p.offer_id} (id=${p.id}) — ${p.title.substring(0, 40)}...`);

    try {
      const data = await scrapeProduct(p);

      const updates: string[] = [];
      const values: any[] = [];
      let idx = 1;

      if (data.main_spec) {
        updates.push(`main_spec = $${idx++}`);
        values.push(data.main_spec);
      }
      if (data.specifications) {
        updates.push(`specifications = $${idx++}`);
        values.push(JSON.stringify(data.specifications));
      }
      if (data.models) {
        updates.push(`models = $${idx++}`);
        values.push(JSON.stringify(data.models));
      }
      if (data.variant_prices) {
        updates.push(`variant_prices = $${idx++}`);
        values.push(JSON.stringify(data.variant_prices));
      }
      if (data.video_url) {
        updates.push(`video_url = $${idx++}`);
        values.push(data.video_url);
      }

      if (updates.length > 0) {
        values.push(p.id);
        await pool.query(`UPDATE factory_products SET ${updates.join(', ')} WHERE id = $${idx}`, values);
        console.log(`   ✅ Updated: ${Object.keys(data).filter(k => data[k]).join(', ')}`);
        // Reset backoff on any successful extraction
        currentBackoff = 300000;
      } else {
        console.log(`   ⚠️  No data extracted`);
      }
    } catch (err: any) {
      if (err.rateLimited) {
        console.log(`   ⏸️  Rate limit hit — pausing ${Math.round(currentBackoff/60000)} minutes...`);
        await new Promise(resolve => setTimeout(resolve, currentBackoff));
        // Exponential backoff: double for next consecutive failure
        currentBackoff = Math.min(3600000, currentBackoff * 2);
        i--;
        continue;
      }
      console.error(`   ❌ Error: ${err.message}`);
    }

    // Rate limit: 20 second delay between scrapes
    await new Promise(resolve => setTimeout(resolve, 20000));
  }

  await pool.end();
  console.log('✅ Backfill complete');
}

// Run only when executed directly (not imported)
if (require.main === module) {
  (async () => {
    try {
      const args = process.argv.slice(2);
      if (args.includes('--audit')) {
        await auditCoverage();
      } else if (args.includes('--backfill')) {
        const topArg = args.find(a => a.startsWith('--top='));
        const topN = topArg ? parseInt(topArg.split('=')[1]) : 500;
        const catArg = args.find(a => a.startsWith('--category='));
        const categories = catArg ? catArg.split('=')[1].split(',') : undefined;
        await backfillSpecs(topN, categories);
      } else {
        console.log('Usage: npx tsx src/lib/scraper/1688-factory.ts --audit | --backfill [--top=N]');
      }
    } catch (err) {
      console.error('Fatal:', err);
      process.exit(1);
    }
  })();
}
