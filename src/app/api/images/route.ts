import { NextRequest, NextResponse } from 'next/server';
import { Storage } from '@google-cloud/storage';
import { LRUCache } from 'lru-cache';
import crypto from 'crypto';

// ─── Configuration ────────────────────────────────────────────────────────
const PROJECT_ID = process.env.GOOGLE_CLOUD_PROJECT || process.env.GCP_PROJECT_ID || '4766585081';
const BUCKET_NAME = process.env.IMAGE_CACHE_BUCKET || `${PROJECT_ID}.appspot.com`;
const MAX_CACHE_SIZE = process.env.IMAGE_CACHE_MAX_SIZE
  ? parseInt(process.env.IMAGE_CACHE_MAX_SIZE)
  : 250;
const CACHE_TTL_SEC = process.env.IMAGE_CACHE_TTL_SEC
  ? parseInt(process.env.IMAGE_CACHE_TTL_SEC)
  : 60 * 60 * 24 * 30;

// ─── In-memory LRU cache (per-instance) ───────────────────────────────────
const memoryCache = new LRUCache<string, Buffer>({
  max: MAX_CACHE_SIZE,
  ttl: CACHE_TTL_SEC * 1000,
});

// ─── GCS client ────────────────────────────────────────────────────────────
let gcsStorage: Storage | null = null;
function getStorage(): Storage | null {
  if (!gcsStorage) {
    try {
      gcsStorage = new Storage({ projectId: PROJECT_ID });
    } catch (e) {
      console.warn('GCS init failed, using memory-only cache:', e);
      gcsStorage = null;
    }
  }
  return gcsStorage;
}

// ─── Helpers ──────────────────────────────────────────────────────────────
function hashUrl(url: string): string {
  return crypto.createHash('sha256').update(url).digest('hex');
}

function isAllowedDomain(url: string): boolean {
  const allowed = ['cbu01.alicdn.com', 'cbu02.alicdn.com', 'cbu03.alicdn.com', 'alicdn.com'];
  try {
    const u = new URL(url);
    return allowed.some((d) => u.hostname.endsWith(d));
  } catch {
    return false;
  }
}

async function fetchImage(url: string): Promise<Buffer> {
  const res = await fetch(url, {
    headers: {
      'User-Agent': 'Mozilla/5.0 (compatible; 1688IntelBot/1.0; +https://intel-dashboard.run.app/)',
      Accept: 'image/*',
    },
    signal: AbortSignal.timeout(15000),
  });
  if (!res.ok) throw new Error(`Fetch failed: ${res.status}`);
  const arrayBuffer = await res.arrayBuffer();
  return Buffer.from(arrayBuffer);
}

async function uploadToGCS(bucket: any, key: string, buffer: Buffer): Promise<void> {
  const file = bucket.file(key);
  await file.save(buffer, {
    contentType: 'image/jpeg',
    metadata: { cacheControl: 'public, max-age=2592000' },
  });
}

// ─── Main ─────────────────────────────────────────────────────────────────
export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const url = searchParams.get('url');
    if (!url) return NextResponse.json({ error: 'Missing ?url=' }, { status: 400 });
    if (!isAllowedDomain(url)) return NextResponse.json({ error: 'URL domain not allowed' }, { status: 403 });

    const key = hashUrl(url);

    // Memory cache hit?
    const mem = memoryCache.get(key);
    if (mem) {
      return new Response(mem as any, {
        headers: { 'Content-Type': 'image/jpeg', 'Cache-Control': 'public, max-age=2592000', 'X-Cache': 'MEMORY' },
      });
    }

    // GCS cache hit?
    const storage = getStorage();
    if (storage) {
      try {
        const bucket = storage.bucket(BUCKET_NAME);
        const file = bucket.file(key);
        const [exists] = await file.exists();
        if (exists) {
          const [buffer] = await file.download();
          memoryCache.set(key, buffer);
          return new Response(buffer as any, {
            headers: { 'Content-Type': 'image/jpeg', 'Cache-Control': 'public, max-age=2592000', 'X-Cache': 'GCS' },
          });
        }
      } catch (e) {
        console.warn('GCS read error (serving origin):', e);
      }
    }

    // Fetch from origin
    const buffer = await fetchImage(url);

    // Write to GCS (best-effort)
    if (storage) {
      try {
        const bucket = storage.bucket(BUCKET_NAME);
        await uploadToGCS(bucket, key, buffer);
      } catch (e) {
        console.warn('GCS upload error:', e);
      }
    }

    memoryCache.set(key, buffer);
    return new Response(buffer as any, {
      headers: { 'Content-Type': 'image/jpeg', 'Cache-Control': 'public, max-age=2592000', 'X-Cache': 'MISS' },
    });
  } catch (error: any) {
    console.error('Image proxy error:', error);
    return NextResponse.json({ error: 'Image fetch failed', details: error.message }, { status: 500 });
  }
}
