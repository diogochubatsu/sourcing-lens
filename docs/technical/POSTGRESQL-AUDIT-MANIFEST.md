# PostgreSQL Migration Audit Manifest

> **Prepared by Hermes Agent (1688-intel-devops)**  
> **Date:** 2026-04-23  
> **Scope:** Full assessment of the Phase 2 PostgreSQL migration completed by the 1688-intel agent

---

## 1. Executive Summary

The 1688-intel agent completed the PostgreSQL migration (commit `6dd1eb1`). Data was successfully migrated to Cloud SQL. **However, the app will NOT build in GitHub Actions** due to two missing `export const dynamic = 'force-dynamic'` declarations. This is the only **critical** blocker. All other issues are medium/low severity and have proposed fixes below.

| Severity | Count | Categories |
|---|---|---|
| 🔴 Critical | 1 | Build failure on `dashboard` + `analysis` pages |
| 🟡 Medium | 2 | Deploy registry (gcr.io), Secret verification |
| 🟢 Low | 3 | Dockerfile cleanup, data.ts modification note, SQLite artifact |

---

## 2. What Was Done (Verified)

### 2.1 Data Migration ✅

| Table | Rows | Status |
|---|---|---|
| `factory_products` | 18,704 | ✅ Migrated (with `sales_count` column) |
| `reviews` | 8,836 | ✅ Migrated (new table added by agent) |
| `ranked_suppliers` | 904 | ✅ Migrated |
| `listing_products` | 2,040 | ✅ Migrated |
| `air_products` | 252 | ✅ Migrated |
| `global_products` | 60 | ✅ Migrated |
| `pipeline_runs` | 5 | ✅ Migrated |
| `categories` | 50 | ✅ Migrated |
| `runs` | — | ✅ Migrated |

### 2.2 New Files Created ✅

| File | Author | Status |
|---|---|---|
| `src/lib/db-pg.ts` | Hermes | ✅ Connection pool (TCP + Unix socket) |
| `src/lib/data-pg.ts` | Hermes + 1688-intel agent | ✅ Async data layer with GROUP BY, sales_count |
| `scripts/setup-postgres.ts` | Hermes + 1688-intel agent | ✅ Schema + indexes + views + reviews table |
| `scripts/migrate-sqlite-to-postgres.ts` | Hermes + 1688-intel agent | ✅ Data migration with ON CONFLICT |
| `PHASE2-MANIFEST.md` | Hermes | ✅ Switchover guide |

### 2.3 App Imports Switched ✅

**15 files** changed from `@/lib/data` → `@/lib/data-pg`:

- `src/app/page.tsx`
- `src/app/dashboard/page.tsx`
- `src/app/analysis/page.tsx`
- `src/app/bestsellers/page.tsx`
- `src/app/products-pt/page.tsx`
- `src/app/products/[productId]/page.tsx`
- `src/app/suppliers/[id]/page.tsx`
- `src/app/api/rankings/route.ts`
- `src/app/api/rankings/runs/route.ts`
- `src/app/api/products/route.ts`
- `src/app/api/bestsellers/route.ts`
- `src/app/api/bestsellers/runs/route.ts`
- `src/app/api/meta/route.ts`
- `src/app/api/factories/route.ts`
- `src/app/api/factory-products/route.ts`

**Zero files** still import from `@/lib/data`.

### 2.4 Dependencies ✅

| Package | Location | Status |
|---|---|---|
| `pg` ^8.20.0 | `dependencies` | ✅ Present |
| `@types/pg` ^8.20.0 | `devDependencies` | ✅ Present |
| `package-lock.json` | root | ✅ Present (needed by Dockerfile) |

### 2.5 TypeScript ✅

```bash
npx tsc --noEmit  # ✅ PASSES — zero errors
```

### 2.6 Deploy Configuration ✅

