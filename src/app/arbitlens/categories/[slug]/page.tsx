import Link from 'next/link';
import { execFileSync } from 'child_process';
import path from 'path';

const SCRIPT_DIR = path.join(process.cwd(), 'scripts', 'arbitlens');
const CATEGORIES: Record<string, { name: string; icon: string; children: string[]; q: string }> = {
  'audio': { name: 'Áudio & Microfones', icon: '🎙️', children: ['Microfones', 'Fones de Ouvido', 'Caixas de Som'], q: 'microfone wireless speaker' },
  'eletronicos': { name: 'Eletrônicos', icon: '📱', children: ['Carregadores', 'Cabos', 'Acessórios'], q: 'carregador power bank cabo' },
  'wearables': { name: 'Wearables', icon: '⌚', children: ['Relógios', 'Pulseiras'], q: 'smartwatch pulseira' },
  'camera': { name: 'Câmeras', icon: '📷', children: ['Webcam', 'Drones'], q: 'webcam camera drone' },
  'casa': { name: 'Casa', icon: '🏠', children: ['Organização', 'Decoração'], q: 'organizador decoração' },
  'cozinha': { name: 'Cozinha', icon: '🍳', children: ['Panelas', 'Copos'], q: 'panela copo' },
  'moda': { name: 'Moda', icon: '👗', children: ['Bolsas', 'Óculos'], q: 'bolsa mochila óculos' },
  'beleza': { name: 'Beleza', icon: '💄', children: ['Maquiagem', 'Cabelo'], q: 'maquiagem secador' },
  'saude': { name: 'Saúde', icon: '🏥', children: ['Oxímetro', 'Massagem'], q: 'oxímetro termômetro' },
  'esportes': { name: 'Esportes', icon: '🏋️', children: ['Yoga', 'Halteres'], q: 'yoga halteres' },
  'pets': { name: 'Pet Shop', icon: '🐾', children: ['Cães', 'Gatos'], q: 'cachorro gato coleira' },
  'infantis': { name: 'Infantil', icon: '🧸', children: ['Brinquedos', 'Lego'], q: 'brinquedo lego' },
  'automotivo': { name: 'Automotivo', icon: '🚗', children: ['Suporte', 'Compressor'], q: 'suporte celular carro' },
  'ferramentas': { name: 'Ferramentas', icon: '🔧', children: ['Furadeira', 'Chave'], q: 'furadeira parafusadeira' },
  'jardim': { name: 'Jardim', icon: '🌱', children: ['Regador', 'Vaso'], q: 'regador vaso planta' },
  'iluminacao': { name: 'Iluminação', icon: '💡', children: ['LED', 'Ring Light'], q: 'lampada led ring light' },
  'papelaria': { name: 'Papelaria', icon: '📝', children: ['Canetas', 'Cadernos'], q: 'caneta caderno' },
  'moveis': { name: 'Móveis', icon: '🪑', children: ['Cadeiras', 'Mesas'], q: 'cadeira mesa' },
  'calcados': { name: 'Calçados', icon: '👟', children: ['Tênis', 'Chinelo'], q: 'tênis chinelo' },
  'uncategorized': { name: 'Sem Categoria', icon: '❓', children: [], q: '' },
};
const PLATFORM_COLORS: Record<string, string> = { 'rakumart-1688': '#3B82F6', 'rakumart-taobao': '#8B5CF6', 'rakumart-alibaba': '#06B6D4', 'dhgate': '#F97316', 'alibaba': '#EAB308' };
const PLATFORM_SHORT: Record<string, string> = { 'rakumart-1688': '1688', 'rakumart-taobao': 'Taobao', 'rakumart-alibaba': 'Alibaba BR', 'dhgate': 'DHgate', 'alibaba': 'Alibaba' };

function searchProducts(q: string, limit: number = 12) {
  try { const output = execFileSync('python3', ['-u', path.join(SCRIPT_DIR, 'search.py'), q, String(limit)], { cwd: process.cwd(), timeout: 30000, encoding: 'utf-8', maxBuffer: 5 * 1024 * 1024 }); return JSON.parse(output).products || []; } catch { return []; }
}

export default async function CategoryDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const cat = CATEGORIES[slug];
  if (!cat) return <div className="max-w-6xl mx-auto px-4 py-8"><Link href="/arbitlens/categories" className="text-xs" style={{ color: '#C8102E' }}>← Categories</Link><div className="text-center py-16" style={{ color: '#8A8A8A' }}>Not found</div></div>;
  const products = searchProducts(cat.q, 12);
  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <nav className="flex items-center gap-1.5 text-xs mb-4"><Link href="/arbitlens" className="hover:underline" style={{ color: '#C8102E' }}>Dashboard</Link><span style={{ color: '#8A8A8A' }}>/</span><Link href="/arbitlens/categories" className="hover:underline" style={{ color: '#C8102E' }}>Categories</Link><span style={{ color: '#8A8A8A' }}>/</span><span className="font-semibold">{cat.icon} {cat.name}</span></nav>
      <h1 className="text-2xl font-bold flex items-center gap-2 mb-2"><span className="text-3xl">{cat.icon}</span> {cat.name}</h1>
      {cat.children.length > 0 && <div className="flex gap-2 flex-wrap mb-6">{cat.children.map(c => <span key={c} className="px-3 py-1.5 text-xs bg-white rounded-full" style={{ border: '1px solid #E5E5E5' }}>{c}</span>)}</div>}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">{products.map((item: any, i: number) => { const c = PLATFORM_COLORS[item.platform] || '#666'; const l = PLATFORM_SHORT[item.platform] || item.platform; return (<a key={i} href={item.product_url} target="_blank" rel="noopener noreferrer" className="bg-white rounded-xl overflow-hidden hover:shadow-lg transition-all" style={{ border: '1px solid #E5E5E5' }}><div className="aspect-square flex items-center justify-center" style={{ background: '#F5F5F5' }}>{item.image_url ? <img src={`/api/proxy/image?url=${encodeURIComponent(item.image_url)}`} alt="" className="w-full h-full object-contain" loading="lazy" /> : <span className="text-3xl" style={{ color: '#D4D4D4' }}>📦</span>}</div><div className="p-2.5"><span className="inline-block text-[9px] font-semibold px-1.5 py-0.5 rounded text-white mb-1" style={{ background: c }}>{l}</span><div className="text-[11px] font-medium line-clamp-2">{item.product_name}</div><div className="text-sm font-bold mt-1" style={{ color: '#059669' }}>{item.price_brl ? `R$ ${item.price_brl.toFixed(2)}` : '—'}</div></div></a>); })}</div>
    </div>
  );
}
