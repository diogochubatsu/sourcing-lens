import { NextRequest, NextResponse } from 'next/server';
import { execFileSync } from 'child_process';
import path from 'path';

const SCRIPT_DIR = path.join(process.cwd(), 'scripts', 'arbitlens');

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const productId = searchParams.get('product_id');
  const limit = parseInt(searchParams.get('limit') || '10');

  if (!productId) {
    return NextResponse.json({ error: 'Missing ?product_id= parameter' }, { status: 400 });
  }

  try {
    const script = path.join(SCRIPT_DIR, 'match_pg.py');
    const output = execFileSync('python3', [
      '-u', script, '--product-id', productId, '--limit', String(limit),
    ], {
      cwd: process.cwd(),
      timeout: 15000,
      encoding: 'utf-8',
      env: { ...process.env },
    });

    return NextResponse.json(JSON.parse(output));
  } catch (error: any) {
    console.error('Visual match error:', error.message);
    return NextResponse.json({ error: error.message || 'Visual match failed' }, { status: 500 });
  }
}