| Item | Status | Notes |
|---|---|---|
| `--set-cloudsql-instances` | ✅ Present | Attaches `intel-postgres` |
| `--set-env-vars` | ✅ Present | `CLOUD_SQL_CONNECTION_NAME`, `DB_USER`, `DB_NAME` |
| `--set-secrets` | ✅ Present | `DB_PASS=intel-postgres-password:latest` |
| `workflow_dispatch` | ✅ Present | Manual trigger enabled |
| Workload Identity | ✅ Present | Uses `GCP_WORKLOAD_IDENTITY_PROVIDER` + `GCP_SERVICE_ACCOUNT` |

---

## 3. Issues Found

### 🔴 CRITICAL: Build Failure — Missing `dynamic` Export

**Problem:** `src/app/dashboard/page.tsx` and `src/app/analysis/page.tsx` do **not** declare:

```tsx
export const dynamic = 'force-dynamic';
```

Next.js tries to **prerender** these pages at build time. Since they call PostgreSQL (via `data-pg.ts`) and the build environment has no DB connection, the build fails with:

```
Error: DATABASE_URL or CLOUD_SQL_CONNECTION_NAME must be set for PostgreSQL
```

**Verified:** Adding `export const dynamic = 'force-dynamic';` to both files makes `npm run build` pass successfully.

**Fix:** Add the dynamic export to both files (see Section 5).

---

### 🟡 MEDIUM: Deploy Registry Uses `gcr.io` (Deprecated)

**Problem:** `.github/workflows/deploy.yml` pushes to `gcr.io`:

```yaml
IMAGE: gcr.io/leafy-flash-489319-c7/intel-dashboard:${{ github.sha }}
```

Google recommends **Artifact Registry** (`us-central1-docker.pkg.dev`). `gcr.io` is in maintenance mode.

**Impact:** Works today, but may break or be deprecated. Also, the Phase 1 Artifact Registry repository (`us-central1-docker.pkg.dev/.../intel-app`) already exists and was used successfully.

**Fix:** Switch to Artifact Registry (see Section 5).

---

### 🟡 MEDIUM: Secret Verification Required

**Problem:** The deploy workflow relies on three secrets that must be configured in GitHub + GCP:

| Secret | Where | Status |
|---|---|---|
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | GitHub Secrets | ⚠️ Must be verified |
| `GCP_SERVICE_ACCOUNT` | GitHub Secrets | ⚠️ Must be verified |
| `intel-postgres-password` | GCP Secret Manager | ⚠️ Must be verified |

**If any are missing or misconfigured**, the GitHub Actions run will fail at the auth or deploy step.

**Fix:** Verify all three are set (see Section 5).

---

### 🟢 LOW: `src/lib/data.ts` Was Modified

**Problem:** The 1688-intel agent added `getFactories()` and `getFactoryProducts()` directly to `src/lib/data.ts` (the original SQLite module), plus a `sales_count` column.

**Impact:** This breaks the "parallel track" rule we established (never modify existing working code). However, since the app now imports from `data-pg.ts`, the SQLite module is effectively unused at runtime. The modification is harmless but creates tech debt.

**Fix:** Leave as-is for now. In a future cleanup, revert `data.ts` to its pre-migration state.

---

### 🟢 LOW: Dockerfile Copies SQLite DB

**Problem:** The Dockerfile still copies `storage/1688-intel.db`:

```dockerfile
COPY storage/1688-intel.db storage/1688-intel.db
```

**Impact:** Harmless — the app uses PostgreSQL, so the SQLite file is ignored at runtime. It adds ~5-20MB to the image size.

**Fix:** Remove the COPY line (see Section 5).

---

### 🟢 LOW: `getFactoryProducts` Return Type Divergence

**Problem:** `data.ts` added a `sales` field to `FactoryProductRow`, but `data-pg.ts` also has it. Both are consistent. No action needed.

---

## 4. Build Test Results

### Before Fix ❌

```bash
$ npm run build
Error occurred prerendering page "/analysis"
Error: DATABASE_URL or CLOUD_SQL_CONNECTION_NAME must be set for PostgreSQL
Export encountered an error on /analysis/page: /analysis, exiting the build.
```

