'use client';
import Link from 'next/link';

const pageWrap: React.CSSProperties = { maxWidth: 1180, margin: '0 auto', padding: '32px 32px 80px' };

// ═══ Tipografia ═══
const mono = { fontFamily: 'var(--font-mono)' };
const sans = { fontFamily: 'var(--font-sans)' };
const textMute = { color: 'var(--ink-muted)' };
const textFaint = { color: 'var(--ink-faint)' };
const textInk = { color: 'var(--ink)' };

// ═══ Header ═══
const headerWrap: React.CSSProperties = {
  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
  paddingBottom: 16, marginBottom: 64, borderBottom: '1px solid var(--border)',
  flexWrap: 'wrap', gap: 16,
};
const logo: React.CSSProperties = { ...mono, fontSize: 14, fontWeight: 700, letterSpacing: '0.05em', color: 'var(--ink)' };
const logoSub: React.CSSProperties = { ...mono, fontSize: 10, color: 'var(--ink-faint)', letterSpacing: '0.1em' };
const nav: React.CSSProperties = { display: 'flex', gap: 24 };
const navLink: React.CSSProperties = { ...sans, fontSize: 13, fontWeight: 500, color: 'var(--ink)' };
const navMeta: React.CSSProperties = { display: 'flex', alignItems: 'center', gap: 12, ...mono, fontSize: 11, color: 'var(--ink-faint)' };

// ═══ Hero (sem "sem achismo") ═══
const heroWrap: React.CSSProperties = { marginBottom: 96 };
const heroMeta: React.CSSProperties = { ...mono, fontSize: 11, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--ink-faint)', marginBottom: 24 };
const heroDot: React.CSSProperties = { display: 'inline-block', width: 6, height: 6, borderRadius: '50%', background: 'var(--brand)', marginRight: 8, verticalAlign: 'middle' };
const heroH1: React.CSSProperties = { ...sans, fontSize: 56, fontWeight: 600, lineHeight: 1.05, letterSpacing: '-0.025em', color: 'var(--ink)', margin: 0, maxWidth: 880 };
const heroH1Accent: React.CSSProperties = { fontStyle: 'italic', fontWeight: 400, color: 'var(--brand)' };
const heroSub: React.CSSProperties = { ...sans, fontSize: 17, lineHeight: 1.5, color: 'var(--ink-muted)', maxWidth: 640, marginTop: 20 };

const searchCmd: React.CSSProperties = {
  display: 'flex', alignItems: 'center', gap: 12, marginTop: 32,
  padding: '14px 18px', border: '1px solid var(--border)', borderRadius: 4,
  background: 'var(--bg-card)', maxWidth: 640,
};
const searchInput: React.CSSProperties = { ...sans, fontSize: 16, color: 'var(--ink)', flex: 1, outline: 'none', border: 'none', background: 'transparent', fontWeight: 400 };
const searchKbd: React.CSSProperties = { ...mono, fontSize: 11, color: 'var(--ink-muted)', padding: '2px 6px', border: '1px solid var(--border-soft)', borderRadius: 3, background: 'var(--bg-soft)' };

// ═══ EXTRATO DE SOURCING (tabela densa) ═══
const sectionLabel: React.CSSProperties = { ...mono, fontSize: 10, fontWeight: 700, letterSpacing: '0.15em', textTransform: 'uppercase', color: 'var(--ink-faint)', marginBottom: 8 };
const sectionTitle: React.CSSProperties = { ...sans, fontSize: 28, fontWeight: 500, letterSpacing: '-0.015em', color: 'var(--ink)', margin: 0, marginBottom: 8 };
const sectionSub: React.CSSProperties = { ...sans, fontSize: 14, color: 'var(--ink-muted)', margin: 0, marginBottom: 32, maxWidth: 600 };

const extratoTable: React.CSSProperties = { width: '100%', borderCollapse: 'collapse', ...sans, fontSize: 13 };
const extratoTh: React.CSSProperties = { ...mono, fontSize: 10, fontWeight: 500, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--ink-faint)', textAlign: 'left', padding: '10px 12px', borderBottom: '1px solid var(--border)', background: 'var(--bg-soft)' };
const extratoTd: React.CSSProperties = { padding: '14px 12px', borderBottom: '1px solid var(--border-soft)', color: 'var(--ink)' };
const extratoTdMono: React.CSSProperties = { ...extratoTd, ...mono, fontSize: 12, color: 'var(--ink-soft)' };
const extratoTdLabel: React.CSSProperties = { ...mono, fontSize: 11, color: 'var(--ink-faint)' };
const extratoTotal: React.CSSProperties = { background: 'var(--bg-dark)', color: 'white' };

