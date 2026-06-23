import { NextRequest, NextResponse } from 'next/server';
import { execFileSync } from 'child_process';
import path from 'path';
import { searchCache } from '@/lib/cache';

const SCRIPT_DIR = path.join(process.cwd(), 'scripts', 'arbitlens');

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  let query = searchParams.get('q');
  const isTrending = searchParams.get('trending') === '1';
  const category = searchParams.get('category');
  const limit = parseInt(searchParams.get('k') || '50');
  
  if (!query && isTrending) {
    query = '';
  }
  
  if (query === null && !category) {
    return NextResponse.json({
      error: 'Missing query parameter ?q= or ?category=',
      usage: '/api/arbitlens/search?q=microfone&k=10 or /api/arbitlens/search?category=audio',
    }, { status: 400 });
  }

  // Check cache
  const cacheKey = `search:${query || ''}:${limit}:${category || ''}`;
  const cached = searchCache.get(cacheKey);
  if (cached) {
    return NextResponse.json(cached);
  }
  
  try {
    const script = path.join(SCRIPT_DIR, 'search.py');
    const args = ['-u', script, query || '', String(limit)];
    
    const output = execFileSync('python3', args, {
      cwd: process.cwd(),
      timeout: 60000,
      encoding: 'utf-8',
      maxBuffer: 5 * 1024 * 1024,
    });
    
    const result = JSON.parse(output);
    
    // Add taxonomy info to results if category specified
    if (category && result.products) {
      result.category_filter = category;
    }

    // Cache the result
    searchCache.set(cacheKey, result);
    
    return NextResponse.json(result);
    
  } catch (error: any) {
    console.error('Search error:', error.message);
    
    if (error.killed) {
      return NextResponse.json({
        query,
        products: [],
        total_products: 0,
        platforms: {},
        error: 'Search timed out (60s limit)',
      }, { status: 408 });
    }
    
    return NextResponse.json({
      query,
      products: [],
      total_products: 0,
      platforms: {},
      error: error.message || 'Search failed',
    }, { status: 500 });
  }
}
