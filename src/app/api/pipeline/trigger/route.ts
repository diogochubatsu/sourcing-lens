import { spawn } from 'child_process';
import { existsSync, readFileSync } from 'fs';
import path from 'path';

import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';

import { requireApiKey } from '@/lib/auth';

const requestSchema = z.object({
  target: z.enum(['rankings', 'bestsellers']),
});

const repoRoot = () => path.resolve(process.cwd(), '..', '..');

const scriptByTarget = {
  rankings: '1688:rankings',
  bestsellers: '1688:bestsellers',
} as const;

function getPackageScripts(cwd: string): Record<string, string> | null {
  const packageJsonPath = path.join(cwd, 'package.json');
  if (!existsSync(packageJsonPath)) {
    return null;
  }

  try {
    const parsed = JSON.parse(readFileSync(packageJsonPath, 'utf8')) as { scripts?: Record<string, string> };
    return parsed.scripts ?? {};
  } catch {
    return null;
  }
}

function resolveRunner(script: string): { cwd: string; script: string; checked: string[] } | null {
  const checked = [repoRoot(), process.cwd()];

  for (const cwd of checked) {
    const scripts = getPackageScripts(cwd);
    if (scripts && scripts[script]) {
      return { cwd, script, checked };
    }
  }

  return null;
}

export async function POST(request: NextRequest) {
  const unauthorized = requireApiKey(request);
  if (unauthorized) {
    return unauthorized;
  }

  if (process.env.NODE_ENV === 'production') {
    return NextResponse.json(
      {
        error: 'Not implemented',
        message: 'Pipeline triggers are not available in production. Use the scheduled ingest workflow (.github/workflows/ingest-1688.yml).',
      },
      { status: 501 },
    );
  }

  const parsed = requestSchema.safeParse(await request.json().catch(() => null));
  if (!parsed.success) {
    return NextResponse.json({ error: 'Invalid payload', issues: parsed.error.issues }, { status: 400 });
  }

  const script = scriptByTarget[parsed.data.target];
  const runner = resolveRunner(script);

  if (!runner) {
    return NextResponse.json(
      {
        error: 'Pipeline runner unavailable',
        message: `Script '${script}' was not found in package.json scripts in checked directories.`,
        checkedDirectories: [repoRoot(), process.cwd()],
        expectedScripts: Object.values(scriptByTarget),
      },
      { status: 503 },
    );
  }

  const child = spawn('npm', ['run', runner.script], {
    cwd: runner.cwd,
    windowsHide: true,
    detached: true,
    stdio: 'ignore',
  });
  child.unref();

  return NextResponse.json({ ok: true, message: `Triggered ${runner.script}`, cwd: runner.cwd });
}