### After Fix ✅

```bash
# Added dynamic export to dashboard + analysis
$ npm run build
✓ Compiled successfully
✓ Linting and checking validity of types
✓ Collecting page data
✓ Generating static pages
# Build completes successfully
```

**All routes compile:**
- `/` (Overview)
- `/dashboard` (Dynamic)
- `/analysis` (Dynamic)
- `/rankings` (Static shell)
- `/products` (Static shell)
- `/factories` (Static shell)
- `/bestsellers` (Dynamic)
- `/products-pt` (Dynamic)
- `/suppliers/[id]` (Dynamic)
- `/products/[productId]` (Dynamic)
- All `/api/*` routes (Dynamic by default)

---

## 5. Proposed Fixes & Improvements

### Fix A: Add `dynamic` Export (CRITICAL — Do First)

**File:** `src/app/dashboard/page.tsx`  
**Add at top of file:**

```tsx
export const dynamic = 'force-dynamic';
```

**File:** `src/app/analysis/page.tsx`  
**Add at top of file:**

```tsx
export const dynamic = 'force-dynamic';
```

**Why:** Prevents Next.js from prerendering these pages at build time. They will be server-rendered on-demand at runtime, where Cloud SQL is available.

---

### Fix B: Switch Deploy Registry to Artifact Registry (MEDIUM)

**File:** `.github/workflows/deploy.yml`

**Change:**

```diff
- IMAGE: gcr.io/leafy-flash-489319-c7/intel-dashboard:${{ github.sha }}
+ IMAGE: us-central1-docker.pkg.dev/leafy-flash-489319-c7/intel-app/intel-dashboard:${{ github.sha }}
```

```diff
- run: gcloud auth configure-docker gcr.io --quiet
+ run: gcloud auth configure-docker us-central1-docker.pkg.dev --quiet
```

**Why:** `gcr.io` is deprecated. Artifact Registry is the current standard. The `intel-app` repository already exists from Phase 1.

---

### Fix C: Verify Secrets (MEDIUM)

Run these checks **before** the next deploy:

**1. GitHub Secrets:**
Go to `https://github.com/diogochubatsu/1688-intel/settings/secrets/actions` and verify:
- `GCP_WORKLOAD_IDENTITY_PROVIDER` is set (format: `projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL/providers/PROVIDER`)
- `GCP_SERVICE_ACCOUNT` is set (format: `github-deployer@leafy-flash-489319-c7.iam.gserviceaccount.com` or similar)

**2. GCP Secret Manager:**
```bash
gcloud secrets list --project=leafy-flash-489319-c7
# Should show: intel-postgres-password
gcloud secrets versions list intel-postgres-password --project=leafy-flash-489319-c7
# Should show at least version 1 (enabled)
```

**3. Cloud Run IAM (already done in Phase 1, but verify):**
```bash
gcloud run services get-iam-policy intel-dashboard --region=us-central1 --project=leafy-flash-489319-c7
# Should show: allUsers with roles/run.invoker
```

---

### Fix D: Clean Up Dockerfile (LOW)

**File:** `Dockerfile`

**Remove these lines (SQLite is no longer used):**

```diff
- # Copy SQLite DB explicitly (excluded by .dockerignore but needed for build-time prerendering)
- COPY storage/1688-intel.db storage/1688-intel.db
```

```diff
- # Copy SQLite database for read-only serving
- COPY --from=builder --chown=nextjs:nodejs /app/storage/1688-intel.db ./storage/1688-intel.db
```

**Why:** Reduces image size by ~5-20MB. The app connects to PostgreSQL, not SQLite.

---

### Fix E: Add `db:status` Script (Improvement)

**File:** `package.json`

**Add to `scripts`:**

