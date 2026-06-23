/**
 * POST /api/pipeline/silver-refresh
 *
 * Trigger the silver→gold refresh pipeline.
 * Designed for Cloud Scheduler (daily cron) and manual triggers.
 *
 * Auth: X-API-Key header required
 *
 * Request body (optional):
 *   { "dry_run": true }          — run without modifying data
 *   { "step": 1 }                — run only step 1 (sync)
 *   { "step": 2 }                — run only step 2 (gold views)
 *   { "no_gold": true }          — skip gold view refresh
 *   { "pipeline_version": "v2" } — use v2 with ML integration (default: v2)
 *   { "no_ml": true }            — skip ML integration steps (v2 only)
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
  const step = body.step ?? null;
  const noGold = body.no_gold ?? false;
  const noMl = body.no_ml ?? false;
  const timeout = body.timeout ?? 300;
  // Default to v2 (with ML integration)
  const pipelineVersion = body.pipeline_version ?? 'v2';

  // Resolve the pipeline script path
  // v2 is the default (includes ML integration), v1 is legacy
  const scriptName = pipelineVersion === 'v1'
    ? 'silver-refresh-pipeline.ts'
    : 'silver-refresh-pipeline-v2.ts';

  const candidates = [
    path.join(process.cwd(), 'scripts', scriptName),
    path.join(process.cwd(), '..', '..', 'scripts', scriptName),
    `/mnt/ssd/1688-intel/scripts/${scriptName}`,
  ];

  const scriptPath = candidates.find(p => existsSync(p));
  if (!scriptPath) {
    return NextResponse.json(
      {
        ok: false,
        error: `Pipeline script not found: ${scriptName}`,
        checked: candidates,
      },
      { status: 500 },
    );
  }

  // Build command args
  const args = ['tsx', scriptPath];
  if (dryRun) args.push('--dry-run');
  if (step) args.push('--step', String(step));
  if (noGold) args.push('--no-gold');
  if (noMl) args.push('--no-ml');
  args.push('--timeout', String(timeout));

  return new Promise<NextResponse>((resolve) => {
    const child = spawn('npx', args, {
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
      // Extract JSON result if present
      const jsonMarker = '__PIPELINE_RESULT__';
      const markerIdx = stdout.indexOf(jsonMarker);
      let result = null;
      let logs = stdout;

      if (markerIdx !== -1) {
        const jsonStr = stdout.slice(markerIdx + jsonMarker.length).trim();
        try {
          result = JSON.parse(jsonStr);
        } catch {
          // JSON parse failed, return raw
        }
        logs = stdout.slice(0, markerIdx).trim();
      }

      if (code === 0 || code === 1) {
        // Pipeline completed (exit 1 = step errors, still valid response)
        resolve(
          NextResponse.json(
            {
              ok: result?.success ?? code === 0,
              result,
              logs: logs.slice(-2000), // last 2KB of logs
            },
            { status: 200 },
          ),
        );
      } else {
        resolve(
          NextResponse.json(
            {
              ok: false,
              error: `Pipeline exited with code ${code}`,
              logs: logs.slice(-2000),
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
            error: `Failed to start pipeline: ${err.message}`,
          },
          { status: 500 },
        ),
      );
    });
  });
}

export async function GET() {
  return NextResponse.json({
    endpoint: '/api/pipeline/silver-refresh',
    method: 'POST',
    auth: 'X-API-Key header required',
    body: {
      dry_run: 'boolean (optional) — run without modifying data',
      step: 'number (optional) — v1: 1=sync, 2=gold-views | v2: 1=sync, 2=velocity, 3=matching, 4=opportunity, 5=gold-views',
      no_gold: 'boolean (optional) — skip gold view refresh',
      no_ml: 'boolean (optional) — skip ML integration steps (v2 only)',
      pipeline_version: 'string (optional) — "v1" or "v2" (default: v2, includes ML integration)',
      timeout: 'number (optional) — max seconds per step (default: 300)',
    },
  });
}
