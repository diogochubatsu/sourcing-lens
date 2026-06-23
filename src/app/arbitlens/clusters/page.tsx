import Link from 'next/link';
import { execFileSync } from 'child_process';
import path from 'path';

const SCRIPT_DIR = path.join(process.cwd(), 'scripts', 'arbitlens');
const PLATFORM_COLORS: Record<string, string> = { 'rakumart-1688': '#3B82F6', 'rakumart-taobao': '#8B5CF6', 'rakumart-alibaba': '#06B6D4', 'dhgate': '#F97316', 'alibaba': '#EAB308' };
const PLATFORM_SHORT: Record<string, string> = { 'rakumart-1688': '1688', 'rakumart-taobao': 'Taobao', 'rakumart-alibaba': 'Alibaba BR', 'dhgate': 'DHgate', 'alibaba': 'Alibaba' };

function searchProducts(q: string, limit: number = 4) {
  try { const output = execFileSync('python3', ['-u', path.join(SCRIPT_DIR, 'search.py'), q, String(limit)], { cwd: process.cwd(), timeout: 30000, encoding: 'utf-8', maxBuffer: 5 * 1024 * 1024 }); return JSON.parse(output).products || []; } catch { return []; }
}

export default async function ClustersPage() {
  const clusterQueries = [{ name: 'Wireless Microphones', q: 'microfone wireless lapela' }, { name: 'Smartwatches', q: 'smartwatch pulseira' }, { name: 'Webcams', q: 'webcam camera 1080p' }, { name: 'Power Banks', q: 'power bank carregador' }];
  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-6"><Link href="/arbitlens" className="text-xs" style={{ color: '#C8102E' }}>← Dashboard</Link><h1 className="text-2xl font-bold mt-2">Product Clusters</h1><p className="text-sm" style={{ color: '#8A8A8A' }}>Same product across multiple marketplaces</p></div>
      <div className="space-y-6">{clusterQueries.map(cluster => { const products = searchProducts(cluster.q, 8); if (products.length === 0) return null; const prices = products.map((p: any) => p.price_brl).filter(Boolean); const minP = Math.min(...prices); const maxP = Math.max(...prices); const platforms = products.map((p: any) => p.platform).filter((v: any, i: number, a: any[]) => a.indexOf(v) === i); return (<section key={cluster.q}><div className="flex items-center gap-2 mb-3"><h2 className="text-base font-bold">{cluster.name}</h2><div className="flex gap-1">{platforms.map((p: string) => <span key={p} className="text-[9px] font-semibold px-1.5 py-0.5 rounded text-white" style={{ background: PLATFORM_COLORS[p] || '#666' }}>{PLATFORM_SHORT[p] || p}</span>)}</div>{prices.length >= 2 && <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded" style={{ background: '#FEF3C7', color: '#92400E' }}>Δ R$ {(maxP - minP).toFixed(2)}</span>}</div><div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">{products.map((item: any, i: number) => { const c = PLATFORM_COLORS[item.platform] || '#666'; const l = PLATFORM_SHORT[item.platform] || item.platform; const isBest = item.price_brl === minP && prices.length >= 2; return (<a key={i} href={item.product_url} target="_blank" rel="noopener noreferrer" className="bg-white rounded-xl overflow-hidden hover:shadow-lg transition-all" style={{ border: isBest ? '2px solid #059669' : '1px solid #E5E5E5' }}><div className="aspect-square flex items-center justify-center" style={{ background: '#F5F5F5' }}>{item.image_url ? <img src={`/api/proxy/image?url=${encodeURIComponent(item.image_url)}`} alt="" className="w-full h-full object-contain" loading="lazy" /> : <span className="text-2xl" style={{ color: '#D4D4D4' }}>📦</span>}</div><div className="p-2.5"><div className="flex items-center gap-1 mb-1"><span className="text-[9px] font-semibold px-1.5 py-0.5 rounded text-white" style={{ background: c }}>{l}</span>{isBest && <span className="text-[8px] font-bold" style={{ color: '#059669' }}>BEST</span>}</div><div className="text-[10px] font-medium line-clamp-2">{item.product_name}</div><div className="text-sm font-bold mt-1" style={{ color: '#059669' }}>{item.price_brl ? `R$ ${item.price_brl.toFixed(2)}` : '—'}</div></div></a>); })}</div></section>); })}</div>
    </div>
  );
}
