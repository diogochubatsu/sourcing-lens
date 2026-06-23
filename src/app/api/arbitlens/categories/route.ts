import { NextRequest, NextResponse } from 'next/server';
import { execFileSync } from 'child_process';
import path from 'path';
import { taxonomyCache } from '@/lib/cache';

const CATEGORIES = [
  { slug: 'audio', name: 'Áudio & Microfones', icon: '🎙️' },
  { slug: 'wearables', name: 'Wearables & Smartwatches', icon: '⌚' },
  { slug: 'carregadores', name: 'Carregadores & Power Banks', icon: '🔋' },
  { slug: 'camera', name: 'Câmeras & Webcams', icon: '📷' },
  { slug: 'fones', name: 'Fones & Auscultadores', icon: '🎧' },
  { slug: 'cabos', name: 'Cabos & Adaptadores', icon: '🔌' },
  { slug: 'gadgets', name: 'Gadgets & Eletrônicos', icon: '💡' },
  { slug: 'iluminacao', name: 'Iluminação LED', icon: '💡' },
];

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const category = searchParams.get('cat') || '';
  const maxResults = parseInt(searchParams.get('k') || '15');

  // Return category list (lightweight, no counts)
  if (!category) {
    return NextResponse.json({ categories: CATEGORIES });
  }

  // Quick count mode
  if (category === '_count') {
    const slug = searchParams.get('slug') || '';
    const cacheKey = `cat-count:${slug}`;
    const cached = taxonomyCache.get(cacheKey);
    if (cached) {
      return NextResponse.json(cached);
    }

    try {
      const script = path.join(process.cwd(), 'scripts', 'arbitlens', 'categories.py');
      const output = execFileSync('python3', ['-u', script, '--search', slug, '3'], {
        timeout: 30000,
        maxBuffer: 1024 * 1024,
        encoding: 'utf-8',
      });
      const data = JSON.parse(output);
      const result = { slug, total_products: data.total_products || 0 };
      taxonomyCache.set(cacheKey, result);
      return NextResponse.json(result);
    } catch {
      return NextResponse.json({ slug, total_products: null });
    }
  }

  // Search a specific category
  const cacheKey = `cat-search:${category}:${maxResults}`;
  const cached = taxonomyCache.get(cacheKey);
  if (cached) {
    return NextResponse.json(cached);
  }

  try {
    const script = path.join(process.cwd(), 'scripts', 'arbitlens', 'categories.py');
    const output = execFileSync('python3', ['-u', script, '--search', category, String(maxResults)], {
      timeout: 90000,
      maxBuffer: 10 * 1024 * 1024,
      encoding: 'utf-8',
    });

    const data = JSON.parse(output);
    taxonomyCache.set(cacheKey, data);
    return NextResponse.json(data);
  } catch (e: any) {
    if (e.stdout) {
      try {
        const data = JSON.parse(e.stdout);
        return NextResponse.json(data);
      } catch {}
    }
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
