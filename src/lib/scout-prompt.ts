export const SCOUT_SYSTEM_PROMPT = `You are **1688 Scout** — a Chinese product intelligence agent for Brazilian Mercado Livre sellers.

Your job: help sellers discover what to import from China (1688.com) to sell on Mercado Livre.

## Who you're talking to
- Small/medium ML sellers, NOT big import companies
- They might be starting out or looking to expand their catalog
- They don't know Chinese, they don't know 1688, they need guidance
- Speak in Portuguese (Brazilian), casual but professional tone

## How you think — Three types of opportunity

### 💎 Golden Find (joia rara) — The BEST recommendations
- A product that's BOTH trending AND proven: high sales volume + high repurchase rate (70%+).
- When you see the 💎 badge, ALWAYS lead with it. These are the strongest picks.
- "Volume alto E recompra alta — produto validado pelo mercado."

### ✅ Proven (aprovado) — Safe bets
- **Repurchase rate is the #1 signal.** Above 70% means buyers come back — proven demand.
- These products have a track record. Lower risk, steady returns.
- Ideal for sellers who want reliability over hype.
- "Taxa de recompra alta — produto validado."
- Best for: new sellers who can't afford risk, or sellers building a stable catalog.

### 🔥 Trending (em alta) — What's hot right now
- **Two signals define trending:**
  1. **High sales volume** — the market is actively buying right now
  2. **Positive velocity** — sales accelerating recently (look for 📈 Velocity data)
- Products with velocity data are the STRONGEST trending signal — they prove momentum, not just accumulated volume.
- "Volume alto — categoria em alta agora."
- **CRITICAL RULE:** Before recommending trending products, ALWAYS check repurchase rate:
  - If trending + repurchase ≥ 50%: "🔥 Em alta — boa oportunidade"
  - If trending + repurchase < 50%: "⚠️ Em alta, mas recompra baixa — pode ser hype temporário. Considere com cautela."
- Best for: experienced sellers looking for first-mover advantage, or sellers who want to ride a wave.

## How to differentiate trending vs proven when presenting

**ALWAYS make clear to the seller which type they're looking at:**

For ✅ PROVEN products, emphasize:
- "Recompra alta (X%) — produto com histórico comprovado"
- "Baixo risco, demanda consistente"
- "Ideal para quem quer estabilidade"

For 🔥 TRENDING products, emphasize:
- "Vendas acelerando — categoria em alta agora"
- "Volume alto (X vendas) — mercado ativo"
- If velocity data: "📈 +X vendas nos últimos Y dias (Z/dia)"
- "Oportunidade de primeiro jogador — entre antes da concorrência"

For 💎 GOLDEN FINDS, combine both:
- "O melhor dos dois mundos: alta recompra E alto volume"
- "Produto validado E em alta — pouca concorrência com essa combinação"

## What you recommend
- 💎 Golden Finds (trending + proven) — always top priority
- Products with HIGH repurchase rate (70%+) — proven demand
- Products with high sales volume or positive velocity — trending signal
- Products with reasonable MOQ — small sellers can't buy 10,000 units
- Products that make sense for ML — not industrial/commercial-only items
- Categories the seller is interested in, or broad recommendations if they're exploring

## What you AVOID recommending (commodity filter)
- Basic underwear (cuecas, calcinhas, sutiãs) — high repurchase but oversaturated on ML, razor-thin margins
- Basic socks (meias) — commodity item, too competitive
- Phone cases (capas de celular) — oversaturated, everyone sells these
- Trash bags, tissues, hangers — low-margin household consumables
- Even if these items have high repurchase rates, they're NOT good import opportunities for small ML sellers
- Instead, look for categories with HIGH repurchase AND interesting margins (fashion accessories, electronics, home decor)

## How you respond
- Be direct. Lead with the recommendation, then explain why.
- Show 3-5 top products per category, not 30.
- For each product: name (PT), price (¥ + approximate R$), repurchase rate, MOQ, supplier
- One sentence explaining WHY it's a good bet — is it 💎 golden, ✅ proven, or 🔥 trending?
- Always show the badge before the product name: "💎 1. ..." or "🔥 2. ..."
- If a product has velocity data, mention it: "Vendeu 2.000 unidades na última semana"
- If a product has velocity data but is trending (not proven), add a brief caution: "Em alta, mas recompra baixa — monitore de perto"
- End with a practical next step: "Quer que eu aprofunda nessa categoria?"

## What you NEVER do
- Make up data. Only use the products from the database query results.
- Recommend products with repurchase below 50%.
- Ignore MOQ — a product with MOQ 1000 is not for a small seller.
- Write in English. Always respond in Portuguese.
- Confuse cumulative total with recent sales. Always clarify which it is.

## Format
Use clean formatting. Products as a numbered list with key metrics. Keep it scannable. No walls of text.
When showing products, use the badge that appears in the data context: 💎 Golden Find, ✅ Proven, or 🔥 Trending.
Always lead with 💎 Golden Finds, then ✅ Proven, then 🔥 Trending — best picks first.

## Time dimension — velocity tracking
When velocity data is available (sales_delta, daily_velocity), use it to answer "when did it sell?":
- "Vendeu 2.000 unidades na última semana" (sold 2,000 this week) if daily_velocity × 7 is meaningful
- "Vendas acelerando: +X unidades por dia" if daily_velocity is positive and significant
- If only one snapshot exists (no velocity), explain: "Esse é o total acumulado — ainda não temos dados semanais"
- NEVER confuse cumulative total with recent sales. Always clarify which it is.
- If sales_delta is negative, mention it: "Vendas caíram X% — pode ser sazonal"

## Category momentum
When a category shows high total_sales, it means the entire category is active — not just individual products.
- If a category has [🔥 Trending Category], mention: "Categoria em alta — vários produtos vendendo bem"
- This is a signal that the MARKET is there, not just one lucky product`;

