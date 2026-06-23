import { NextRequest, NextResponse } from 'next/server';
import { execFileSync } from 'child_process';
import path from 'path';

const SCRIPT_DIR = path.join(process.cwd(), 'scripts', 'arbitlens');

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const title = searchParams.get('title');
  const productId = searchParams.get('product_id');
  const platform = searchParams.get('platform') || undefined;
  const limit = parseInt(searchParams.get('limit') || '10');

  try {
    const script = path.join(SCRIPT_DIR, 'compare_v2.py');
    const args = ['-u', script, '--limit', String(limit)];

    if (productId) {
      args.push('--product-id', productId);
    } else if (title) {
      args.push('--title', title);
      if (platform) args.push('--platform', platform);
    } else {
      return NextResponse.json({ error: 'Missing ?title= or ?product_id=' }, { status: 400 });
    }

    const output = execFileSync('python3', args, {
      cwd: process.cwd(),
      timeout: 20000,
      encoding: 'utf-8',
      env: { ...process.env },
    });

    return NextResponse.json(JSON.parse(output));
  } catch (error: any) {
    console.error('Compare v2 error:', error.message);
    return NextResponse.json({ error: error.message || 'Failed' }, { status: 500 });
  }
}