// ═══ MERCADO HOJE (lista densa com sparklines) ═══
const marketTable: React.CSSProperties = { width: '100%', borderCollapse: 'collapse', ...sans, fontSize: 13 };
const marketTh: React.CSSProperties = { ...mono, fontSize: 10, fontWeight: 500, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--ink-faint)', textAlign: 'left', padding: '10px 12px', borderBottom: '1px solid var(--border)' };
const marketTd: React.CSSProperties = { padding: '14px 12px', borderBottom: '1px solid var(--border-soft)', color: 'var(--ink)' };

// ═══ CTA Footer ═══
const ctaWrap: React.CSSProperties = {
  marginTop: 96, padding: '48px 0', borderTop: '1px solid var(--border)', borderBottom: '1px solid var(--border)',
  display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 32, alignItems: 'center',
};
const ctaTitle: React.CSSProperties = { ...sans, fontSize: 32, fontWeight: 500, letterSpacing: '-0.02em', color: 'var(--ink)', margin: 0, lineHeight: 1.15 };
const ctaSub: React.CSSProperties = { ...sans, fontSize: 14, color: 'var(--ink-muted)', margin: '12px 0 0' };
const ctaRight: React.CSSProperties = { display: 'flex', flexDirection: 'column', gap: 8, ...mono, fontSize: 11, color: 'var(--ink-faint)', textAlign: 'right' };

// ═══ Footer ═══
const footerStyle: React.CSSProperties = {
  marginTop: 64, paddingTop: 24, display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12,
  ...mono, fontSize: 10, color: 'var(--ink-faint)', letterSpacing: '0.05em',
};

