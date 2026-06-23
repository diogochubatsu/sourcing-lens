import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db-pg';
import { taxonomyCache } from '@/lib/cache';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const level = searchParams.get('level');
  const parent = searchParams.get('parent');

  const cacheKey = `taxonomy:${level || ''}:${parent || ''}`;
  const cached = taxonomyCache.get(cacheKey);
  if (cached) {
    return NextResponse.json(cached);
  }

  try {
    let sql = `
      SELECT 
        t.slug,
        t.level,
        t.parent_slug,
        t.name_pt,
        t.name_en,
        t.icon,
        (SELECT COUNT(*) FROM arbitlens_products p WHERE p.category = t.slug OR p.category_n2 = t.slug OR p.category_n3 = t.slug OR p.category_n4 = t.slug) as product_count,
        (SELECT COUNT(*) FROM taxonomy c WHERE c.parent_slug = t.slug) as children_count
      FROM taxonomy t
      WHERE t.is_active = true
    `;
    const params: any[] = [];

    if (level) {
      sql += ` AND t.level = $${params.length + 1}`;
      params.push(parseInt(level));
    }

    if (parent) {
      sql += ` AND t.parent_slug = $${params.length + 1}`;
      params.push(parent);
    }

    sql += ` ORDER BY t.level, t.slug`;

    const categories = await query(sql, params);

    let result;
    if (!level && !parent) {
      const tree = buildTree(categories);
      result = { categories: tree };
    } else {
      result = { categories };
    }

    taxonomyCache.set(cacheKey, result);
    return NextResponse.json(result);
  } catch (error: any) {
    console.error('Taxonomy error:', error.message);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

function buildTree(categories: any[]) {
  const map = new Map();
  const roots: any[] = [];
  for (const cat of categories) {
    map.set(cat.slug, { ...cat, children: [] });
  }
  for (const cat of categories) {
    const node = map.get(cat.slug);
    if (cat.parent_slug && map.has(cat.parent_slug)) {
      map.get(cat.parent_slug).children.push(node);
    } else {
      roots.push(node);
    }
  }
  return roots;
}
