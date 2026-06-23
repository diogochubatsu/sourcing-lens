import { NextRequest } from 'next/server';
import { query } from '@/lib/db-pg';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

// Import scraper functions
import { execSync } from 'child_process';

interface ScrapedProduct {
  offer_id: string;
  title: string;
  price_cny: number;
  image_url: string;
  supplier_name: string;
  moq: string;
  repurchase_rate: number | null;
  sales_volume_estimate: number | null;
}

/**
 * Scrape 1688 search results using Jina Reader API
 */
async function scrape1688Search(keyword: string, limit: number = 20): Promise<ScrapedProduct[]> {
  const url = `https://s.1688.com/selloffer/offer_search.htm?keywords=${encodeURIComponent(keyword)}`;
  const jinaUrl = `https://r.jina.ai/${url}`;

  console.log(`Scraping via Jina: ${url}`);

  try {
    const result = execSync(
      `curl -s "${jinaUrl}" -H "Accept: application/json" -H "X-Return-Format: markdown" --max-time 60`,
      {
        encoding: 'utf-8',
        maxBuffer: 10 * 1024 * 1024,
      }
    );

    const data = JSON.parse(result);
    const content = data?.data?.content || '';

    if (content.length < 1000) {
      throw new Error(`Jina returned too little content (${content.length} chars)`);
    }

    return parseProducts(content, limit);
  } catch (error: any) {
    throw new Error(`Jina scrape failed: ${error.message}`);
  }
}

/**
 * Parse products from Jina markdown content
 */
function parseProducts(markdown: string, limit: number): ScrapedProduct[] {
  const products: ScrapedProduct[] = [];

  // Split by product blocks - look for offerId patterns
  const blocks = markdown.split(/(?=\[Image \d+\])/);

  for (const block of blocks) {
    if (products.length >= limit) break;

    // Extract offer ID
    const offerIdMatch = block.match(/offerId[s=](\d{10,19})/);
    const offerId = offerIdMatch?.[1];

    // Extract title
    const titleMatch = block.match(/物流时效\s*[\d.]+\s+([^\n]{4,150})/)
      || block.match(/!\[.*?\]\(.*?\)\s+(.+?)\s*¥/);
    let title = titleMatch?.[1]?.trim() || null;
    if (title) {
      title = title.replace(/\s*¥.*$/, '').trim();
    }

    // Extract price
    const priceMatch = block.match(/¥\s*([\d.]+)/);
    const price = priceMatch ? parseFloat(priceMatch[1]) : null;
    if (price === null || isNaN(price)) continue;

    // Extract company/supplier
    const companyMatch = block.match(/\[([^\[\]]{2,60})\]\(https?:\/\/shop[\w.-]+\.1688\.com\//i);
    const company = companyMatch?.[1]?.trim() || '';

    // Extract sales volume
    const salesMatch = block.match(/([\d.]+[万千百]?\+?件)/);
    const sales = salesMatch?.[1] || '';

    // Extract image
    const imageMatch = block.match(/https:\/\/cbu01\.alicdn\.com\/img\/ibank\/[^\s"')]+\.(?:jpg|jpeg|png|webp)/i);
    const imageUrl = imageMatch?.[0] || '';

    // Extract MOQ
    const moqMatch = block.match(/(\d+)\s*件起批/);
    const moq = moqMatch ? `${moqMatch[1]} pieces` : 'N/A';

    if (title || offerId) {
      products.push({
        offer_id: offerId || '',
        title: title || '',
        price_cny: price,
        image_url: imageUrl,
        supplier_name: company,
        moq: moq,
        repurchase_rate: null,
        sales_volume_estimate: parseSalesVolume(sales),
      });
    }
  }

  return products;
}

/**
 * Parse sales volume string to number
 * "1.2万件" -> 12000, "500件" -> 500
 */
function parseSalesVolume(sales: string): number | null {
  if (!sales) return null;

  const match = sales.match(/([\d.]+)([万千百])?/);
  if (!match) return null;

  const num = parseFloat(match[1]);
  const unit = match[2];

  if (isNaN(num)) return null;

  switch (unit) {
    case '万': return Math.round(num * 10000);
    case '千': return Math.round(num * 1000);
    case '百': return Math.round(num * 100);
    default: return Math.round(num);
  }
}

/**
 * Store scrape request and results in database
 */
async function storeScrapeResults(
  query_text: string,
  requested_by: string,
  products: ScrapedProduct[]
): Promise<{ request_id: number; result_count: number }> {
  // Create request record
  const requestResult = await query<{ id: number }>(
    `INSERT INTO scrape_requests (query, requested_by, status, result_count, completed_at)
     VALUES ($1, $2, 'done', $3, NOW())
     RETURNING id`,
    [query_text, requested_by, products.length]
  );

  const requestId = requestResult[0].id;

  // Insert products
  for (const product of products) {
    await query(
      `INSERT INTO scrape_results (request_id, offer_id, title, price_cny, image_url, supplier_name, moq, repurchase_rate, sales_volume_estimate)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)`,
      [
        requestId,
        product.offer_id,
        product.title,
        product.price_cny,
        product.image_url,
        product.supplier_name,
        product.moq,
        product.repurchase_rate,
        product.sales_volume_estimate,
      ]
    );
  }

  return { request_id: requestId, result_count: products.length };
}

/**
 * GET /api/scrape - Query existing scrape results
 * POST /api/scrape - Request new scrape
 */
export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const requestId = searchParams.get('request_id');
    const requestedBy = searchParams.get('requested_by') || 'arbitlens';
    const limit = parseInt(searchParams.get('limit') || '100');

    if (requestId) {
      // Get specific request results
      const results = await query(
        `SELECT * FROM scrape_results WHERE request_id = $1 ORDER BY scraped_at DESC LIMIT $2`,
        [parseInt(requestId), limit]
      );

      const request = await query(
        `SELECT * FROM scrape_requests WHERE id = $1`,
        [parseInt(requestId)]
      );

      return Response.json({
        request: request[0] || null,
        results: results,
      });
    }

    // Get recent requests
    const requests = await query(
      `SELECT * FROM scrape_requests WHERE requested_by = $1 ORDER BY requested_at DESC LIMIT $2`,
      [requestedBy, limit]
    );

    return Response.json({ requests });
  } catch (err) {
    console.error('Scrape API error:', err);
    return Response.json({ error: 'Internal error' }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { query: query_text, requested_by = 'arbitlens', limit = 20 } = body;

    if (!query_text || typeof query_text !== 'string') {
      return Response.json({ error: 'Missing query parameter' }, { status: 400 });
    }

    // Check for duplicate request in last hour
    const existing = await query(
      `SELECT id FROM scrape_requests
       WHERE query = $1 AND requested_by = $2 AND requested_at > NOW() - INTERVAL '1 hour'
       LIMIT 1`,
      [query_text, requested_by]
    );

    if (existing.length > 0) {
      return Response.json({
        message: 'Duplicate request found',
        request_id: existing[0].id,
      });
    }

    // Scrape 1688
    const products = await scrape1688Search(query_text, limit);

    // Store results
    const result = await storeScrapeResults(query_text, requested_by, products);

    return Response.json({
      message: 'Scrape completed',
      request_id: result.request_id,
      result_count: result.result_count,
    });
  } catch (err) {
    console.error('Scrape API error:', err);
    return Response.json({ error: 'Internal error' }, { status: 500 });
  }
}
