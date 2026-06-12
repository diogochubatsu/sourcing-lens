/* =========================================
   ARBITLENS — Vanilla JS App
   ========================================= */

// --- Demo Data ---
const DEMO_PRODUCT = {
  title: 'Wireless Lapel Microphone Type-C',
  source: 'Mercado Livre',
  source_price: 'R$88',
  emoji: '🎤',

  prices: [
    { platform: '1688 (source)',     price: '¥22 ($3)',   sales: 'MOQ 50',       status: 'active', statusLabel: '✅ Active' },
    { platform: 'AliExpress',        price: '$7.99',      sales: '2,340 ord',    status: 'active', statusLabel: '✅ Active' },
    { platform: 'Amazon BR',         price: 'R$129',      sales: 'BSR #1,203',   status: 'active', statusLabel: '✅ Active' },
    { platform: 'Amazon USA',        price: '$15.99',     sales: 'BSR #4,521',   status: 'active', statusLabel: '✅ Active' },
    { platform: 'Mercado Livre',     price: 'R$88',       sales: '1,240 sold',   status: 'active', statusLabel: '✅ Active' },
    { platform: 'Shopee BR',         price: 'R$79',       sales: '890 sold',     status: 'active', statusLabel: '✅ Active' },
    { platform: 'TikTok Shop',       price: '$12.99',     sales: 'trending',     status: 'hot',    statusLabel: '🔥 Hot' },
  ],

  margins: [
    { platform: 'Mercado Livre', cost: 'R$25',   price: 'R$88',   pct: 72 },
    { platform: 'Amazon BR',     cost: 'R$25',   price: 'R$129',  pct: 81 },
    { platform: 'Shopee BR',     cost: 'R$25',   price: 'R$79',   pct: 68 },
    { platform: 'Amazon USA',    cost: '$8.50',  price: '$15.99', pct: 47 },
  ],

  matches: [
    { pct: 98, platform: '1688', supplier: 'Shenzhen Coico Electronics',   meta: '¥22/unit, MOQ 50, 98.2% positive', url: '#' },
    { pct: 92, platform: '1688', supplier: 'Guangzhou Audio Tech',         meta: '¥18/unit, MOQ 200, 95.1% positive', url: '#' },
    { pct: 87, platform: 'AliExpress', supplier: '"Lapel Mic Wireless Type-C"', meta: '$7.99, 2,340 orders, 4.6★', url: '#' },
    { pct: 65, platform: '1688', supplier: 'Yiwu Direct Store',           meta: '¥15/unit, MOQ 500, 92.3% positive', url: '#' },
    { pct: 41, platform: 'AliExpress', supplier: '"Mini Mic USB-C Phone"', meta: '$5.49, 180 orders, 4.2★', url: '#' },
  ],

  pulse: {
    velocity:    { icon: '🔥', label: 'Velocity',    value: 'Hot — trending up this month' },
    competition: { icon: '🟡', label: 'Competition', value: 'Medium — 12 sellers on ML' },
    window:      { icon: '📅', label: 'Window',      value: '~3-6 months before saturation' },
    sources: [
      'Mercado Livre: #3 in Games category',
      'TikTok Shop: Tech accessories trending',
      'Amazon BR: BSR climbing last 30 days',
    ],
  },

  verdict: {
    level: 'strong',
    label: '⚡ VERDICT: Strong Opportunity',
    points: [
      '72% margin on ML with 50-unit order',
      'Content creation boom driving demand',
      'TikTok viral signal confirms trend',
      'Moderate competition — room for entry',
      'Recommended: Test with 50 units on ML',
      'Risk: Trend may peak in 3-4 months',
    ],
    tip: '💡 <strong>TIP:</strong> The 92% match at ¥18/MOQ200 drops your cost to R$18/unit, pushing margin to 79%. Scale to 200 once you validate demand.',
  },
};

const TRENDING_ITEMS = [
  { emoji: '🎤', name: 'Wireless Mic',       price: 'R$88',  fire: true,  query: 'wireless lapel microphone type-c' },
  { emoji: '🧹', name: 'Electric Scrubber',   price: 'R$149', fire: true,  query: 'electric spin scrubber' },
  { emoji: '📽️', name: 'Mini Projector',      price: 'R$299', fire: false, query: 'mini projector portable' },
  { emoji: '🎧', name: 'Bluetooth Earbuds',   price: 'R$79',  fire: false, query: 'bluetooth earbuds wireless' },
  { emoji: '💡', name: 'LED Strip Lights',     price: 'R$45',  fire: true,  query: 'led strip lights rgb' },
  { emoji: '⌚', name: 'Smart Watch',          price: 'R$129', fire: false, query: 'smart watch fitness tracker' },
  { emoji: '🔌', name: 'USB-C Hub',           price: 'R$89',  fire: false, query: 'usb c hub multiport' },
  { emoji: '📱', name: 'Phone Gimbal',        price: 'R$199', fire: true,  query: 'phone gimbal stabilizer' },
];

