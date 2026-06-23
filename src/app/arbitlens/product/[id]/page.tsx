import Link from 'next/link';
import { execFileSync } from 'child_process';
import path from 'path';

const SCRIPT_DIR = path.join(process.cwd(), 'scripts', 'arbitlens');
const PLATFORM_COLORS: Record<string, string> = { 'rakumart-1688': '#3B82F6', 'rakumart-taobao': '#8B5CF6', 'rakumart-alibaba': '#06B6D4', 'dhgate': '#F97316', 'alibaba': '#EAB308' };
const PLATFORM_SHORT: Record<string, string> = { 'rakumart-1688': '1688', 'rakumart-taobao': 'Taobao', 'rakumart-alibaba': 'Alibaba BR', 'dhgate': 'DHgate', 'alibaba': 'Alibaba' };

function searchProducts(q: string, limit: number = 6) {
  try { const output = execFileSync('python3', ['-u', path.join(SCRIPT_DIR, 'search.py'), q, String(limit)], { cwd: process.cwd(), timeout: 30000, encoding: 'utf-8', maxBuffer: 5 * 1024 * 1024 }); return JSON.parse(output).products || []; } catch { return []; }
}

export default async function ProductDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const parts = id.split('_', 2);
  const platform = parts[0];
  const platformId = id.replace(platform + '_', '');
  const products = searchProducts(platformId, 1);
  const product = products[0] || null;
  const similarProducts = product ? searchProducts(product.product_name?.substring(0, 30) || '', 6) : [];
  if (!product) return <div className="max-w-5xl mx-auto px-4 py-8"><Link href="/arbitlens" className="text-xs" style={{ color: '#C8102E' }}>← Dashboard</Link><div className="text-center py-16" style={{ color: '#8A8A8A' }}>Product not found</div></div>;
  const color = PLATFORM_COLORS[product.platform] || '#666';
  const label = PLATFORM_SHORT[product.platform] || product.platform;
  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <nav className="flex items-center gap-1.5 text-xs mb-6"><Link href="/arbitlens" className="hover:underline" style={{ color: '#C8102E' }}>Dashboard</Link><span style={{ color: '#8A8A8A' }}>/</span><span className="font-semibold">{label}</span></nav>
      <div className="grid md:grid-cols-2 gap-8 mb-10">
        <div><div className="aspect-square rounded-2xl overflow-hidden" style={{ background: '#F5F5F5' }}>{product.image_url ? <img src={`/api/proxy/image?url=${encodeURIComponent(product.image_url)}`} alt={product.product_name} className="w-full h-full object-contain" /> : <div className="w-full h-full flex items-center justify-center text-5xl" style={{ color: '#D4D4D4' }}>📦</div>}</div></div>
        <div><div className="flex items-center gap-2 mb-3"><span className="text-[10px] font-semibold px-2 py-1 rounded text-white" style={{ background: color }}>{label}</span></div><h1 className="text-xl font-bold mb-4 leading-snug">{product.product_name}</h1><div className="mb-6"><div className="text-3xl font-bold" style={{ color: '#059669' }}>{product.price_brl ? `R$ ${product.price_brl.toFixed(2)}` : '—'}</div></div><div className="grid grid-cols-3 gap-3 mb-6 p-4 rounded-xl" style={{ background: '#F5F5F5' }}><div><div className="text-[10px] uppercase tracking-wider" style={{ color: '#8A8A8A' }}>Sales/mo</div><div className="text-lg font-bold mt-1">{product.monthly_sales || '—'}</div></div><div><div className="text-[10px] uppercase tracking-wider" style={{ color: '#8A8A8A' }}>Reviews</div><div className="text-lg font-bold mt-1">{product.review_count || '—'}</div></div><div><div className="text-[10px] uppercase tracking-wider" style={{ color: '#8A8A8A' }}>Rating</div><div className="text-lg font-bold mt-1">{product.rating ? `${product.rating}/5` : '—'}</div></div></div>{product.seller_name && <div className="mb-6 p-3 rounded-xl" style={{ background: '#F5F5F5' }}><div className="text-[10px] uppercase mb-1" style={{ color: '#8A8A8A' }}>Supplier</div><div className="text-sm font-semibold">{product.seller_name}</div></div>}<div className="flex gap-3">{product.product_url && <a href={product.product_url} target="_blank" rel="noopener noreferrer" className="flex-1 px-5 py-3 text-white text-sm font-semibold rounded-xl text-center" style={{ background: '#0A0A0A' }}>View on {label} →</a>}<Link href={`/arbitlens/search?q=${encodeURIComponent(product.product_name?.substring(0, 30) || '')}`} className="flex-1 px-5 py-3 text-sm font-semibold rounded-xl text-center" style={{ border: '1px solid #E5E5E5' }}>Search similar</Link></div></div>
      </div>
      {similarProducts.length > 1 && <section><h2 className="text-lg font-bold mb-4">Similar products</h2><div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">{similarProducts.slice(1).map((item: any, i: number) => { const c = PLATFORM_COLORS[item.platform] || '#666'; const l = PLATFORM_SHORT[item.platform] || item.platform; return (<a key={i} href={item.product_url} target="_blank" rel="noopener noreferrer" className="bg-white rounded-xl overflow-hidden hover:shadow-lg transition-all" style={{ border: '1px solid #E5E5E5' }}><div className="aspect-square flex items-center justify-center" style={{ background: '#F5F5F5' }}>{item.image_url ? <img src={`/api/proxy/image?url=${encodeURIComponent(item.image_url)}`} alt="" className="w-full h-full object-contain" loading="lazy" /> : <span className="text-3xl" style={{ color: '#D4D4D4' }}>📦</span>}</div><div className="p-2.5"><span className="inline-block text-[9px] font-semibold px-1.5 py-0.5 rounded text-white mb-1" style={{ background: c }}>{l}</span><div className="text-[11px] font-medium line-clamp-2">{item.product_name}</div><div className="text-sm font-bold mt-1" style={{ color: '#059669' }}>{item.price_brl ? `R$ ${item.price_brl.toFixed(2)}` : '—'}</div></div></a>); })}</div></section>}
    </div>
  );
}
