'use client'

import { useEffect, useState } from 'react'

interface CSVButtonProps {
  products: any[]
  filename?: string
  headers?: string[]
  label?: string
}

const DEFAULT_HEADERS = ['product_name', 'platform', 'price_brl', 'price_low', 'price_currency', 'monthly_sales', 'seller_name', 'moq', 'product_url']

function CSVButton({ products, filename = 'arbitlens-results.csv', headers, label }: CSVButtonProps) {
  const [url, setUrl] = useState<string>('#')
  const cols = headers || DEFAULT_HEADERS

  useEffect(() => {
    const headerRow = cols.join(',')
    const rows = products.map(p =>
      cols.map(h => {
        const val = p[h];
        return `"${String(val ?? '').replace(/"/g, '""')}"`;
      }).join(',')
    )
    const csv = '\ufeff' + headerRow + '\n' + rows.join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
    setUrl(URL.createObjectURL(blob))
  }, [products, cols])

  return (
    <a
      href={url}
      download={filename}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 6,
        padding: '6px 14px', fontSize: 12, fontWeight: 600,
        background: 'var(--warm-surface, #fcfaf7)',
        border: '1px solid var(--border, #e7e5e4)',
        borderRadius: 999, cursor: 'pointer',
        color: 'var(--ink-muted, #57534e)',
        textDecoration: 'none',
        transition: 'all 0.12s',
      }}
      onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--ink-soft, #292524)'; e.currentTarget.style.color = 'var(--ink)'; }}
      onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--ink-muted)'; }}
    >
      {label || `📥 Exportar CSV (${products.length})`}
    </a>
  )
}

export { CSVButton }
