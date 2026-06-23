import Link from 'next/link';

const CATEGORIES = [
  { slug: 'audio', name: 'Áudio & Microfones', icon: '🎙️' },
  { slug: 'eletronicos', name: 'Eletrônicos & Acessórios', icon: '📱' },
  { slug: 'wearables', name: 'Wearables & Smartwatches', icon: '⌚' },
  { slug: 'camera', name: 'Câmeras & Segurança', icon: '📷' },
  { slug: 'casa', name: 'Casa & Decoração', icon: '🏠' },
  { slug: 'cozinha', name: 'Cozinha & Utensílios', icon: '🍳' },
  { slug: 'moda', name: 'Moda & Acessórios', icon: '👗' },
  { slug: 'beleza', name: 'Beleza & Cuidados', icon: '💄' },
  { slug: 'saude', name: 'Saúde & Bem-Estar', icon: '🏥' },
  { slug: 'esportes', name: 'Esportes & Lazer', icon: '🏋️' },
  { slug: 'pets', name: 'Pet Shop', icon: '🐾' },
  { slug: 'infantis', name: 'Infantil & Brinquedos', icon: '🧸' },
  { slug: 'automotivo', name: 'Automotivo', icon: '🚗' },
  { slug: 'ferramentas', name: 'Ferramentas', icon: '🔧' },
  { slug: 'jardim', name: 'Jardim & Plantio', icon: '🌱' },
  { slug: 'iluminacao', name: 'Iluminação', icon: '💡' },
  { slug: 'papelaria', name: 'Papelaria & Escritório', icon: '📝' },
  { slug: 'moveis', name: 'Móveis & Organização', icon: '🪑' },
  { slug: 'calcados', name: 'Calçados', icon: '👟' },
  { slug: 'uncategorized', name: 'Sem Categoria', icon: '❓' },
];

export default function CategoriesPage() {
  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-6">
        <Link href="/arbitlens" className="text-xs" style={{ color: '#C8102E' }}>← Dashboard</Link>
        <h1 className="text-2xl font-bold mt-2">Categories</h1>
        <p className="text-sm" style={{ color: '#8A8A8A' }}>4-level taxonomy: 19 root → 89 sub → 162 types → 32 niches</p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
        {CATEGORIES.map(cat => (
          <Link
            key={cat.slug}
            href={`/arbitlens/categories/${cat.slug}`}
            className="bg-white rounded-xl p-4 hover:shadow-lg transition-all"
            style={{ border: '1px solid #E5E5E5' }}
          >
            <div className="text-3xl mb-2">{cat.icon}</div>
            <div className="text-sm font-semibold">{cat.name}</div>
          </Link>
        ))}
      </div>
    </div>
  );
}
