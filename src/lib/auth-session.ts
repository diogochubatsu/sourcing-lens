/**
 * Auth utilities for premium insight gating
 *
 * Token-based auth: users register/login, receive a session token,
 * send it as Authorization: Bearer <token> or ?token=<token>
 *
 * Subscription tiers:
 *   'free'      → basic product catalog
 *   'mentorado' → AI insights, trend scores, profit margins, premium products
 *   'admin'     → everything + admin features
 */
import * as crypto from 'crypto';
import { promisify } from 'util';
import { query, queryOne } from './db-pg';

const scryptAsync = promisify(crypto.scrypt);

// ─── Password hashing ──────────────────────────────────────────────

export async function hashPassword(password: string): Promise<string> {
  const salt = crypto.randomBytes(16).toString('hex');
  const derived = await scryptAsync(password, salt, 64);
  return salt + ':' + (derived as Buffer).toString('hex');
}

export async function verifyPassword(
  password: string,
  stored: string
): Promise<boolean> {
  const [salt, hash] = stored.split(':');
  const derived = await scryptAsync(password, salt, 64);
  return (derived as Buffer).toString('hex') === hash;
}

// ─── Session tokens ────────────────────────────────────────────────

const SESSION_TTL_HOURS = 72; // 3 days

export function generateToken(): string {
  return crypto.randomBytes(32).toString('hex');
}

export interface SessionUser {
  user_id: number;
  email: string;
  name: string | null;
  subscription: 'free' | 'mentorado' | 'admin';
}

/**
 * Create a new session and return { token, user }
 */
export async function createSession(
  userId: number,
  email: string,
  name: string | null,
  subscription: string
): Promise<{ token: string; expiresAt: Date }> {
  const token = generateToken();
  const expiresAt = new Date(Date.now() + SESSION_TTL_HOURS * 60 * 60 * 1000);

  await query(
    `INSERT INTO user_sessions (user_id, token, expires_at) VALUES ($1, $2, $3)`,
    [userId, token, expiresAt]
  );

  return { token, expiresAt };
}

/**
 * Validate a session token and return the user, or null if expired/invalid
 */
export async function validateSession(token: string): Promise<SessionUser | null> {
  const row = await queryOne<{ user_id: number; email: string; name: string | null; subscription: string }>(
    `SELECT u.id as user_id, u.email, u.name, u.subscription
     FROM user_sessions s
     JOIN users u ON u.id = s.user_id
     WHERE s.token = $1 AND s.expires_at > NOW()`,
    [token]
  );

  if (!row) return null;

  return {
    user_id: row.user_id,
    email: row.email,
    name: row.name,
    subscription: row.subscription as 'free' | 'mentorado' | 'admin',
  };
}

/**
 * Delete a session (logout)
 */
export async function deleteSession(token: string): Promise<void> {
  await query(`DELETE FROM user_sessions WHERE token = $1`, [token]);
}

/**
 * Delete all sessions for a user (force logout everywhere)
 */
export async function deleteUserSessions(userId: number): Promise<void> {
  await query(`DELETE FROM user_sessions WHERE user_id = $1`, [userId]);
}

// ─── Subscription checks ──────────────────────────────────────────

export function hasPremiumAccess(subscription: string): boolean {
  return subscription === 'mentorado' || subscription === 'admin';
}

/**
 * Extract token from request (Bearer header, cookie, or query param)
 */
export function extractToken(request: Request): string | null {
  // 1. Authorization: Bearer <token>
  const authHeader = request.headers.get('authorization');
  if (authHeader?.startsWith('Bearer ')) {
    return authHeader.slice(7);
  }

  // 2. Cookie
  const cookies = request.headers.get('cookie');
  if (cookies) {
    const match = cookies.match(/session_token=([^;]+)/);
    if (match) return match[1];
  }

  // 3. Query param (fallback for non-browser clients)
  const url = new URL(request.url);
  return url.searchParams.get('token');
}

/**
 * Full auth check: extract token, validate session, return user or null
 */
export async function authenticateRequest(request: Request): Promise<SessionUser | null> {
  const token = extractToken(request);
  if (!token) return null;
  return validateSession(token);
}
