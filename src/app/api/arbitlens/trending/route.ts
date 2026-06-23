import { NextRequest, NextResponse } from 'next/server';
import { execFileSync } from 'child_process';
import path from 'path';

const SCRIPT_DIR = path.join(process.cwd(), 'scripts', 'arbitlens');

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const maxResults = parseInt(searchParams.get('k') || '10');

  try {
    const script = path.join(SCRIPT_DIR, 'search.py');
    const output = execFileSync('python3', ['-u', script, '', String(maxResults)], {
      cwd: process.cwd(),
      timeout: 120000,
      encoding: 'utf-8',
      maxBuffer: 2 * 1024 * 1024,
    });

    const result = JSON.parse(output);
    return NextResponse.json(result);
  } catch (error: any) {
    console.error('Trending error:', error.message);
    if (error.killed) {
      return NextResponse.json({ error: 'Trending timed out (2 min limit)' }, { status: 408 });
    }
    return NextResponse.json({ error: error.message || 'Trending failed' }, { status: 500 });
  }
}
