import { NextRequest, NextResponse } from 'next/server';
import { execFileSync } from 'child_process';
import path from 'path';

const SCRIPT_DIR = path.join(process.cwd(), 'scripts', 'arbitlens');

export async function DELETE() {
  try {
    const script = path.join(SCRIPT_DIR, 'cache.py');
    execFileSync('python3', ['-u', script, '--clear'], {
      cwd: process.cwd(),
      timeout: 10000,
      encoding: 'utf-8',
    });
    return NextResponse.json({ message: 'Cache cleared' });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
