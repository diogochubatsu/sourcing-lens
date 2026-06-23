---
name: 1688-intel-frontend
description: Frontend and dashboard development patterns for the 1688-intel Next.js app. Covers data visualization, filtering, categorization, insights generation, and the stone/amber design system.
version: 1.0.1
category: software-development
metadata:
  hermes:
    tags: [1688, nextjs, dashboard, data-viz, frontend]
---

# 1688-Intel Frontend Skill

Specialized patterns for building dashboards and data pages in the 1688-intel Next.js application.

## Project Context

- **Codebase:** `/mnt/ssd/1688-intel`
- **Stack:** Next.js 15 App Router, TypeScript, TailwindCSS, PostgreSQL
- **Data Layer:** `src/lib/data-pg.ts` exports all query functions
- **No chart libraries** — pure CSS bar charts and tables only

## Design System

### Color Palette
- Background: `bg-stone-50`
- Cards: `bg-white rounded-2xl border border-stone-200 shadow-sm`
- Primary text: `text-ink` (custom, ~stone-900)
- Accent charts: `bg-amber-500`, `bg-emerald-500`, `bg-indigo-500`
- Badges: emerald (≥70%), amber (≥40%), red (<40%)

### Typography
- Section headers: `text-sm font-semibold uppercase tracking-widest text-stone-400`
- KPI values: `text-2xl font-bold text-ink` (or `text-3xl` for hero metrics)
- Table text: `text-sm`

### Reusable Components

**StatCard:**
```tsx
function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="bg-white rounded-2xl border border-stone-200 px-5 py-4">
      <div className="text-xs font-semibold uppercase tracking-widest text-stone-400 mb-1">{label}</div>
      <div className="text-3xl font-bold text-ink">{value}</div>
      {sub && <div className="text-xs text-stone-400 mt-1">{sub}</div>}
    </div>
  );
}
```

**CSS BarChart:**
```tsx
function BarChart({ data, maxValue, color }: {
  data: { label: string; value: number }[];
  maxValue: number;
  color: string; // e.g. "bg-amber-500"
}) {
  return (
    <div className="flex flex-col gap-2">
      {data.map(({ label, value }) => (
        <div key={label} className="flex items-center gap-3 text-sm">
          <span className="w-36 truncate text-stone-600 text-right">{label}</span>
          <div className="flex-1 bg-stone-100 rounded-full h-5 overflow-hidden">
            <div className={`h-full ${color} rounded-full transition-all duration-500`} style={{ width: `${Math.round((value / maxValue) * 100)}%` }} />
          </div>
          <span className="w-20 text-stone-800 font-medium">{value}</span>
        </div>
      ))}
    </div>
  );
}
```

**SectionCard:**
```tsx
import type { ReactNode } from 'react';
export function SectionCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm">
      <h2 className="mb-4 text-lg font-semibold text-ink">{title}</h2>
      {children}
    </section>
  );
}
```

