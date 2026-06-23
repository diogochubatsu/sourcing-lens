import { NextRequest, NextResponse } from 'next/server';
import { execFileSync } from 'child_process';
import path from 'path';

const SCRIPT_DIR = path.join(process.cwd(), 'scripts', 'arbitlens');

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.get('q');
  const action = searchParams.get('action') || 'trends';
  const days = parseInt(searchParams.get('days') || '30');

  if (action === 'recent') {
    // Get recent queries
    try {
      const script = path.join(SCRIPT_DIR, 'price_history.py');
      const output = execFileSync('python3', [
        '-u', script, '--recent', '20',
      ], {
        cwd: process.cwd(),
        timeout: 10000,
        encoding: 'utf-8',
      });
      return NextResponse.json(JSON.parse(output));
    } catch {
      return NextResponse.json({ queries: [] });
    }
  }

  if (!query) {
    return NextResponse.json({ error: 'Missing ?q= parameter' }, { status: 400 });
  }

  try {
    const script = path.join(SCRIPT_DIR, 'price_history.py');
    const output = execFileSync('python3', [
      '-u', script, '--trends', query, String(days),
    ], {
      cwd: process.cwd(),
      timeout: 10000,
      encoding: 'utf-8',
    });
    return NextResponse.json(JSON.parse(output));
  } catch (error: any) {
    return NextResponse.json({ error: error.message || 'Failed' }, { status: 500 });
  }
}
