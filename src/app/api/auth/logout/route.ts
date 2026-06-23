import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db-pg';

export async function POST(request: NextRequest) {
  try {
    const token = request.cookies.get('session')?.value;
    
    if (token) {
      await query('DELETE FROM user_sessions WHERE token = $1', [token]);
    }

    const response = NextResponse.json({ message: 'Logged out' });
    response.cookies.set('session', '', { httpOnly: true, secure: true, maxAge: 0 });
    
    return response;
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
