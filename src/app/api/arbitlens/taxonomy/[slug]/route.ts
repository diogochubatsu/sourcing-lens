import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db-pg';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ slug: string }> }
) {
  const { slug } = await params;

  try {
    const category = (await query(`
      SELECT 
        t.slug,
        t.level,
        t.parent_slug,
        t.name_pt,
        t.name_en,
        t.icon,
        t.keywords
      FROM taxonomy t
      WHERE t.slug = $1 AND t.is_active = true
    `, [slug]))[0];

    if (!category) {
      return NextResponse.json({ error: 'Category not found' }, { status: 404 });
    }

    const children = await query(`
      SELECT 
        t.slug,
        t.level,
        t.name_pt,
        t.name_en,
        t.icon,
        (SELECT COUNT(*) FROM arbitlens_products p 
         WHERE p.category = t.slug OR p.category_n2 = t.slug 
         OR p.category_n3 = t.slug OR p.category_n4 = t.slug
         OR p.category_path LIKE t.slug || '.%') as product_count
      FROM taxonomy t
      WHERE t.parent_slug = $1 AND t.is_active = true
      ORDER BY t.slug
    `, [slug]);

    const productCount = (await query(`
      SELECT COUNT(*) as count
      FROM arbitlens_products
      WHERE is_active = true
        AND (category = $1 OR category_n2 = $1 OR category_n3 = $1 OR category_n4 = $1
             OR category_path LIKE $1 || '.%')
    `, [slug]))[0];

    return NextResponse.json({
      ...category,
      product_count: productCount?.count || 0,
      children,
    });
  } catch (error: any) {
    console.error('Taxonomy slug error:', error.message);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