// --- Routing ---
function navigate(view) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  const el = document.getElementById(view);
  if (el) {
    el.classList.add('active');
    window.scrollTo(0, 0);
  }
  // Update URL hash
  history.pushState(null, '', view === 'search' ? '/' : '/product');
}

function handleRoute() {
  const hash = window.location.hash.replace('#', '') || 'search';
  if (hash === 'product') {
    navigate('product-view');
  } else {
    navigate('search-view');
  }
}

// --- Search ---
function doSearch(query) {
  if (!query.trim()) return;
  // In MVP with demo data, any search goes to product page
  navigate('product-view');
}

// --- Render Functions ---
function renderTrending() {
  const grid = document.getElementById('trending-grid');
  if (!grid) return;
  grid.innerHTML = TRENDING_ITEMS.map(item => `
    <div class="trending-card" onclick="doSearch('${item.query}')">
      <span class="emoji">${item.emoji}</span>
      <div class="name">${item.name}</div>
      <div class="price">${item.price} ${item.fire ? '<span class="fire">🔥</span>' : ''}</div>
    </div>
  `).join('');
}

function renderPrices() {
  const tbody = document.getElementById('prices-tbody');
  if (!tbody) return;
  tbody.innerHTML = DEMO_PRODUCT.prices.map(p => `
    <tr>
      <td>${p.platform}</td>
      <td class="price">${p.price}</td>
      <td>${p.sales}</td>
      <td class="status-${p.status}">${p.statusLabel}</td>
    </tr>
  `).join('');
}

function renderMargins() {
  const container = document.getElementById('margin-rows');
  if (!container) return;
  container.innerHTML = DEMO_PRODUCT.margins.map(m => {
    const cls = m.pct >= 70 ? 'high' : m.pct >= 50 ? 'medium' : 'low';
    return `
      <div class="margin-row">
        <span class="margin-platform">${m.platform}</span>
        <span class="margin-cost">${m.cost}</span>
        <span class="margin-price">${m.price}</span>
        <span class="margin-pct ${cls}">${m.pct}%</span>
      </div>
    `;
  }).join('');
}

function renderMatches() {
  const container = document.getElementById('match-items');
  if (!container) return;
  container.innerHTML = DEMO_PRODUCT.matches.map(m => {
    const cls = m.pct >= 85 ? 'high' : m.pct >= 60 ? 'medium' : 'low';
    return `
      <div class="match-item">
        <div class="match-confidence">
          <div class="pct ${cls}">${m.pct}%</div>
          <div class="label">match</div>
        </div>
        <div class="match-details">
          <div class="supplier">${m.platform}: ${m.supplier}</div>
          <div class="meta">${m.meta}</div>
          <a href="${m.url}" class="view-link">view listing →</a>
        </div>
      </div>
    `;
  }).join('');
}

function renderPulse() {
  const container = document.getElementById('pulse-grid');
  if (!container) return;
  const p = DEMO_PRODUCT.pulse;
  const items = [p.velocity, p.competition, p.window];

  container.innerHTML = items.map(item => `
    <div class="pulse-item">
      <span class="pulse-icon">${item.icon}</span>
      <div>
        <div class="pulse-label">${item.label}</div>
        <div class="pulse-value">${item.value}</div>
      </div>
    </div>
  `).join('') + `
    <div class="pulse-sources">
      <h4>Trend sources</h4>
      ${p.sources.map(s => `<div class="pulse-source-item">${s}</div>`).join('')}
    </div>
  `;
}

function renderVerdict() {
  const container = document.getElementById('verdict-content');
  if (!container) return;
  const v = DEMO_PRODUCT.verdict;

  container.innerHTML = `
    <div class="verdict-header">
      <span class="verdict-badge ${v.level}">${v.label}</span>
    </div>
    <ul class="verdict-points">
      ${v.points.map(pt => `<li>${pt}</li>`).join('')}
    </ul>
    <div class="verdict-tip">${v.tip}</div>
  `;
}

// --- Init ---
document.addEventListener('DOMContentLoaded', () => {
  // Render all sections
  renderTrending();
  renderPrices();
  renderMargins();
  renderMatches();
  renderPulse();
  renderVerdict();

  // Search bar event
  const searchInput = document.getElementById('search-input');
  const searchBtn = document.getElementById('search-btn');

  if (searchBtn) {
    searchBtn.addEventListener('click', () => doSearch(searchInput.value));
  }
  if (searchInput) {
    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') doSearch(searchInput.value);
    });
  }

  // Back button
  const backBtn = document.getElementById('back-btn');
  if (backBtn) {
    backBtn.addEventListener('click', () => navigate('search-view'));
  }

  // Action buttons (just alerts for demo)
  document.querySelectorAll('.action-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const label = btn.textContent.trim();
      alert(`Demo mode: "${label}" — will be wired to backend in Phase 2.`);
    });
  });

  // Initial route
  navigate('search-view');
});
