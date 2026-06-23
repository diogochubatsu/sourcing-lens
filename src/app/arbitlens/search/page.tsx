import Link from 'next/link';
import { execFileSync } from 'child_process';
import path from 'path';

const SCRIPT_DIR = path.join(process.cwd(), 'scripts', 'arbitlens');
const PLATFORM_COLORS: Record<string, string> = { 'rakumart-1688': '#3B82F6', 'rakumart-taobao': '#8B5CF6', 'rakumart-alibaba': '#06B6D4', 'dhgate': '#F97316', 'alibaba': '#EAB308' };
const PLATFORM_SHORT: Record<string, string> = { 'rakumart-1688': '1688', 'rakumart-taobao': 'Taobao', 'rakumart-alibaba': 'Alibaba BR', 'dhgate': 'DHgate', 'alibaba': 'Alibaba' };

function searchProducts(q: string, limit: number = 24) {
  try { const output = execFileSync('python3', ['-u', path.join(SCRIPT_DIR, 'search.py'), q, String(limit)], { cwd: process.cwd(), timeout: 60000, encoding: 'utf-8', maxBuffer: 10 * 1024 * 1024 }); return JSON.parse(output).products || []; } catch { return []; }
}

export default async function SearchPage({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
  const sp = await searchParams;
  const q = sp.q || '';
  const products = q ? searchProducts(q, 24) : [];
  const platforms: string[] = []; products.forEach((p: any) => { if (!platforms.includes(p.platform)) platforms.push(p.platform); });
  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-6"><Link href="/arbitlens" className="text-xs" style={{ color: '#C8102E' }}>← Dashboard</Link><h1 className="text-2xl font-bold mt-2">{q ? `Results for "${q}"` : 'Search'}</h1><p className="text-sm" style={{ color: '#8A8A8A' }}>{products.length} products found across {platforms.length} platforms</p></div>
      <form className="flex gap-2 mb-6" action="/arbitlens/search" method="get"><input type="text" name="q" defaultValue={q} placeholder='Search products...' className="flex-1 px-4 py-3 text-sm bg-white rounded-xl focus:outline-none" style={{ border: '1px solid #E5E5E5' }} /><button type="submit" className="px-5 py-3 text-white text-sm font-semibold rounded-xl" style={{ background: '#0A0A0A' }}>Search</button></form>
      {platforms.length > 1 && <div className="flex gap-2 mb-6 flex-wrap">{platforms.map(p => <span key={p} className="px-3 py-1.5 text-xs font-semibold rounded-full text-white" style={{ background: PLATFORM_COLORS[p] || '#666' }}>{PLATFORM_SHORT[p] || p}</span>)}</div>}
      {products.length === 0 ? <div className="text-center py-16" style={{ color: '#8A8A8A' }}><p>No results</p></div> : <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">{products.map((item: any, i: number) => (<a key={i} href={item.product_url} target="_blank" rel="noopener noreferrer" className="bg-white rounded-xl overflow-hidden hover:shadow-lg transition-all" style={{ border: '1px solid #E5E5E5' }}><div className="aspect-square flex items-center justify-center" style={{ background: '#F5F5F5' }}>{item.image_url ? <img src={`/api/proxy/image?url=${encodeURIComponent(item.image_url)}`} alt="" className="w-full h-full object-contain" loading="lazy" /> : <span className="text-3xl" style={{ color: '#D4D4D4' }}>📦</span>}</div><div className="p-2.5"><span className="inline-block text-[9px] font-semibold px-1.5 py-0.5 rounded text-white mb-1" style={{ background: PLATFORM_COLORS[item.platform] || '#666' }}>{PLATFORM_SHORT[item.platform] || item.platform}</span><div className="text-[11px] font-medium line-clamp-2">{item.product_name}</div><div className="text-sm font-bold mt-1" style={{ color: '#059669' }}>{item.price_brl ? `R$ ${item.price_brl.toFixed(2)}` : '—'}</div></div></a>))}</div>}
    </div>
  );
}