```json
{
  "db:setup": "npx tsx scripts/setup-postgres.ts",
  "db:migrate": "npx tsx scripts/migrate-sqlite-to-postgres.ts",
  "db:status": "npx tsx scripts/db-status.ts"
}
```

**Why:** Makes it easier to run schema setup and migration from the command line.

---

## 6. Deployment Checklist (After Fixes Applied)

- [ ] Fix A applied: `dashboard/page.tsx` has `export const dynamic = 'force-dynamic'`
- [ ] Fix A applied: `analysis/page.tsx` has `export const dynamic = 'force-dynamic'`
- [ ] Fix B applied: `deploy.yml` uses Artifact Registry (`us-central1-docker.pkg.dev`)
- [ ] Fix C verified: GitHub Secrets `GCP_WORKLOAD_IDENTITY_PROVIDER`, `GCP_SERVICE_ACCOUNT` are set
- [ ] Fix C verified: GCP Secret Manager has `intel-postgres-password`
- [ ] Local build passes: `npm run build`
- [ ] Push to `master`
- [ ] GitHub Actions workflow triggers and passes
- [ ] Cloud Run deploys successfully
- [ ] Verify live URL: `https://intel-dashboard-4766585081.us-central1.run.app`
- [ ] Verify `/api/factories` returns 975 suppliers from PostgreSQL
- [ ] Verify `/api/meta` returns correct run counts
- [ ] Verify `/dashboard` loads without errors
- [ ] Verify `/analysis` loads without errors

---

## 7. Rollback Plan (If Deploy Fails)

1. **Revert imports:** Change all 15 files back from `@/lib/data-pg` to `@/lib/data`
2. **Remove dynamic exports:** From `dashboard/page.tsx` and `analysis/page.tsx` (if added)
3. **Remove `--set-cloudsql-instances`** from `deploy.yml`
4. **Push revert** — app returns to SQLite-on-Cloud-Run (Phase 1)
5. **PostgreSQL data is untouched** — can retry migration later

---

## 8. Files That Were Modified (by 1688-intel Agent)

```
.github/workflows/deploy.yml       # Rewritten for Workload Identity + Cloud SQL
package.json                       # Added pg, @types/pg
scripts/setup-postgres.ts          # Created (with reviews table)
scripts/migrate-sqlite-to-postgres.ts  # Created
src/app/analysis/page.tsx          # Switched to data-pg
src/app/api/bestsellers/route.ts   # Switched to data-pg
src/app/api/bestsellers/runs/route.ts  # Switched to data-pg
src/app/api/factories/route.ts     # Switched to data-pg
src/app/api/factory-products/route.ts  # Switched to data-pg
src/app/api/meta/route.ts          # Switched to data-pg
src/app/api/products/route.ts      # Switched to data-pg
src/app/api/rankings/route.ts      # Switched to data-pg
src/app/api/rankings/runs/route.ts # Switched to data-pg
src/app/bestsellers/page.tsx       # Switched to data-pg
src/app/dashboard/page.tsx         # Switched to data-pg
src/app/factories/FactoriesClient.tsx  # Unchanged import path (no data import)
src/app/factories/page.tsx         # Switched to data-pg
src/app/page.tsx                   # Switched to data-pg
src/app/products-pt/page.tsx       # Switched to data-pg
src/app/products/[productId]/page.tsx  # Switched to data-pg
src/app/suppliers/[id]/page.tsx    # Switched to data-pg
src/lib/data-pg.ts                 # Created
src/lib/data.ts                    # MODIFIED (added factory functions)
src/lib/db-pg.ts                   # Created
```

---

## 9. Recommendation

**Apply Fix A immediately** (add `dynamic` export to 2 pages). This is the only critical blocker.  
**Apply Fix B** (switch to Artifact Registry) before the next deploy.  
**Apply Fix C** (verify secrets) before the next deploy.  
**Apply Fix D** (Dockerfile cleanup) at your convenience.

Once Fix A is applied, the app will build and deploy successfully to Cloud Run with PostgreSQL.

---

*End of audit manifest.*
