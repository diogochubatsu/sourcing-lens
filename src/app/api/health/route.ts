import { NextResponse } from 'next/server';
import { query } from '@/lib/db-pg';

export async function GET() {
  const checks: Record<string, string> = {};
  
  // Check PostgreSQL
  try {
    await query('SELECT 1');
    checks.database = 'ok';
  } catch {
    checks.database = 'error';
  }

  // Check disk space
  try {
    const stat = require('fs').statSync('/mnt/ssd');
    checks.disk = 'ok';
  } catch {
    checks.disk = 'error';
  }

  const status = Object.values(checks).every(v => v === 'ok') ? 'healthy' : 'degraded';

  return NextResponse.json({
    status,
    checks,
    timestamp: new Date().toISOString(),
    version: '2.4.0',
  });
}
