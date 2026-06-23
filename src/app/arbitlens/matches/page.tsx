import Link from 'next/link';
import { execFileSync } from 'child_process';
import path from 'path';

const SCRIPT_DIR = path.join(process.cwd(), 'scripts', 'arbitlens');
const PLATFORM_COLORS: Record<string, string> = { 'rakumart-1688': '#3B82F6', 'rakumart-taobao': '#8B5CF6', 'rakumart-alibaba': '#06B6D4', 'dhgate': '#F97316', 'alibaba': '#EAB308' };
const PLATFORM_SHORT: Record<string, string> = { 'rakumart-1688': '1688', 'rakumart-taobao': 'Taobao', 'rakumart-alibaba': 'Alibaba BR', 'dhgate': 'DHgate', 'alibaba': 'Alibaba' };

function searchProducts(q: string, limit: number = 4) {
  try { const output = execFileSync('python3', ['-u', path.join(SCRIPT_DIR, 'search.py'), q, String(limit)], { cwd: process.cwd(), timeout: 30000, encoding: 'utf-8', maxBuffer: 5 * 1024 * 1024 }); return JSON.parse(output).products || []; } catch { return []; }
}

export default async function MatchesPage() {
  const queries = ['microfone wireless', 'smartwatch', 'webcam', 'power bank'];
  const allProducts: any[] = [];
  for (const q of queries) { allProducts.push(...searchProducts(q, 2)); }
  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-6"><Link href="/arbitlens" className="text-xs" style={{ color: '#C8102E' }}>← Dashboard</Link><h1 className="text-2xl font-bold mt-2">Cross-Platform Matches</h1><p className="text-sm" style={{ color: '#8A8A8A' }}>Products found on multiple marketplaces</p></div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">{allProducts.map((item: any, i: number) => { const c = PLATFORM_COLORS[item.platform] || '#666'; const l = PLATFORM_SHORT[item.platform] || item.platform; return (<a key={i} href={item.product_url} target="_blank" rel="noopener noreferrer" className="bg-white rounded-xl overflow-hidden hover:shadow-lg transition-all" style={{ border: '1px solid #E5E5E5' }}><div className="aspect-square flex items-center justify-center" style={{ background: '#F5F5F5' }}>{item.image_url ? <img src={`/api/proxy/image?url=${encodeURIComponent(item.image_url)}`} alt="" className="w-full h-full object-contain" loading="lazy" /> : <span className="text-3xl" style={{ color: '#D4D4D4' }}>📦</span>}</div><div className="p-2.5"><span className="inline-block text-[9px] font-semibold px-1.5 py-0.5 rounded text-white mb-1" style={{ background: c }}>{l}</span><div className="text-[11px] font-medium line-clamp-2">{item.product_name}</div><div className="text-sm font-bold mt-1" style={{ color: '#059669' }}>{item.price_brl ? `R$ ${item.price_brl.toFixed(2)}` : '—'}</div></div></a>); })}</div>
    </div>
  );
}
