import { NextRequest, NextResponse } from 'next/server';
import { query, queryOne } from '@/lib/db-pg';
import { hashPassword } from '@/lib/auth-session';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { email, password, name } = body;

    if (!email || !password) {
      return NextResponse.json({ error: 'Email and password are required' }, { status: 400 });
    }

    // Check if user exists
    const existing = await queryOne('SELECT id FROM users WHERE email = $1', [email.toLowerCase().trim()]);
    if (existing) {
      return NextResponse.json({ error: 'Email already registered' }, { status: 409 });
    }

    // Create user
    const passwordHash = await hashPassword(password);
    const result = await queryOne(
      `INSERT INTO users (email, password_hash, name) 
       VALUES ($1, $2, $3) 
       RETURNING id, email, name, subscription`,
      [email.toLowerCase().trim(), passwordHash, name || null]
    );

    // Create session
    const token = crypto.randomUUID();
    await query(
      `INSERT INTO user_sessions (user_id, token, expires_at) 
       VALUES ($1, $2, NOW() + INTERVAL '7 days')`,
      [result!.id, token]
    );

    const response = NextResponse.json({ user: result });
    response.cookies.set('session', token, {
      httpOnly: true,
      secure: true,
      sameSite: 'lax',
      maxAge: 7 * 24 * 60 * 60,
    });

    return response;
  } catch (error: any) {
    console.error('Register error:', error.message);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
