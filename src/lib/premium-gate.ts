/**
 * Premium gating helpers for API routes
 *
 * Usage in any API route:
 *   import { requirePremium } from '@/lib/premium-gate';
 *
 *   export async function GET(request: Request) {
 *     const auth = await requirePremium(request);
 *     if (auth.response) return auth.response; // 401/403 response
 *     // auth.user is guaranteed to have premium access
 *   }
 */
import { NextResponse } from 'next/server';
import { authenticateRequest, hasPremiumAccess, type SessionUser } from './auth-session';

export type PremiumAuthResult =
  | { allowed: true; user: SessionUser; response?: never }
  | { allowed: false; user?: never; response: NextResponse };

/**
 * Require authenticated user with mentorado or admin subscription.
 * Returns { allowed: true, user } if authorized,
 * or { allowed: false, response } with appropriate error.
 */
export async function requirePremium(request: Request): Promise<PremiumAuthResult> {
  const user = await authenticateRequest(request);

  if (!user) {
    return {
      allowed: false,
      response: NextResponse.json(
        {
          error: 'Authentication required',
          message: 'Please log in to access premium insights.',
          premium_required: true,
        },
        { status: 401 }
      ),
    };
  }

  if (!hasPremiumAccess(user.subscription)) {
    return {
      allowed: false,
      response: NextResponse.json(
        {
          error: 'Premium subscription required',
          message: 'This content requires a Mentorado subscription.',
          premium_required: true,
          current_tier: user.subscription,
          upgrade_to: 'mentorado',
        },
        { status: 403 }
      ),
    };
  }

  return { allowed: true, user };
}

/**
 * Require any authenticated user (free or premium).
 */
export async function requireAuth(request: Request): Promise<PremiumAuthResult> {
  const user = await authenticateRequest(request);

  if (!user) {
    return {
      allowed: false,
      response: NextResponse.json(
        {
          error: 'Authentication required',
          message: 'Please log in to access this content.',
        },
        { status: 401 }
      ),
    };
  }

  return { allowed: true, user };
}

/**
 * Filter premium insight fields based on user's subscription tier.
 * Returns the full object for premium users, or a sanitized version for free users.
 *
 * Fields gated behind premium:
 *   - trend_score
 *   - novelty_score
 *   - profit_margin_estimate
 *   - competition_level
 *   - insight_summary
 *   - content_angle
 *   - opportunity_score
 *   - is_premium_insight
 *   - completeness_score
 */
const PREMIUM_FIELDS = [
  'trend_score',
  'novelty_score',
  'profit_margin_estimate',
  'competition_level',
  'insight_summary',
  'content_angle',
  'opportunity_score',
  'is_premium_insight',
  'completeness_score',
] as const;

export type GatedProduct<T extends Record<string, any>> = T & {
  _premium_locked: boolean;
  _gated_fields: string[];
};

export function gateProductInsights<T extends Record<string, any>>(
  product: T,
  isPremiumUser: boolean
): GatedProduct<T> {
  if (isPremiumUser) {
    return { ...product, _premium_locked: false, _gated_fields: [] };
  }

  const gated: string[] = [];
  const sanitized = { ...product };

  for (const field of PREMIUM_FIELDS) {
    if (field in sanitized) {
      gated.push(field);
      delete (sanitized as any)[field];
    }
  }

  return {
    ...sanitized,
    _premium_locked: true,
    _gated_fields: gated,
  } as GatedProduct<T>;
}

/**
 * Gate an array of products.
 */
export function gateProductsInsights<T extends Record<string, any>>(
  products: T[],
  isPremiumUser: boolean
): GatedProduct<T>[] {
  return products.map(p => gateProductInsights(p, isPremiumUser));
}
