import { NextResponse } from 'next/server';
import { query } from '@/lib/db-pg';

export async function GET() {
  try {
    const matches = await query(`
      SELECT 
        p1.platform || '_' || p1.platform_id as product_id,
        p1.platform,
        p1.title,
        p1.price,
        p1.image_urls,
        p1.url,
        p1.sales_30d,
        m.confidence
      FROM arbitlens_matches m
      JOIN arbitlens_products p1 ON m.product_a_id = p1.id
      WHERE m.confidence > 0.7
        AND p1.is_active = true
      ORDER BY m.confidence DESC
      LIMIT 20
    `);

    return NextResponse.json({
      matches: matches.map(m => ({
        ...m,
        image_url: m.image_urls?.[0] || null,
        price: m.price ? parseFloat(m.price) : null,
        confidence: m.confidence ? parseFloat(m.confidence) : null,
      })),
    });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