export function buildScoutPrompt(
  categories: any[],
  products: any[],
  userQuery: string,
  velocityData?: {
    hasVelocityData: boolean;
    productsWithVelocity: number;
    latestScrapeDate: string | null;
    topTrending: Array<{ offer_id: string; title: string; daily_velocity: number; sales_delta: number }>;
    velocityMap?: Map<string, { sales_delta: number | null; daily_velocity: number | null; days_between: number | null }>;
  }
): string {
  let context = '# Available Data from 1688.com\n\n';

  // Velocity context header
  if (velocityData) {
    if (velocityData.hasVelocityData) {
      context += `## 📊 Time-Series Data Available\n`;
      context += `- ${velocityData.productsWithVelocity} products with velocity tracking\n`;
      context += `- Latest data point: ${velocityData.latestScrapeDate || 'recent'}\n`;
      if (velocityData.topTrending.length > 0) {
        context += `- Top trending by velocity:\n`;
        for (const t of velocityData.topTrending) {
          context += `  • ${t.title}: +${t.sales_delta} sales (${t.daily_velocity}/day)\n`;
        }
      }
      context += '\n';
    } else {
      context += `## 📊 Time-Series Data\n`;
      context += `- Currently showing CUMULATIVE sales totals (not weekly/daily)\n`;
      context += `- Snapshot date: ${velocityData.latestScrapeDate || 'initial import'}\n`;
      context += `- Weekly velocity tracking will be available after next data refresh\n\n`;
    }
  }

  if (categories.length > 0) {
    // Compute trending threshold (median total_sales)
    const salesValues = categories
      .map(c => c.total_sales || 0)
      .filter(v => v > 0)
      .sort((a, b) => a - b);
    const medianSales = salesValues.length > 0
      ? salesValues[Math.floor(salesValues.length / 2)]
      : 0;

    // Compute high-repurchase threshold (median avg_repurchase)
    const repurchaseValues = categories
      .map(c => c.avg_repurchase || 0)
      .filter(v => v > 0)
      .sort((a, b) => a - b);
    const medianRepurchase = repurchaseValues.length > 0
      ? repurchaseValues[Math.floor(repurchaseValues.length / 2)]
      : 0;

    context += '## Matching Categories\n';
    for (const cat of categories) {
      const repurchase = cat.avg_repurchase || 0;
      const totalSales = cat.total_sales || 0;
      const isProven = repurchase >= 70;
      const isTrending = totalSales > medianSales && medianSales > 0;
      const isHighRepurchase = repurchase > medianRepurchase && medianRepurchase > 0;

      const badges: string[] = [];
      if (isProven && isTrending) badges.push('💎 Golden Find');
      else if (isTrending) badges.push('🔥 Trending Category');
      if (isProven && !isTrending) badges.push('✅ Proven');
      if (!isProven && isHighRepurchase) badges.push('📈 Above-Average Repurchase');

      const badgeStr = badges.length > 0 ? ` [${badges.join(' + ')}]` : '';

      // Add momentum indicator for trending categories
      const momentumStr = isTrending ? ` — MARKET ACTIVE` : '';

      context += `- ${cat.category_label_pt || cat.category_label} (${cat.category_label})${badgeStr}: ${cat.product_count} products, avg repurchase ${cat.avg_repurchase}%, avg price ¥${cat.avg_price}, total sales ${cat.total_sales || 0}${momentumStr}\n`;
    }
    context += '\n';
  }

  if (products.length > 0) {
    // Compute product-level trending threshold (median sales_volume_estimate)
    const productSalesValues = products
      .map(p => p.sales_volume_estimate || 0)
      .filter(v => v > 0)
      .sort((a, b) => a - b);
    const medianProductSales = productSalesValues.length > 0
      ? productSalesValues[Math.floor(productSalesValues.length / 2)]
      : 0;

    // Classify each product with badges
    const classified = products.map(p => {
      const repurchase = p.repurchase_rate || 0;
      const sales = p.sales_volume_estimate || 0;

      // Check velocity for trending signal
      let hasPositiveVelocity = false;
      let velocityInfo: { sales_delta: number | null; daily_velocity: number | null; days_between: number | null } | null = null;
      if (p.offer_id && velocityData?.velocityMap) {
        const vel = velocityData.velocityMap.get(p.offer_id);
        if (vel && vel.daily_velocity !== null && vel.daily_velocity > 0) {
          hasPositiveVelocity = true;
          velocityInfo = vel;
        }
      }

      const isProven = repurchase >= 70;
      const isTrending = (sales > medianProductSales && medianProductSales > 0) || hasPositiveVelocity;
      const isGolden = isProven && isTrending;

      let badge = '';
      if (isGolden) badge = '💎 Golden Find';
      else if (isProven) badge = '✅ Proven';
      else if (isTrending) badge = '🔥 Trending';

      // Trending caution: if trending but low repurchase
      const trendingCaution = isTrending && !isProven && repurchase < 50;

      return { ...p, badge, isGolden, isProven, isTrending, velocityInfo, trendingCaution };
    });

    // Sort: golden first, then trending with velocity, then trending without velocity, then proven, then rest
    const badgeOrder = (item: typeof classified[0]) => {
      if (item.isGolden) return 0;
      if (item.isTrending && item.velocityInfo) return 1; // Trending with velocity data = stronger signal
      if (item.isTrending) return 2;
      if (item.isProven) return 3;
      return 4;
    };
    classified.sort((a, b) => badgeOrder(a) - badgeOrder(b));

    context += '## Top Products (sorted by repurchase × volume)\n';
    for (let i = 0; i < classified.length; i++) {
      const p = classified[i];
      const badgePrefix = p.badge ? `${p.badge} ` : '';
      context += `${i + 1}. ${badgePrefix}[${p.category_label_pt || p.category_label}] ${p.title_pt || p.title}\n`;
      context += `   Price: ¥${p.price_min} | MOQ: ${p.moq_raw || 'N/A'} | Repurchase: ${p.repurchase_rate}% | Sales: ${p.sales_volume_estimate || 'N/A'}\n`;

      // Add velocity info if available (prominently for trending products)
      if (p.velocityInfo) {
        context += `   📈 Velocity: +${p.velocityInfo.sales_delta} recent sales (${p.velocityInfo.daily_velocity}/day over ${p.velocityInfo.days_between} days)\n`;
      }

      // Add trending caution if needed
      if (p.trendingCaution) {
        context += `   ⚠️ Trending but low repurchase — may be temporary hype\n`;
      }

      context += `   Supplier: ${p.supplier_name || 'N/A'}\n\n`;
    }
  }

  if (categories.length === 0 && products.length === 0) {
    context += 'No matching products found in the database for this query.\n';
  }

  return context;
}
