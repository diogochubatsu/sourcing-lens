import { NextRequest, NextResponse } from 'next/server';
import { query, queryOne } from '@/lib/db-pg';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const n1 = searchParams.get('n1');
  const n2 = searchParams.get('n2');
  const n3 = searchParams.get('n3');
  const n4 = searchParams.get('n4');
  const limit = parseInt(searchParams.get('limit') || '50');
  const offset = parseInt(searchParams.get('offset') || '0');
  const sort = searchParams.get('sort') || 'price';
  const platform = searchParams.get('platform');

  try {
    const conditions: string[] = ['p.is_active = true'];
    const params: any[] = [];

    if (n1) {
      conditions.push(`(p.category = $${params.length + 1} OR p.category_path LIKE $${params.length + 2})`);
      params.push(n1, `${n1}.%`);
    }
    if (n2) {
      conditions.push(`(p.category_n2 = $${params.length + 1} OR p.category_path LIKE $${params.length + 2})`);
      params.push(n2, `%.${n2}.%`);
    }
    if (n3) {
      conditions.push(`(p.category_n3 = $${params.length + 1} OR p.category_path LIKE $${params.length + 2})`);
      params.push(n3, `%.${n3}.%`);
    }
    if (n4) {
      conditions.push(`p.category_n4 = $${params.length + 1}`);
      params.push(n4);
    }
    if (platform) {
      conditions.push(`p.platform = $${params.length + 1}`);
      params.push(platform);
    }

    const where = conditions.join(' AND ');

    const countResult = await query(
      `SELECT COUNT(*) as total FROM arbitlens_products p WHERE ${where}`,
      params
    );
    const total = countResult[0]?.total || 0;

    let orderClause = 'p.price ASC';
    if (sort === 'sales') orderClause = 'COALESCE(p.sales_30d, 0) DESC';
    if (sort === 'newest') orderClause = 'p.last_updated DESC';

    const products = await query(`
      SELECT 
        p.id,
        p.platform || '_' || p.platform_id as product_id,
        p.platform,
        p.title,
        p.title_translated,
        p.price,
        p.currency,
        p.url,
        p.image_urls,
        p.supplier_name,
        p.moq,
        p.sales_30d,
        p.review_count,
        p.review_avg,
        p.category,
        p.category_n2,
        p.category_n3,
        p.category_n4,
        p.category_path
      FROM arbitlens_products p
      WHERE ${where}
      ORDER BY ${orderClause}
      LIMIT $${params.length + 1} OFFSET $${params.length + 2}
    `, [...params, limit, offset]);

    const breadcrumbs: any[] = [];
    for (const slug of [n1, n2, n3, n4].filter(Boolean)) {
      const cat = await queryOne(`SELECT slug, name_pt, icon FROM taxonomy WHERE slug = $1`, [slug]);
      if (cat) breadcrumbs.push(cat);
    }

    const currentSlug = n4 || n3 || n2 || n1;
    const subcategories = currentSlug ? await query(`
      SELECT 
        t.slug,
        t.level,
        t.name_pt,
        t.icon,
        (SELECT COUNT(*) FROM arbitlens_products p 
         WHERE p.category = t.slug OR p.category_n2 = t.slug 
         OR p.category_n3 = t.slug OR p.category_n4 = t.slug
         OR p.category_path LIKE t.slug || '.%') as product_count
      FROM taxonomy t
      WHERE t.parent_slug = $1 AND t.is_active = true
      ORDER BY t.slug
    `, [currentSlug]) : [];

    return NextResponse.json({
      total,
      products,
      breadcrumbs,
      subcategories,
      limit,
      offset,
    });
  } catch (error: any) {
    console.error('Products by category error:', error.message);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
