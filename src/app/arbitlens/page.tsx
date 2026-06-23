export const dynamic = "force-dynamic";
import Link from 'next/link';
import { execFileSync } from 'child_process';
import path from 'path';

const SCRIPT_DIR = path.join(process.cwd(), 'scripts', 'arbitlens');
const CATEGORIES = [
  { slug: 'audio', name: 'Áudio', icon: '🎙️', q: 'microfone wireless speaker' },
  { slug: 'eletronicos', name: 'Eletrônicos', icon: '📱', q: 'carregador power bank' },
  { slug: 'wearables', name: 'Wearables', icon: '⌚', q: 'smartwatch pulseira' },
  { slug: 'camera', name: 'Câmeras', icon: '📷', q: 'webcam camera drone' },
  { slug: 'casa', name: 'Casa', icon: '🏠', q: 'organizador decoração' },
  { slug: 'cozinha', name: 'Cozinha', icon: '🍳', q: 'panela copo' },
  { slug: 'moda', name: 'Moda', icon: '👗', q: 'bolsa mochila óculos' },
  { slug: 'beleza', name: 'Beleza', icon: '💄', q: 'maquiagem secador' },
  { slug: 'saude', name: 'Saúde', icon: '🏥', q: 'oxímetro termômetro' },
  { slug: 'esportes', name: 'Esportes', icon: '🏋️', q: 'yoga halteres' },
  { slug: 'pets', name: 'Pet Shop', icon: '🐾', q: 'cachorro gato coleira' },
  { slug: 'infantis', name: 'Infantil', icon: '🧸', q: 'brinquedo lego' },
  { slug: 'automotivo', name: 'Automotivo', icon: '🚗', q: 'suporte celular carro' },
  { slug: 'ferramentas', name: 'Ferramentas', icon: '🔧', q: 'furadeira parafusadeira' },
  { slug: 'jardim', name: 'Jardim', icon: '🌱', q: 'regador vaso planta' },
  { slug: 'iluminacao', name: 'Iluminação', icon: '💡', q: 'lampada led ring light' },
  { slug: 'papelaria', name: 'Papelaria', icon: '📝', q: 'caneta caderno' },
  { slug: 'moveis', name: 'Móveis', icon: '🪑', q: 'cadeira mesa' },
  { slug: 'calcados', name: 'Calçados', icon: '👟', q: 'tênis chinelo' },
  { slug: 'uncategorized', name: 'Sem Categoria', icon: '❓', q: '' },
];
const PLATFORM_COLORS: Record<string, string> = { 'rakumart-1688': '#3B82F6', 'rakumart-taobao': '#8B5CF6', 'rakumart-alibaba': '#06B6D4', 'dhgate': '#F97316', 'alibaba': '#EAB308' };
const PLATFORM_SHORT: Record<string, string> = { 'rakumart-1688': '1688', 'rakumart-taobao': 'Taobao', 'rakumart-alibaba': 'Alibaba BR', 'dhgate': 'DHgate', 'alibaba': 'Alibaba' };

function searchProducts(q: string, limit: number = 3) {
  try { const output = execFileSync('python3', ['-u', path.join(SCRIPT_DIR, 'search.py'), q, String(limit)], { cwd: process.cwd(), timeout: 20000, encoding: 'utf-8', maxBuffer: 5 * 1024 * 1024 }); return JSON.parse(output).products || []; } catch { return []; }
}

