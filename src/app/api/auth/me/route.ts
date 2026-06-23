import { NextRequest, NextResponse } from 'next/server';
import { queryOne } from '@/lib/db-pg';

export async function GET(request: NextRequest) {
  try {
    const token = request.cookies.get('session')?.value;
    
    if (!token) {
      return NextResponse.json({ user: null });
    }

    const session = await queryOne(
      `SELECT u.id, u.email, u.name, u.subscription, u.created_at
       FROM user_sessions s
       JOIN users u ON s.user_id = u.id
       WHERE s.token = $1 AND s.expires_at > NOW()`,
      [token]
    );

    if (!session) {
      return NextResponse.json({ user: null });
    }

    return NextResponse.json({ user: session });
  } catch (error: any) {
    return NextResponse.json({ user: null });
  }
}
