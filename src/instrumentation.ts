/**
 * Next.js instrumentation hook — runs once on server startup.
 * Simplified for V2: no DB dependency needed.
 */
export async function register() {
  // V2: No auth system yet — skip DB migrations.
  if (typeof window !== 'undefined') return;
  console.log('[instrumentation] V2 mode — DB migrations skipped');
}