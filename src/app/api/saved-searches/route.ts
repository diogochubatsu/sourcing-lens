import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/db-pg';
import { extractToken, validateSession } from '@/lib/auth-session';

export async function GET(request: NextRequest) {
  try {
    const token = extractToken(request);
    if (!token) {
      return NextResponse.json({ error: 'Authentication required' }, { status: 401 });
    }

    const user = await validateSession(token);
    if (!user) {
      return NextResponse.json({ error: 'Invalid session' }, { status: 401 });
    }

    const searches = await query(
      `SELECT * FROM saved_searches WHERE user_id = $1 ORDER BY created_at DESC LIMIT 20`,
      [user.user_id]
    );

    return NextResponse.json({ searches });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const token = extractToken(request);
    if (!token) {
      return NextResponse.json({ error: 'Authentication required' }, { status: 401 });
    }

    const user = await validateSession(token);
    if (!user) {
      return NextResponse.json({ error: 'Invalid session' }, { status: 401 });
    }

    const body = await request.json();
    const { query: searchQuery, category, filters } = body;

    if (!searchQuery) {
      return NextResponse.json({ error: 'query required' }, { status: 400 });
    }

    const result = await query(
      `INSERT INTO saved_searches (user_id, query, category, filters)
       VALUES ($1, $2, $3, $4) RETURNING *`,
      [user.user_id, searchQuery, category || null, filters ? JSON.stringify(filters) : null]
    );

    return NextResponse.json({ search: result[0] });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const token = extractToken(request);
    if (!token) {
      return NextResponse.json({ error: 'Authentication required' }, { status: 401 });
    }

    const user = await validateSession(token);
    if (!user) {
      return NextResponse.json({ error: 'Invalid session' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');

    if (!id) {
      return NextResponse.json({ error: 'ID required' }, { status: 400 });
    }

    await query(
      `DELETE FROM saved_searches WHERE id = $1 AND user_id = $2`,
      [id, user.user_id]
    );

    return NextResponse.json({ message: 'Deleted' });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
