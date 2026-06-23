import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db-pg';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  
  // Parse filter params
  const category = searchParams.get('category') || null;
  const platforms = searchParams.get('platform')?.split(',').filter(Boolean) || null;
  const minPrice = searchParams.get('min_price') ? parseFloat(searchParams.get('min_price')!) : null;
  const maxPrice = searchParams.get('max_price') ? parseFloat(searchParams.get('max_price')!) : null;
  const minSales = searchParams.get('min_sales') ? parseInt(searchParams.get('min_sales')!) : null;
  const minMatch = searchParams.get('min_match') ? parseFloat(searchParams.get('min_match')!) : null;
  const sort = searchParams.get('sort') || 'price_asc';
  const page = parseInt(searchParams.get('page') || '1');
  const limit = parseInt(searchParams.get('limit') || '50');
  const offset = (page - 1) * limit;

  try {
    // Build WHERE clause dynamically
    const conditions: string[] = ['p.is_active = true'];
    const params: any[] = [];
    let paramIdx = 1;

    if (category) {
      conditions.push(`(p.category = $${paramIdx} OR p.category LIKE $${paramIdx} || '.%')`);
      params.push(category);
      paramIdx++;
    }

    if (platforms && platforms.length > 0) {
      conditions.push(`p.platform = ANY($${paramIdx})`);
      params.push(platforms);
      paramIdx++;
    }

    if (minPrice !== null) {
      conditions.push(`p.price >= $${paramIdx}`);
      params.push(minPrice);
      paramIdx++;
    }

    if (maxPrice !== null) {
      conditions.push(`p.price <= $${paramIdx}`);
      params.push(maxPrice);
      paramIdx++;
    }

    if (minSales !== null) {
      conditions.push(`p.sales_30d >= $${paramIdx}`);
      params.push(minSales);
      paramIdx++;
    }

    if (minMatch !== null) {
      conditions.push(`m.confidence >= $${paramIdx}`);
      params.push(minMatch);
      paramIdx++;
    }

    const whereClause = conditions.join(' AND ');

    // Sort clause
    const sortClause = {
      'price_asc': 'p.price ASC NULLS LAST',
      'price_desc': 'p.price DESC NULLS LAST',
      'sales_desc': 'p.sales_30d DESC NULLS LAST',
      'match_desc': 'm.confidence DESC NULLS LAST',
    }[sort] || 'p.price ASC NULLS LAST';

    // Main query
    const sql = `
      SELECT 
        p.id,
        p.platform || '_' || p.platform_id as product_id,
        p.platform,
        p.title,
        p.price,
        p.image_urls,
        p.url,
        p.sales_30d,
        p.category,
        m.confidence
      FROM arbitlens_products p
      LEFT JOIN arbitlens_matches m ON p.id = m.product_a_id
      WHERE ${whereClause}
      ORDER BY ${sortClause}
      LIMIT $${paramIdx} OFFSET $${paramIdx + 1}
    `;
    params.push(limit, offset);

    const products = await query(sql, params);

    // Count total
    const countSql = `
      SELECT COUNT(*) as total
      FROM arbitlens_products p
      LEFT JOIN arbitlens_matches m ON p.id = m.product_a_id
      WHERE ${whereClause}
    `;
    const countResult = await query(countSql, params.slice(0, -2));
    const total = parseInt(countResult[0]?.total || '0');

    // Aggregates
    const aggSql = `
      SELECT 
        AVG(p.price) as avg_price,
        COUNT(DISTINCT CASE WHEN m.confidence IS NOT NULL THEN p.id END) as matched_count
      FROM arbitlens_products p
      LEFT JOIN arbitlens_matches m ON p.id = m.product_a_id
      WHERE ${whereClause}
    `;
    const aggResult = await query(aggSql, params.slice(0, -2));

    // Platform distribution
    const platformSql = `
      SELECT platform, COUNT(*) as count
      FROM arbitlens_products p
      WHERE ${whereClause.replace(/AND m\.confidence.*$/, '')}
      GROUP BY platform
      ORDER BY count DESC
    `;
    const platformResult = await query(platformSql, params.slice(0, -2));

    return NextResponse.json({
      products: products.map(p => ({
        ...p,
        image_url: p.image_urls?.[0] || null,
        price: p.price ? parseFloat(p.price) : null,
        confidence: p.confidence ? parseFloat(p.confidence) : null,
      })),
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
      aggregates: {
        avg_price: aggResult[0]?.avg_price ? parseFloat(aggResult[0].avg_price) : 0,
        matched_count: parseInt(aggResult[0]?.matched_count || '0'),
      },
      platform_counts: platformResult.reduce((acc: Record<string, number>, r: any) => {
        acc[r.platform] = parseInt(r.count);
        return acc;
      }, {}),
    });
  } catch (error: any) {
    console.error('Explore error:', error.message);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