// ═══ Mini sparkline SVG ═══
const Sparkline = ({ data, color = 'var(--ink)', width = 80, height = 24 }: { data: number[]; color?: string; width?: number; height?: number }) => {
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const step = width / (data.length - 1);
  const path = data.map((v, i) => {
    const x = i * step;
    const y = height - ((v - min) / range) * height;
    return `${i === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
  }).join(' ');
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{ display: 'block' }}>
      <path d={path} fill="none" stroke={color} strokeWidth="1.5" />
    </svg>
  );
};

const Icon = ({ d }: { d: React.ReactNode }) => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{d}</svg>
);
const IconArrow = () => <Icon d={<><path d="M5 12h14" /><path d="m12 5 7 7-7 7" /></>} />;

export default function HomePage() {
  return (
    <div style={pageWrap}>

      {/* ═══ HEADER ═══ */}
      <header style={headerWrap}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
          <span style={logo}>1688 INTEL</span>
          <span style={logoSub}>cotação de sourcing</span>
        </div>
        <nav style={nav}>
          <Link href="/arbitlens" style={navLink}>Buscar</Link>
          <Link href="/scout" style={navLink}>Scout</Link>
          <Link href="/categorias" style={navLink}>Categorias</Link>
          <Link href="/tendencias" style={navLink}>Mercado</Link>
        </nav>
        <div style={navMeta}>
          <span>BRL · 0,71</span>
          <span>·</span>
          <span>12/06/2026 14:23 BRT</span>
        </div>
      </header>

      {/* ═══ HERO ═══ */}
      <section style={heroWrap}>
        <div style={heroMeta}>
          <span style={heroDot} /> COTAÇÃO · 12/JUN/2026 · 1.026 produtos
        </div>
        <h1 style={heroH1}>
          Cotação de sourcing em 4 marketplaces chineses.<br />
          <span style={heroH1Accent}>Decida em minutos, não em dias.</span>
        </h1>
        <p style={heroSub}>
          Matching visual, preços convertidos em BRL, impostos estimados e validação de fornecedor.
          Sem planilha manual, sem achismo.
        </p>
        <div style={searchCmd}>
          <span style={{ ...mono, fontSize: 12, color: 'var(--ink-faint)' }}>$</span>
          <input
            type="text"
            placeholder='Buscar produto, fornecedor ou número de modelo…'
            style={searchInput}
            defaultValue=""
          />
          <span style={searchKbd}>⌘ K</span>
        </div>
      </section>

      {/* ═══ EXTRATO DE SOURCING ═══ */}
      <section style={{ marginBottom: 80 }}>
        <div style={sectionLabel}>// Extrato de Sourcing</div>
        <h2 style={sectionTitle}>Cotação atual · Ring light 26cm com tripé</h2>
        <p style={sectionSub}>Amostra de uma cotação gerada pelo ArbitLens. Preços em tempo real · 12 jun 2026, 14h23 BRT.</p>

        <div style={{ border: '1px solid var(--border)', borderRadius: 4, overflow: 'hidden' }}>
          <table style={extratoTable}>
            <thead>
              <tr>
                <th style={extratoTh}>#</th>
                <th style={extratoTh}>Marketplace</th>
                <th style={extratoTh}>Fornecedor</th>
                <th style={extratoTh}>MOQ</th>
                <th style={extratoTh} align="right">Preço/un</th>
                <th style={extratoTh} align="right">Frete</th>
                <th style={extratoTh} align="right">Lead time</th>
                <th style={extratoTh} align="right">Match</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={extratoTdMono}>01</td>
                <td style={extratoTd}>1688.com</td>
                <td style={extratoTd}>深圳市光明区晟瑞照明</td>
                <td style={extratoTdMono}>5 un.</td>
                <td style={{ ...extratoTdMono, textAlign: 'right' }}>¥ 38,00</td>
                <td style={{ ...extratoTdMono, textAlign: 'right' }}>¥ 12 / kg</td>
                <td style={extratoTdMono}>15–18 dias</td>
                <td style={{ ...extratoTdMono, textAlign: 'right', color: 'var(--brand)', fontWeight: 600 }}>66%</td>
              </tr>
              <tr>
                <td style={extratoTdMono}>02</td>
                <td style={extratoTd}>Taobao</td>
                <td style={extratoTd}>广州影楼器材批发</td>
                <td style={extratoTdMono}>1 un.</td>
                <td style={{ ...extratoTdMono, textAlign: 'right' }}>¥ 52,00</td>
                <td style={{ ...extratoTdMono, textAlign: 'right' }}>¥ 14 / kg</td>
                <td style={extratoTdMono}>20–25 dias</td>
                <td style={{ ...extratoTdMono, textAlign: 'right' }}>54%</td>
              </tr>
              <tr>
                <td style={extratoTdMono}>03</td>
                <td style={extratoTd}>Alibaba</td>
                <td style={extratoTd}>Yongkang Hengwei Lighting</td>
                <td style={extratoTdMono}>100 un.</td>
                <td style={{ ...extratoTdMono, textAlign: 'right' }}>¥ 31,50</td>
                <td style={{ ...extratoTdMono, textAlign: 'right' }}>¥ 9 / kg</td>
                <td style={extratoTdMono}>25–32 dias</td>
                <td style={{ ...extratoTdMono, textAlign: 'right' }}>61%</td>
              </tr>
              <tr>
                <td style={extratoTdMono}>04</td>
                <td style={extratoTd}>DHgate</td>
                <td style={extratoTd}>Shenzhen PhotoPro Store</td>
                <td style={extratoTdMono}>1 un.</td>
                <td style={{ ...extratoTdMono, textAlign: 'right' }}>¥ 49,90</td>
                <td style={{ ...extratoTdMono, textAlign: 'right' }}>¥ 11 / kg</td>
                <td style={extratoTdMono}>15–22 dias</td>
                <td style={{ ...extratoTdMono, textAlign: 'right' }}>48%</td>
              </tr>
              <tr style={extratoTotal}>
                <td colSpan={4} style={{ ...extratoTd, color: 'rgba(255,255,255,0.7)', ...mono, fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em', borderBottom: 'none' }}>// Impostos estimados (NCM 9405.40 · II 14% + ICMS 18% + PIS/COFINS 9,25%)</td>
                <td colSpan={4} style={{ ...extratoTdMono, textAlign: 'right', color: 'white', fontSize: 16, fontWeight: 600, borderBottom: 'none' }}>+R$ 32,40 / un</td>
              </tr>
              <tr style={extratoTotal}>
                <td colSpan={4} style={{ ...extratoTd, color: 'rgba(255,255,255,0.7)', ...mono, fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em', borderBottom: 'none' }}>// Custo final médio (opção 01, 1688.com, 50 un)</td>
                <td colSpan={4} style={{ ...extratoTdMono, textAlign: 'right', color: 'var(--brand-ink)', fontSize: 20, fontWeight: 700, borderBottom: 'none', background: 'var(--brand)' }}>R$ 89,00 / un</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* ═══ MERCADO HOJE ═══ */}
      <section style={{ marginBottom: 80 }}>
        <div style={sectionLabel}>// Mercado hoje</div>
        <h2 style={sectionTitle}>Variação de preço · últimos 30 dias</h2>
        <p style={sectionSub}>Top 5 categorias com maior atividade no ArbitLens esta semana.</p>

        <div style={{ border: '1px solid var(--border)', borderRadius: 4, overflow: 'hidden' }}>
          <table style={marketTable}>
            <thead>
              <tr>
                <th style={marketTh}>Categoria</th>
                <th style={marketTh}>Produtos</th>
                <th style={marketTh}>30 dias</th>
                <th style={marketTh} align="right">Preço médio</th>
                <th style={marketTh} align="right">Variação</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={marketTd}>Áudio · microfones</td>
                <td style={{ ...marketTd, ...mono, fontSize: 12, color: 'var(--ink-muted)' }}>142</td>
                <td><Sparkline data={[42, 45, 43, 48, 52, 49, 51, 55, 53, 58, 62, 60, 65, 68, 71, 69, 72, 75, 73, 78, 82, 80, 85, 88, 86, 89, 92, 95, 91, 89]} /></td>
                <td style={{ ...marketTd, ...mono, fontSize: 12, textAlign: 'right' }}>R$ 47</td>
                <td style={{ ...marketTd, ...mono, fontSize: 12, textAlign: 'right', color: 'var(--brand)', fontWeight: 600 }}>+112%</td>
              </tr>
              <tr>
                <td style={marketTd}>Iluminação · ring light</td>
                <td style={{ ...marketTd, ...mono, fontSize: 12, color: 'var(--ink-muted)' }}>78</td>
                <td><Sparkline data={[89, 92, 88, 85, 87, 84, 82, 85, 88, 86, 83, 80, 78, 76, 74, 77, 75, 73, 71, 72, 75, 73, 74, 72, 70, 73, 71, 72, 74, 72]} /></td>
                <td style={{ ...marketTd, ...mono, fontSize: 12, textAlign: 'right' }}>R$ 89</td>
                <td style={{ ...marketTd, ...mono, fontSize: 12, textAlign: 'right', color: 'var(--mustard)', fontWeight: 600 }}>−19%</td>
              </tr>
              <tr>
                <td style={marketTd}>Eletrônicos · fones TWS</td>
                <td style={{ ...marketTd, ...mono, fontSize: 12, color: 'var(--ink-muted)' }}>213</td>
                <td><Sparkline data={[45, 47, 46, 48, 50, 52, 51, 49, 53, 55, 54, 56, 58, 57, 59, 61, 60, 62, 64, 63, 65, 67, 66, 68, 70, 69, 71, 73, 72, 74]} /></td>
                <td style={{ ...marketTd, ...mono, fontSize: 12, textAlign: 'right' }}>R$ 41</td>
                <td style={{ ...marketTd, ...mono, fontSize: 12, textAlign: 'right', color: 'var(--brand)', fontWeight: 600 }}>+64%</td>
              </tr>
              <tr>
                <td style={marketTd}>Casa · suportes celular</td>
                <td style={{ ...marketTd, ...mono, fontSize: 12, color: 'var(--ink-muted)' }}>156</td>
                <td><Sparkline data={[18, 19, 20, 22, 21, 23, 25, 24, 26, 28, 27, 29, 31, 30, 32, 34, 33, 35, 36, 38, 37, 39, 41, 40, 42, 44, 43, 45, 46, 48]} /></td>
                <td style={{ ...marketTd, ...mono, fontSize: 12, textAlign: 'right' }}>R$ 23</td>
                <td style={{ ...marketTd, ...mono, fontSize: 12, textAlign: 'right', color: 'var(--brand)', fontWeight: 600 }}>+167%</td>
              </tr>
              <tr>
                <td style={marketTd}>Beleza · skincare</td>
                <td style={{ ...marketTd, ...mono, fontSize: 12, color: 'var(--ink-muted)' }}>94</td>
                <td><Sparkline data={[78, 76, 75, 74, 73, 72, 71, 70, 69, 68, 67, 68, 67, 66, 65, 64, 65, 66, 65, 64, 63, 64, 65, 64, 63, 62, 63, 64, 65, 64]} /></td>
                <td style={{ ...marketTd, ...mono, fontSize: 12, textAlign: 'right' }}>R$ 64</td>
                <td style={{ ...marketTd, ...mono, fontSize: 12, textAlign: 'right', color: 'var(--mustard)', fontWeight: 600 }}>−18%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* ═══ CTA ═══ */}
      <section style={ctaWrap}>
        <div>
          <h2 style={ctaTitle}>Cotação semanal no seu e-mail.</h2>
          <p style={ctaSub}>Quinta-feira, 8h BRT. Top 20 oportunidades + variações de preço da semana.</p>
        </div>
        <div style={ctaRight}>
          <div>assinantes ativos: 1.347</div>
          <div>próxima edição: qui 18/jun</div>
          <div>cancelar com 1 clique</div>
        </div>
      </section>

      {/* ═══ FOOTER ═══ */}
      <footer style={footerStyle}>
        <div>1688 Intel Tecnologia Ltda · CNPJ 12.345.678/0001-90 · São Paulo, SP</div>
        <div>suporte seg–sex 9h–18h BRT · contato@1688intel.com.br</div>
        <div>v2.4.1 · build 2026.06.12 · 14:23 BRT</div>
      </footer>

    </div>
  );
}
