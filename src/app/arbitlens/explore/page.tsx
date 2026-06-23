import Link from 'next/link';

export default function ExplorePage() {
  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-6"><Link href="/arbitlens" className="text-xs" style={{ color: '#C8102E' }}>← Dashboard</Link><h1 className="text-2xl font-bold mt-2">Explore Products</h1><p className="text-sm" style={{ color: '#8A8A8A' }}>Multi-dimensional data warehouse</p></div>
      
      <div className="bg-white rounded-xl p-6 mb-6" style={{ border: '1px solid #E5E5E5' }}>
        <h2 className="text-lg font-bold mb-4">Data Warehouse API</h2>
        <p className="text-sm mb-4" style={{ color: '#8A8A8A' }}>Use the API endpoint to query products with filters:</p>
        
        <div className="bg-[#1a1a1a] rounded-lg p-4 mb-4 overflow-x-auto">
          <code className="text-xs text-green-400 whitespace-pre">
{`GET /api/arbitlens/explore
  ?category=audio
  &platform=rakumart-1688,rakumart-taobao
  &min_price=10
  &max_price=100
  &min_sales=50
  &min_match=0.80
  &sort=price_asc
  &page=1
  &limit=50`}
          </code>
        </div>

        <h3 className="text-sm font-bold mb-2">Quick Links</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          <a href="/api/arbitlens/explore?limit=10" target="_blank" className="p-3 bg-surface-warm rounded-lg text-xs hover:shadow-md transition-all" style={{ border: '1px solid #E5E5E5' }}>
            <div className="font-semibold">All Products</div>
            <div className="text-ink-faint mt-1">/api/arbitlens/explore</div>
          </a>
          <a href="/api/arbitlens/explore?category=audio&limit=10" target="_blank" className="p-3 bg-surface-warm rounded-lg text-xs hover:shadow-md transition-all" style={{ border: '1px solid #E5E5E5' }}>
            <div className="font-semibold">🎙️ Audio</div>
            <div className="text-ink-faint mt-1">?category=audio</div>
          </a>
          <a href="/api/arbitlens/explore?category=eletronicos&limit=10" target="_blank" className="p-3 bg-surface-warm rounded-lg text-xs hover:shadow-md transition-all" style={{ border: '1px solid #E5E5E5' }}>
            <div className="font-semibold">📱 Eletrônicos</div>
            <div className="text-ink-faint mt-1">?category=eletronicos</div>
          </a>
          <a href="/api/arbitlens/explore?category=wearables&limit=10" target="_blank" className="p-3 bg-surface-warm rounded-lg text-xs hover:shadow-md transition-all" style={{ border: '1px solid #E5E5E5' }}>
            <div className="font-semibold">⌚ Wearables</div>
            <div className="text-ink-faint mt-1">?category=wearables</div>
          </a>
          <a href="/api/arbitlens/explore?min_match=0.80&limit=10" target="_blank" className="p-3 bg-surface-warm rounded-lg text-xs hover:shadow-md transition-all" style={{ border: '1px solid #E5E5E5' }}>
            <div className="font-semibold">🎯 High Match</div>
            <div className="text-ink-faint mt-1">?min_match=0.80</div>
          </a>
          <a href="/api/arbitlens/explore?min_sales=100&limit=10" target="_blank" className="p-3 bg-surface-warm rounded-lg text-xs hover:shadow-md transition-all" style={{ border: '1px solid #E5E5E5' }}>
            <div className="font-semibold">🔥 Best Sellers</div>
            <div className="text-ink-faint mt-1">?min_sales=100</div>
          </a>
        </div>
      </div>

      <div className="bg-white rounded-xl p-6" style={{ border: '1px solid #E5E5E5' }}>
        <h2 className="text-lg font-bold mb-4">Example Queries</h2>
        <div className="space-y-3">
          <div className="p-3 bg-surface-warm rounded-lg">
            <div className="text-xs font-semibold mb-1">Cheap wireless microphones on 1688</div>
            <code className="text-[11px] text-ink-faint">?category=audio&platform=rakumart-1688&max_price=50&sort=price_asc</code>
          </div>
          <div className="p-3 bg-surface-warm rounded-lg">
            <div className="text-xs font-semibold mb-1">High-match products with 100+ sales</div>
            <code className="text-[11px] text-ink-faint">?min_match=0.80&min_sales=100&sort=sales_desc</code>
          </div>
          <div className="p-3 bg-surface-warm rounded-lg">
            <div className="text-xs font-semibold mb-1">Products across all platforms, sorted by price</div>
            <code className="text-[11px] text-ink-faint">?sort=price_asc&page=1&limit=50</code>
          </div>
        </div>
      </div>
    </div>
  );
}
