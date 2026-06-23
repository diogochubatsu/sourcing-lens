import { NextResponse } from 'next/server';
import { query } from '@/lib/db-pg';
import { statsCache } from '@/lib/cache';

export async function GET() {
  const cached = statsCache.get('global');
  if (cached) {
    return NextResponse.json(cached);
  }

  try {
    const stats = await query(`
      SELECT
        (SELECT COUNT(*) FROM arbitlens_products WHERE is_active = true) as total_products,
        (SELECT COUNT(*) FROM arbitlens_products WHERE is_active = true AND image_embedding IS NOT NULL) as embedded_products,
        (SELECT COUNT(*) FROM arbitlens_matches) as total_matches,
        (SELECT COUNT(DISTINCT category) FROM arbitlens_products WHERE is_active = true AND category IS NOT NULL) as total_categories,
        (SELECT COUNT(*) FROM taxonomy WHERE is_active = true) as taxonomy_entries
    `);

    const categoryStats = await query(`
      SELECT category, COUNT(*) as count
      FROM arbitlens_products
      WHERE is_active = true AND category IS NOT NULL
      GROUP BY category
      ORDER BY count DESC
    `);

    const result = {
      stats: stats[0],
      categories: categoryStats,
    };

    statsCache.set('global', result);

    return NextResponse.json(result);
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
