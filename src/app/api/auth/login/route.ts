import { NextRequest, NextResponse } from 'next/server';
import { queryOne } from '@/lib/db-pg';
import { verifyPassword } from '@/lib/auth-session';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { email, password } = body;

    if (!email || !password) {
      return NextResponse.json({ error: 'Email and password are required' }, { status: 400 });
    }

    // Find user
    const user = await queryOne(
      'SELECT id, email, name, password_hash, subscription FROM users WHERE email = $1',
      [email.toLowerCase().trim()]
    );

    if (!user) {
      return NextResponse.json({ error: 'Invalid email or password' }, { status: 401 });
    }

    // Verify password
    const valid = await verifyPassword(password, user.password_hash);
    if (!valid) {
      return NextResponse.json({ error: 'Invalid email or password' }, { status: 401 });
    }

    // Update last login
    await queryOne('UPDATE users SET last_login = NOW() WHERE id = $1', [user.id]);

    // Create session
    const token = crypto.randomUUID();
    await queryOne(
      `INSERT INTO user_sessions (user_id, token, expires_at) 
       VALUES ($1, $2, NOW() + INTERVAL '7 days')`,
      [user.id, token]
    );

    const response = NextResponse.json({
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
        subscription: user.subscription,
      }
    });

    response.cookies.set('session', token, {
      httpOnly: true,
      secure: true,
      sameSite: 'lax',
      maxAge: 7 * 24 * 60 * 60,
    });

    return response;
  } catch (error: any) {
    console.error('Login error:', error.message);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