**RepurchaseBadge:**
```tsx
export function RepurchaseBadge({ value }: { value: number | null }) {
  if (value == null) return <span className="text-stone-400">—</span>;
  const color = value >= 70 ? 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200'
    : value >= 40 ? 'bg-amber-50 text-amber-700 ring-1 ring-amber-200'
    : 'bg-red-50 text-red-700 ring-1 ring-red-200';
  return <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold tabular-nums ${color}`}>{value}%</span>;
}
```

## Data Patterns

### Sales Parsing (Chinese format)
```ts
function parseSales(s: string | null): number {
  if (!s) return 0;
  const m = s.match(/([\d.]+)\s*万/);
  if (m) return parseFloat(m[1]) * 10000;
  return 0;
}
```

### Ranking Type Normalization
```ts
const TYPE_MAP: Record<string, string> = {
  '回购榜': 'Repurchase',
  '热销榜': 'Best Sellers',
  '好评榜': 'Top Rated',
  '新品榜': 'New Arrivals',
  '实力榜': 'Top Performers',
};
```

### Portuguese Title Sanitization
```ts
function sanitizePt(s: string | null): string {
  if (!s) return '';
  return s.replace(/[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+/g, '').replace(/\s{2,}/g, ' ').trim();
}
```

## Page Architecture

### Server Component (Static Data + Charts)
Use when the page needs async data but no user interaction.
```tsx
export const dynamic = 'force-dynamic';
export default async function Page() {
  const rankings = await getRankings();
  // compute aggregations inline
  return <div>...</div>;
}
```

### Client Component (Filters + URL Sync)
Use when filters, sorting, or pagination are needed.
```tsx
'use client';
import { useRouter, useSearchParams } from 'next/navigation';
import { useTransition } from 'react';
```
Use `FilterForm` and `FilterChips` from `@/components/FilterUI` for URL-synced filters.

## Data Layer Functions

Import from `@/lib/data-pg`:
- `getRankings()` — ranked suppliers
- `getProductRows()` — enriched products
- `getBestsellers(run?)` — bestseller products
- `getFactories()` — factory directory
- `getFactoryProducts()` — factory product catalog
- `listRankingRuns()` / `listBestsellerRuns()` — available data runs
- `listRankingCategories()` / `listRankingRegions()` — filter options
- `getSupplierProfile(id)` / `getSupplierProfiles()` — supplier detail
- `getProductProfile(id)` — product detail
- `getMeta()` — counts and coverage

## Core Patterns

### Numeric Aggregation Safeguards (avgPrice Pattern)
When performing sum/average on values from PostgreSQL that might be stored as strings:
```ts
const validPrices = rows.filter(r => {
  const p = Number(r.price);
  return Number.isFinite(p) && p > 0;
});
const avgPrice = validPrices.length ? validPrices.reduce((sum, r) => sum + Number(r.price), 0) / validPrices.length : 0;
```
This prevents string concatenation (`"10" + "5" → "105"`) and NaN propagation from non-numeric strings.

### SearchableMultiSelect (Large Filter Option Pattern)
For datasets with 50+ options, replace ToggleSet with a custom searchable dropdown:
- Type-ahead filtering using `label_pt` (preferred) or `label_cn`
- Count badges on each option: `${label} (${count})`
- Checkboxes for multi-select with URL sync via comma-separated query params
- "Clear all" and "Select all" buttons
- Reusable across pages: `SearchableMultiSelect` component accepts `{label, label_pt, count}[]`, `value: string[]`, `onChange: (string[]) => void`, and `searchPlaceholder`
- If options exceed viewport, use `max-h-64 overflow-y-auto` styling

### Dynamic Price Bins from Server Quartiles
Server exposes:
```ts
priceQuartiles: { q1: number, median: number, q3: number, max: number }
```
Client constructs bins:
```ts
const bins = [
  { label: `Under ¥${formatK(stats.priceQuartiles.q1)}`, min: 0, max: stats.priceQuartiles.q1 },
  { label: `¥${formatK(stats.priceQuartiles.q1)}–¥${formatK(stats.priceQuartiles.median)}`, min: stats.priceQuartiles.q1, max: stats.priceQuartiles.median },
  { label: `¥${formatK(stats.priceQuartiles.median)}–¥${formatK(stats.priceQuartiles.q3)}`, min: stats.priceQuartiles.median, max: stats.priceQuartiles.q3 },
  { label: `Over ¥${formatK(stats.priceQuartiles.q3)}`, min: stats.priceQuartiles.q3, max: Infinity },
];
```
Use `formatK(n)` → `n >= 10000 ? `${(n/1000).toFixed(0)}k` : n.toFixed(0)` for readable labels. Bin selection auto-clears when `stats` changes.

### InsightsPanel Pattern
Compute one-line summary from already-fetched data:
- Total filtered count (`filtered.length`)
- Average price (reuse avgPrice calculation)
- Top category: `groupBy(filtered, 'category_label_pt')` → max count
Display: `"Showing X of Y products | Avg price: ¥Z | Top category: Z (N products)"`
Place above data table for immediate context.

### Tooltip Convention
For column value explanations, add `title="Tooltip text"` directly to the `<td>` element if the entire cell needs the hint. For badge-specific hints, wrap the badge in a `<span title="">`.

### useMemo Scope and Dependency Propagation
When refactoring filter logic across multiple useMemo blocks:
- Variables referenced inside a useMemo must be in lexical scope (defined earlier) OR included in its dependency array
- If you extract a filtering step into its own useMemo that references another derived value (e.g., `priceBins`, `catMap`), either hoist that value before the consuming useMemo or inline it back
- Always add newly introduced derived mappings (like `catMap` built from `categoriesFull`) to ALL downstream useMemo dependency arrays (`filtered`, `insights`, etc.) so computed values stay in sync

Common error: "Cannot find name X" → X is defined in a later useMemo or isn't in scope. Fix by reordering definitions or lifting state up.

## Rules

1. **No external chart libraries.** Use CSS bar charts only.
2. **Repurchase rate is 0-100 int.** Do not multiply by 100.
3. **Server components for data, client for interactivity.**
4. **Reuse existing components.** Do not reinvent StatCard, SectionCard, FilterUI.
5. **Style consistency.** Stick to stone/amber theme. No new palettes.
6. **Responsive.** Use `grid-cols-1 lg:grid-cols-2` for side-by-side charts.
7. **Add nav links.** Update `src/app/layout.tsx` when adding pages.
8. **Progressive data exploration** — When developing API endpoints, expose raw data with `--limit N` queries first. Validate transformations on a sample before full rollout.

## Content Pages & Dossier Viewer

### When to Use
When building documentation, report, or dossier pages that render markdown content without external libraries like `react-markdown` or `mdx`. Typical for static content that lives alongside the app but outside the `src/` tree.

### Custom Markdown Parser (Regex-based)
Implement a lightweight parser function that processes markdown line-by-line and returns JSX. Supports: headings (H2 only for TOC), paragraphs, bold/italic, unordered lists, code blocks (fenced and indented), tables, horizontal rules, and callout/admonition blocks.

```tsx
function parseMarkdown(content: string): React.ReactNode[] {
  const lines = content.split('\n')
  const result: React.ReactNode[] = []
  let inCodeBlock = false
  let codeContent: string[] = []
  let inTable = false
  let tableRows: string[][] = []

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]

    // Code blocks (fenced)
    if (line.startsWith('```')) {
      if (!inCodeBlock) {
        inCodeBlock = true
        codeContent = []
        continue
      } else {
        inCodeBlock = false
        result.push(<pre key={result.length} className="bg-stone-900 text-stone-100 p-4 rounded-xl overflow-x-auto text-sm"><code>{codeContent.join('\n')}</code></pre>)
        continue
      }
    }
    if (inCodeBlock) {
      codeContent.push(line)
      continue
    }

    // Headings (H2 only for TOC)
    const h2Match = line.match(/^##\s+(.+)$/)
    if (h2Match) {
      const slug = h2Match[1].toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '')
      result.push(<h2 key={result.length} id={slug} className="text-2xl font-bold text-stone-900 mt-8 mb-4">{h2Match[1]}</h2>)
      continue
    }

    // Horizontal rule
    if (/^-{3,}$/.test(line.trim())) {
      result.push(<hr key={result.length} className="my-6 border-stone-200" />)
      continue
    }

    // Callout/admonition (note, warning, tip)
    const calloutMatch = line.match(/^:::+(caution|note|tip)\s*$/i)
    if (calloutMatch) {
      const type = calloutMatch[1].toLowerCase()
      const icon = type === 'tip' ? '💡' : type === 'warning' ? '⚠️' : '📝'
      const className = type === 'tip' ? 'bg-amber-50 border-amber-200' : type === 'warning' ? 'bg-red-50 border-red-200' : 'bg-stone-50 border-stone-200'
      result.push(
        <div key={result.length} className={`my-4 p-4 rounded-xl border ${className}`}>
          <div className="font-semibold mb-1">{icon} {type.charAt(0).toUpperCase() + type.slice(1)}</div>
        </div>
      )
      continue
    }

    // Tables
    const sepMatch = line.match(/^\|?(?:\s*[-:]+\s*\|)+\s*[-:]+(?:\s*\|)?$/)
    if (sepMatch) {
      inTable = true
      tableRows = []
      continue
    }
    if (inTable && line.startsWith('|')) {
      const cells = line.split('|').filter(c => c.trim()).map(c => c.trim().replace(/`/g, ''))
      tableRows.push(cells)
      continue
    }
    if (inTable && !line.startsWith('|')) {
      inTable = false
      result.push(
        <div key={result.length} className="overflow-x-auto my-4">
          <table className="w-full text-sm border-collapse border border-stone-200">
            <thead>
              <tr className="bg-stone-50">
                {tableRows[0]?.map((h, j) => <th key={j} className="border border-stone-200 px-3 py-2 text-left font-semibold text-stone-700">{h}</th>)}
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-100">
              {tableRows.slice(1).map((row, ri) => (
                <tr key={ri} className="hover:bg-stone-50/50">
                  {row.map((cell, ci) => <td key={ci} className="border border-stone-200 px-3 py-2 text-stone-600">{cell}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )
    }

    // Paragraphs + inline formatting
    if (line.trim() === '') continue

    let node: React.ReactNode = line
    // Bold
    node = (node as string).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // Italic
    node = (node as string).replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Code inline
    node = (node as string).replace(/`(.+?)`/g, '<code className="bg-stone-100 text-rose-600 px-1.5 py-0.5 rounded text-xs font-mono">$1</code>')

    result.push(<p key={result.length} className="mb-3 text-stone-700 leading-relaxed" dangerouslySetInnerHTML={{ __html: node as string }} />)
  }

  return result
}
```

### Table of Contents Generator
Extract H2 headings, generate URL-safe slugs, render as a floating sidebar or sticky element.

```tsx
function extractHeadings(content: string): Array<{ title: string; slug: string }> {
  return content
    .split('\n')
    .filter(line => line.startsWith('## '))
    .map(line => {
      const title = line.replace(/^##\s+/, '').trim()
      const slug = title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '')
      return { title, slug }
    })
}
```

Render TOC with collapsible desktop/vertical layout:
```tsx
<aside className="hidden xl:block sticky top-24 w-64 shrink-0">
  <div className="rounded-xl border border-stone-200 bg-stone-50 p-4 text-sm">
    <h3 className="font-semibold text-stone-900 mb-2">Contents</h3>
    <nav className="space-y-1">
      {headings.map(h => (
        <a key={h.slug} href={`#${h.slug}`} className="block text-stone-600 hover:text-stone-900 hover:bg-stone-100 px-2 py-1 rounded transition-colors">
          {h.title}
        </a>
      ))}
    </nav>
  </div>
</aside>
```

### External Content via Symlink (Local Development)
Place content outside the Next.js `src/` tree (e.g., `~/1688-intel/dossiers/`), then create a symlink within the project:

```bash
ln -s /home/chubatsu/1688-intel/dossiers /mnt/ssd/1688-intel/dossiers
```

Read the file in a Next.js server component:

```tsx
import { readFile } from 'fs/promises'
import path from 'path'

const DOSSIERS_DIR = path.join(process.cwd(), 'dossiers')

async function getDossier(slug: string): Promise<string> {
  const file = await readFile(path.join(DOSSIERS_DIR, `${slug}.md`), 'utf-8')
  return file
}

export default async function DossierPage({ params }: { params: { slug: string } }) {
  const markdown = await getDossier(params.slug)
  const html = parseMarkdown(markdown)
  const headings = extractHeadings(markdown)
  // ...
}
```

**⚠️ Production note (Cloud Run / containers):** Symlinks to host paths outside the project directory are **not followed** in deployed containers. The `fs.readFile()` call will fail at runtime with ENOENT when deployed to Cloud Run, Vercel Functions, or similar containerized runtimes. The build artifact only includes files inside the project tree.

**Solution — embed content at build time:** Read the markdown file during local development (or CI), escape it for TypeScript template literals, and embed it directly in the page as a constant:

```tsx
// 1. Pre-process the markdown file (script or manual) and escape: backslashes and backticks
const DOSSIER_MARKDOWN = `# Title\n\nContent with \\`code\\` here...`

// 2. Parse at render time (no filesystem access needed)
function parseMarkdown(text: string): string { /* ... */ }

export default async function DossierPage() {
  const html = parseMarkdown(DOSSIER_MARKDOWN)
  const toc = extractHeadings(DOSSIER_MARKDOWN)
  // render...
}
```

Escaping rules for template literals:
- `\` → `\\`
- `` ` `` → `\``
- `${` → `\${` (if your markdown contains literal `${` sequences)

This makes the page completely self-contained and portable across all deployment targets without special filesystem configuration.

### Report Index Dashboard
A landing page that lists available reports using card components with metadata. Each card displays title, description, badge, and key-value metadata. Use a two-column grid layout.

### TypeScript Duplicate Export Error Pattern
When editing Next.js App Router pages, avoid leaving multiple `export default async function` declarations in the same file. The TypeScript parser will report `TS1128: Declaration or statement expected` at the closing brace of the first or the start of the second.

**Detection:** Search for duplicate `export default async function` or `export function` definitions in the file.

**Fix:** Remove the obsolete duplicate entirely, keeping only the intended implementation. Preserve any state variables or helper functions that belong to the active component. Use `grep -n 'export default' <file>` to locate all occurrences.

### Navigation Updates
When adding a new top-level page under `src/app/`, update the global navigation in `src/app/layout.tsx`:

```tsx
const navItems = [
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/analysis', label: 'Analysis' },
  { href: '/rankings', label: 'Rankings' },
  { href: '/products', label: 'Products' },
  { href: '/reports', label: 'Reports' }, // ← add new entry
  { href: '/docs', label: 'Docs' },
]
```
