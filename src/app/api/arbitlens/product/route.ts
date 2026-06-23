import { NextRequest, NextResponse } from 'next/server';
import { query, queryOne } from '@/lib/db-pg';
import { productCache } from '@/lib/cache';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const productId = searchParams.get('id');

  if (!productId) {
    return NextResponse.json({ error: 'Missing ?id= parameter' }, { status: 400 });
  }

  // Check cache
  const cached = productCache.get(productId);
  if (cached) {
    return NextResponse.json(cached);
  }

  try {
    // Get product by platform_platform_id format
    const parts = productId.split('_', 2);
    const platform = parts[0];
    const platformId = productId.replace(platform + '_', '');

    const product = await queryOne(`
      SELECT 
        id, platform, platform_id, title, title_translated,
        price, currency, url, image_urls, image_hash,
        supplier_name, moq, sales_total, sales_30d,
        review_count, review_avg, category, bsr_rank,
        first_seen, last_updated
      FROM arbitlens_products
      WHERE platform = $1 AND platform_id = $2
    `, [platform, platformId]);

    if (!product) {
      return NextResponse.json({ error: 'Product not found' }, { status: 404 });
    }

    // Get visual matches (top 8)
    const matches = await query(`
      SELECT 
        p.platform || '_' || p.platform_id as product_id,
        p.platform,
        p.title,
        p.price,
        p.image_urls,
        p.category,
        p.supplier_name,
        p.moq,
        p.sales_30d,
        p.review_count,
        1 - (p.image_embedding <=> (
          SELECT image_embedding FROM arbitlens_products 
          WHERE platform = $1 AND platform_id = $2
        )) as similarity
      FROM arbitlens_products p
      WHERE p.id != $3
        AND p.image_embedding IS NOT NULL
        AND p.is_active = true
      ORDER BY p.image_embedding <=> (
        SELECT image_embedding FROM arbitlens_products 
        WHERE platform = $1 AND platform_id = $2
      )
      LIMIT 8
    `, [platform, platformId, product.id]);

    // Get cross-platform matches (same product on different platforms)
    const crossPlatform = await query(`
      SELECT 
        p.platform || '_' || p.platform_id as product_id,
        p.platform,
        p.title,
        p.price,
        p.image_urls,
        p.supplier_name,
        m.confidence
      FROM arbitlens_matches m
      JOIN arbitlens_products p ON (
        (m.product_b_id = p.id AND m.product_a_id = $1)
        OR (m.product_a_id = p.id AND m.product_b_id = $1)
      )
      WHERE m.confidence > 0.7
      ORDER BY m.confidence DESC
      LIMIT 5
    `, [product.id]);

    const result = {
      product: {
        ...product,
        product_id: `${product.platform}_${product.platform_id}`,
      },
      matches: matches.map(m => ({
        ...m,
        image_url: m.image_urls?.[0] || null,
        price: m.price ? parseFloat(m.price) : null,
        similarity: m.similarity ? parseFloat(m.similarity) : null,
      })),
      cross_platform: crossPlatform.map(cp => ({
        ...cp,
        image_url: cp.image_urls?.[0] || null,
        price: cp.price ? parseFloat(cp.price) : null,
        confidence: cp.confidence ? parseFloat(cp.confidence) : null,
      })),
    };

    // Cache the result
    productCache.set(productId, result);

    return NextResponse.json(result);
  } catch (error: any) {
    console.error('Product fetch error:', error.message);
    return NextResponse.json({ error: error.message || 'Failed' }, { status: 500 });
  }
}
