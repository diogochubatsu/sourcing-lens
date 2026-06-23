import { NextResponse } from 'next/server';
import { query } from '@/lib/db-pg';

export async function GET() {
  try {
    // Get products that have matches (clusters)
    const clusters = await query(`
      SELECT 
        p.id,
        p.platform || '_' || p.platform_id as product_id,
        p.platform,
        p.title,
        p.price,
        p.image_urls,
        p.url,
        p.sales_30d,
        (SELECT COUNT(*) FROM arbitlens_matches m 
         WHERE m.product_a_id = p.id OR m.product_b_id = p.id) as match_count
      FROM arbitlens_products p
      WHERE p.is_active = true
        AND p.id IN (
          SELECT DISTINCT product_a_id FROM arbitlens_matches WHERE confidence > 0.7
          UNION
          SELECT DISTINCT product_b_id FROM arbitlens_matches WHERE confidence > 0.7
        )
      ORDER BY match_count DESC
      LIMIT 20
    `);

    return NextResponse.json({
      clusters: clusters.map(c => ({
        ...c,
        image_url: c.image_urls?.[0] || null,
        price: c.price ? parseFloat(c.price) : null,
      })),
    });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
