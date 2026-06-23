/**
 * POST /api/pipeline/ml-bestseller-refresh
 *
 * Trigger the ML bestseller scraper refresh via Cloud Scheduler or manual trigger.
 * Scrapes MercadoLivre bestseller pages using Decodo proxy with IP rotation.
 *
 * Auth: X-API-Key header required
 *
 * Request body (optional):
 *   { "dry_run": true }       — run without DB writes
 *   { "category": "MLB5080" } — single category
 *   { "max_pages": 3 }        — limit pages per category
 *   { "proxy": "residential" } — force specific proxy backend
 *   { "timeout": 600 }        — max seconds (default: 600)
 *
 * Response:
 *   { "ok": true, "result": { ... } }
 *   { "ok": false, "error": "..." }
 */
import { NextRequest, NextResponse } from 'next/server';
import { requireApiKey } from '@/lib/auth';
import { spawn } from 'child_process';
import path from 'path';
import { existsSync } from 'fs';

export async function POST(request: NextRequest) {
  const unauthorized = requireApiKey(request);
  if (unauthorized) return unauthorized;

  const body = await request.json().catch(() => ({}));
  const dryRun = body.dry_run ?? false;
  const category = body.category ?? null;
  const maxPages = body.max_pages ?? 10;
  const proxy = body.proxy ?? 'auto';
  const timeout = body.timeout ?? 600;

  // Resolve the scraper script path
  const candidates = [
    path.join(process.cwd(), 'scripts', 'ml_bestseller_scraper_v2.py'),
    path.join(process.cwd(), '..', '..', 'scripts', 'ml_bestseller_scraper_v2.py'),
    '/mnt/ssd/1688-intel/scripts/ml_bestseller_scraper_v2.py',
  ];

  const scriptPath = candidates.find(p => existsSync(p));
  if (!scriptPath) {
    return NextResponse.json(
      {
        ok: false,
        error: 'Scraper script not found',
        checked: candidates,
      },
      { status: 500 },
    );
  }

  // Build command args
  const args = [scriptPath];
  if (dryRun) args.push('--dry-run');
  if (category) args.push('--category', category);
  args.push('--max-pages', String(maxPages));
  args.push('--proxy', proxy);

  return new Promise<NextResponse>((resolve) => {
    const child = spawn('python3', args, {
      cwd: path.dirname(scriptPath),
      env: { ...process.env },
      stdio: ['ignore', 'pipe', 'pipe'],
      timeout: (timeout + 60) * 1000, // extra 60s for process overhead
    });

    let stdout = '';
    let stderr = '';

    child.stdout?.on('data', (data: Buffer) => {
      stdout += data.toString();
    });

    child.stderr?.on('data', (data: Buffer) => {
      stderr += data.toString();
    });

    child.on('close', (code) => {
      // Extract SUMMARY section from stdout
      const summaryIdx = stdout.indexOf('SUMMARY');
      const summary = summaryIdx !== -1 ? stdout.slice(summaryIdx).trim() : stdout;

      if (code === 0) {
        // Parse summary stats from output
        const totalMatch = stdout.match(/TOTAL:\s+(\d+)\s+products,\s+(\d+)\s+inserted/);
        const result = {
          success: true,
          total_products: totalMatch ? parseInt(totalMatch[1]) : 0,
          total_inserted: totalMatch ? parseInt(totalMatch[2]) : 0,
          dry_run: dryRun,
          proxy: proxy,
          max_pages: maxPages,
          category: category || 'all',
        };

        resolve(
          NextResponse.json(
            {
              ok: true,
              result,
              logs: stdout.slice(-3000), // last 3KB of logs
            },
            { status: 200 },
          ),
        );
      } else {
        resolve(
          NextResponse.json(
            {
              ok: false,
              error: `Scraper exited with code ${code}`,
              logs: stdout.slice(-2000),
              stderr: stderr.slice(-1000),
            },
            { status: 500 },
          ),
        );
      }
    });

    child.on('error', (err) => {
      resolve(
        NextResponse.json(
          {
            ok: false,
            error: `Failed to start scraper: ${err.message}`,
          },
          { status: 500 },
        ),
      );
    });
  });
}

export async function GET() {
  return NextResponse.json({
    endpoint: '/api/pipeline/ml-bestseller-refresh',
    method: 'POST',
    auth: 'X-API-Key header required',
    body: {
      dry_run: 'boolean (optional) — run without DB writes',
      category: 'string (optional) — single category code, e.g. MLB5080',
      max_pages: 'number (optional) — max pages per category (default: 10)',
      proxy: 'string (optional) — auto, site-unblocker, residential, direct (default: auto)',
      timeout: 'number (optional) — max seconds (default: 600)',
    },
  });
}
