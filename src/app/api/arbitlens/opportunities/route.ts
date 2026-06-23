import { NextRequest, NextResponse } from 'next/server';
import { execFileSync } from 'child_process';
import path from 'path';

const SCRIPT_DIR = path.join(process.cwd(), 'scripts', 'arbitlens');

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const category = searchParams.get('category') || undefined;
  const minScore = parseInt(searchParams.get('min_score') || '0');
  const limit = parseInt(searchParams.get('limit') || '20');

  try {
    const script = path.join(SCRIPT_DIR, 'opportunity_detect.py');
    const args = ['-u', script, '--limit', String(limit)];
    if (category) args.push('--category', category);
    if (minScore > 0) args.push('--min-score', String(minScore));

    const output = execFileSync('python3', args, {
      cwd: process.cwd(),
      timeout: 30000,
      encoding: 'utf-8',
      env: { ...process.env },
    });

    return NextResponse.json(JSON.parse(output));
  } catch (error: any) {
    console.error('Opportunity detection error:', error.message);
    return NextResponse.json({ error: error.message || 'Failed' }, { status: 500 });
  }
}
