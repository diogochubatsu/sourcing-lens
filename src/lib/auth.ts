import { NextRequest, NextResponse } from 'next/server';

export function getApiKey(): string {
  return process.env.API_KEY || 'dev';
}

export function isAuthorized(request: NextRequest): boolean {
  const headerValue = request.headers.get('x-api-key');
  return headerValue === getApiKey();
}

export function requireApiKey(request: NextRequest): NextResponse | null {
  if (isAuthorized(request)) {
    return null;
  }

  return NextResponse.json(
    {
      error: 'Unauthorized',
      message: 'Provide a valid X-API-Key header.',
    },
    { status: 401 }
  );
}