export default async function DashboardPage() {
  // Only 4 categories for faster load (was 8)
  const sampleCategories = CATEGORIES.slice(0, 4);
  const categoryProducts: Record<string, any[]> = {};
  for (const cat of sampleCategories) { categoryProducts[cat.slug] = searchProducts(cat.q, 3); }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <section className="text-center mb-10"><h1 className="text-3xl sm:text-4xl font-bold tracking-tight mb-3">Cross-Marketplace<span className="block" style={{ color: '#C8102E' }}>Product Intelligence</span></h1><p className="text-sm mb-6 max-w-lg mx-auto" style={{ color: '#8A8A8A' }}>13,508 products across 5 Chinese marketplaces.</p><form className="flex gap-2 max-w-xl mx-auto" action="/arbitlens/search" method="get"><input type="text" name="q" placeholder='Search products...' className="flex-1 px-4 py-3 text-sm bg-white rounded-xl focus:outline-none" style={{ border: '1px solid #E5E5E5' }} /><button type="submit" className="px-5 py-3 text-white text-sm font-semibold rounded-xl" style={{ background: '#0A0A0A' }}>Search</button></form></section>
      <section className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-10"><div className="p-4 bg-white rounded-xl text-center" style={{ border: '1px solid #E5E5E5' }}><div className="text-2xl font-bold">13,508</div><div className="text-xs" style={{ color: '#8A8A8A' }}>Products</div></div><div className="p-4 bg-white rounded-xl text-center" style={{ border: '1px solid #E5E5E5' }}><div className="text-2xl font-bold">5</div><div className="text-xs" style={{ color: '#8A8A8A' }}>Platforms</div></div><div className="p-4 bg-white rounded-xl text-center" style={{ border: '1px solid #E5E5E5' }}><div className="text-2xl font-bold">1,441</div><div className="text-xs" style={{ color: '#8A8A8A' }}>Matches</div></div><div className="p-4 bg-white rounded-xl text-center" style={{ border: '1px solid #E5E5E5' }}><div className="text-2xl font-bold">20</div><div className="text-xs" style={{ color: '#8A8A8A' }}>Categories</div></div></section>
      <section className="mb-10"><div className="flex items-center justify-between mb-4"><h2 className="text-lg font-bold">Categories</h2><Link href="/arbitlens/categories" className="text-xs font-medium" style={{ color: '#C8102E' }}>View all →</Link></div><div className="grid grid-cols-4 sm:grid-cols-5 lg:grid-cols-10 gap-2">{CATEGORIES.map(cat => <Link key={cat.slug} href={`/arbitlens/search?q=${encodeURIComponent(cat.q || cat.name)}`} className="p-3 bg-white rounded-xl text-center hover:shadow-md transition-all" style={{ border: '1px solid #E5E5E5' }}><div className="text-2xl mb-1">{cat.icon}</div><div className="text-[10px] font-medium leading-tight">{cat.name}</div></Link>)}</div></section>
      {sampleCategories.map(cat => { const products = categoryProducts[cat.slug] || []; if (products.length === 0) return null; return (<section key={cat.slug} className="mb-8"><div className="flex items-center justify-between mb-3"><h2 className="text-base font-bold flex items-center gap-2"><span>{cat.icon}</span> {cat.name}</h2><Link href={`/arbitlens/search?q=${encodeURIComponent(cat.q || cat.name)}`} className="text-xs font-medium" style={{ color: '#C8102E' }}>View all →</Link></div><div className="grid grid-cols-3 gap-3">{products.map((item: any, i: number) => (<a key={i} href={item.product_url} target="_blank" rel="noopener noreferrer" className="bg-white rounded-xl overflow-hidden hover:shadow-md transition-all" style={{ border: '1px solid #E5E5E5' }}><div className="aspect-square flex items-center justify-center" style={{ background: '#F5F5F5' }}>{item.image_url ? <img src={`/api/proxy/image?url=${encodeURIComponent(item.image_url)}`} alt="" className="w-full h-full object-contain" loading="lazy" /> : <span className="text-2xl" style={{ color: '#D4D4D4' }}>📦</span>}</div><div className="p-2"><div className="text-[9px] font-semibold px-1 py-0.5 rounded text-white w-fit mb-1" style={{ background: PLATFORM_COLORS[item.platform] || '#666' }}>{PLATFORM_SHORT[item.platform] || item.platform}</div><div className="text-[10px] font-medium line-clamp-2">{item.product_name}</div><div className="text-xs font-bold mt-0.5" style={{ color: '#059669' }}>{item.price_brl ? `R$ ${item.price_brl.toFixed(2)}` : '—'}</div></div></a>))}</div></section>); })}
    </div>
  );
}
