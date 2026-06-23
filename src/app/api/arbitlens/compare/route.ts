import { NextRequest, NextResponse } from 'next/server';
import { execFileSync } from 'child_process';
import path from 'path';

const SCRIPT_DIR = path.join(process.cwd(), 'scripts', 'arbitlens');

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const title = searchParams.get('title');
  const platform = searchParams.get('platform') || 'unknown';
  const maxResults = parseInt(searchParams.get('k') || '10');

  if (!title) {
    return NextResponse.json({
      error: 'Missing ?title=... (product name to compare)',
      usage: '/api/arbitlens/compare?title=Microfone+lapela+Q8&platform=rakumart-1688&k=10',
    }, { status: 400 });
  }

  try {
    const script = path.join(SCRIPT_DIR, 'compare.py');
    const escapedTitle = title.replace(/"/g, '\\"');
    const output = execFileSync('python3', ['-u', script, title, platform, String(maxResults)], {
      cwd: process.cwd(),
      timeout: 120000,
      encoding: 'utf-8',
      maxBuffer: 2 * 1024 * 1024,
    });

    const result = JSON.parse(output);
    return NextResponse.json(result);
  } catch (error: any) {
    console.error('Compare error:', error.message);

    if (error.killed) {
      return NextResponse.json({ error: 'Compare timed out (2 min limit)' }, { status: 408 });
    }

    return NextResponse.json({
      error: error.message || 'Compare failed',
    }, { status: 500 });
  }
}