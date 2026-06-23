import { NextResponse } from 'next/server';

export async function GET() {
  // Redirect browsers requesting /favicon.ico to the SVG favicon
  return NextResponse.redirect(new URL('/favicon.svg', 'http://localhost:3002'));
}
