import { NextRequest, NextResponse } from 'next/server';
import { query, queryOne } from '@/lib/db-pg';
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

    const alerts = await query(
      `SELECT * FROM price_alerts WHERE user_id = $1 AND is_active = true ORDER BY created_at DESC`,
      [user.user_id]
    );

    return NextResponse.json({ alerts });
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
    const { product_id, platform, target_price } = body;

    if (!product_id || !target_price) {
      return NextResponse.json({ error: 'product_id and target_price required' }, { status: 400 });
    }

    const alert = await queryOne(
      `INSERT INTO price_alerts (user_id, product_id, platform, target_price)
       VALUES ($1, $2, $3, $4) RETURNING *`,
      [user.user_id, product_id, platform || '', target_price]
    );

    return NextResponse.json({ alert });
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
    const alertId = searchParams.get('id');

    if (!alertId) {
      return NextResponse.json({ error: 'Alert ID required' }, { status: 400 });
    }

    await query(
      `DELETE FROM price_alerts WHERE id = $1 AND user_id = $2`,
      [alertId, user.user_id]
    );

    return NextResponse.json({ message: 'Alert deleted' });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
