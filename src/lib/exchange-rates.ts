const CACHE_TTL_MS = 60 * 60 * 1000; // 1 hour
let cache: { rates: Record<string, number>; ts: number } | null = null;

const FALLBACK_RATES: Record<string, number> = {
  CNY: 0.78,
  USD: 5.69,
};

export async function getBrlRate(currency: string): Promise<number> {
  const upper = currency.toUpperCase();
  if (upper === 'BRL') return 1;

  const now = Date.now();
  if (cache && now - cache.ts < CACHE_TTL_MS) {
    if (cache.rates[upper]) return cache.rates[upper];
  }

  try {
    const res = await fetch('https://open.er-api.com/v6/latest/BRL', {
      signal: AbortSignal.timeout(5000),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    if (data?.rates) {
      const inverted: Record<string, number> = {};
      for (const [code, rate] of Object.entries(data.rates) as [string, number][]) {
        inverted[code] = 1 / rate;
      }
      cache = { rates: inverted, ts: now };
      if (inverted[upper]) return inverted[upper];
    }
  } catch {}

  return FALLBACK_RATES[upper] ?? 1;
}

export function toBrlStatic(price: number | null, currency: string): number | null {
  if (!price) return null;
  if (currency === 'BRL') return Math.round(price * 100) / 100;
  if (currency === 'CNY') return Math.round(price * 0.78 * 100) / 100;
  if (currency === 'USD') return Math.round(price * 5.69 * 100) / 100;
  return Math.round(price * 100) / 100;
}
