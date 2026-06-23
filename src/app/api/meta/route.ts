import { NextResponse } from 'next/server';

import { getMeta } from '@/lib/data-pg';

export async function GET() {
  return NextResponse.json(await getMeta());
}