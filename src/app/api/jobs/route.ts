import { NextRequest, NextResponse } from 'next/server';
import { execFileSync } from 'child_process';
import path from 'path';

const SCRIPT_DIR = path.join(process.cwd(), 'scripts', 'arbitlens');

export async function GET() {
  try {
    const script = path.join(SCRIPT_DIR, 'job_queue.py');
    const output = execFileSync('python3', ['-u', script, '--list'], {
      cwd: process.cwd(),
      timeout: 10000,
      encoding: 'utf-8',
    });
    return NextResponse.json(JSON.parse(output));
  } catch (error: any) {
    return NextResponse.json({ jobs: [], error: error.message });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { type, params } = body;

    if (!type) {
      return NextResponse.json({ error: 'Job type required' }, { status: 400 });
    }

    const script = path.join(SCRIPT_DIR, 'job_queue.py');
    const output = execFileSync('python3', [
      '-u', script, '--submit', type, JSON.stringify(params || {}),
    ], {
      cwd: process.cwd(),
      timeout: 10000,
      encoding: 'utf-8',
    });

    return NextResponse.json(JSON.parse(output));
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
