import { LRUCache } from 'lru-cache';

interface CacheOptions {
  max?: number;
  ttl?: number;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const caches = new Map<string, LRUCache<string, any>>();

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function getCache(name: string, options: CacheOptions = {}): LRUCache<string, any> {
  if (caches.has(name)) {
    return caches.get(name)!;
  }

  const cache = new LRUCache<string, any>({
    max: options.max || 500,
    ttl: options.ttl || 1000 * 60 * 5,
  });

  caches.set(name, cache);
  return cache;
}

export function invalidateCache(name: string): void {
  const cache = caches.get(name);
  if (cache) {
    cache.clear();
  }
}

export function invalidateAllCaches(): void {
  Array.from(caches.values()).forEach(cache => cache.clear());
}

export const searchCache = getCache('search', { max: 200, ttl: 1000 * 60 * 2 });
export const taxonomyCache = getCache('taxonomy', { max: 50, ttl: 1000 * 60 * 30 });
export const statsCache = getCache('stats', { max: 10, ttl: 1000 * 60 * 5 });
export const productCache = getCache('product', { max: 100, ttl: 1000 * 60 * 10 });
