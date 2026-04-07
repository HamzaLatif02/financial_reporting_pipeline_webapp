import { useState } from 'react'
import { ExternalLink, ImageOff } from 'lucide-react'

function labelFromUrl(url, symbol_a, symbol_b) {
  const filename = url.split('/').pop() || ''
  // Strip "CMP_{a}_vs_{b}_" prefix and ".png" suffix
  const prefix = `CMP_${symbol_a}_vs_${symbol_b}_`
  let stem = filename.replace(/\.[^.]+$/, '')
  if (stem.startsWith(prefix)) stem = stem.slice(prefix.length)
  // Title-case with spaces
  return stem.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
}

function ChartImage({ url, label }) {
  const [loaded,  setLoaded]  = useState(false)
  const [errored, setErrored] = useState(false)

  if (errored) {
    return (
      <div style={{
        background: 'var(--bg-raised)', border: '1px solid var(--border-default)',
        borderRadius: 'var(--r-lg)', padding: '56px 24px',
        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10,
        color: 'var(--text-3)', textAlign: 'center',
      }}>
        <ImageOff size={28} color="var(--text-4)" />
        <p style={{ margin: 0, fontSize: '13px', color: 'var(--text-2)' }}>{label}</p>
        <p style={{ margin: 0, fontSize: '12px' }}>Chart unavailable</p>
      </div>
    )
  }

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      {!loaded && (
        <div className="fp-skeleton" style={{ position: 'absolute', inset: 0, minHeight: 260, borderRadius: 'var(--r-lg)' }} />
      )}
      <img
        src={url}
        alt={label}
        onLoad={() => setLoaded(true)}
        onError={() => setErrored(true)}
        style={{
          width: '100%', borderRadius: 'var(--r-lg)',
          border: '1px solid var(--border-default)',
          display: 'block',
          opacity: loaded ? 1 : 0,
          transition: 'opacity 0.3s ease',
          boxShadow: 'var(--shadow-md)',
        }}
      />
    </div>
  )
}

export default function ComparisonChartViewer({ chart_urls = [], symbol_a, symbol_b }) {
  const [activeIdx, setActiveIdx] = useState(0)

  if (chart_urls.length === 0) {
    return (
      <div className="fp-card" style={{ padding: '48px', textAlign: 'center', fontSize: '13px', color: 'var(--text-3)' }}>
        No comparison charts available.
      </div>
    )
  }

  const activeUrl = chart_urls[activeIdx]

  return (
    <div className="fp-card" style={{ overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>

      {/* Tab bar */}
      <div className="fp-chart-tabs" style={{ paddingTop: 4, paddingLeft: 4, paddingRight: 4 }}>
        {chart_urls.map((url, idx) => {
          const label = labelFromUrl(url, symbol_a, symbol_b)
          return (
            <button
              key={url}
              onClick={() => setActiveIdx(idx)}
              className={`fp-chart-tab ${idx === activeIdx ? 'active' : ''}`}
            >
              {label}
            </button>
          )
        })}
      </div>

      {/* Colour legend */}
      <div style={{
        display: 'flex', gap: 16, padding: '10px 20px 0',
        alignItems: 'center',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '12px', color: 'var(--text-2)' }}>
          <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#2563EB', flexShrink: 0 }} />
          {symbol_a}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '12px', color: 'var(--text-2)' }}>
          <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#EA580C', flexShrink: 0 }} />
          {symbol_b}
        </div>
      </div>

      {/* Chart */}
      <div style={{ padding: '16px 20px' }}>
        <ChartImage
          key={activeUrl}
          url={activeUrl}
          label={labelFromUrl(activeUrl, symbol_a, symbol_b)}
        />
      </div>

      {/* Open full size */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '0 20px 16px' }}>
        <a
          href={activeUrl}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 5,
            fontSize: '12px', color: 'var(--text-3)',
            textDecoration: 'none', padding: '4px 6px', borderRadius: 'var(--r-sm)',
            transition: 'color var(--t-fast) var(--ease)',
          }}
          onMouseEnter={e => e.currentTarget.style.color = 'var(--accent)'}
          onMouseLeave={e => e.currentTarget.style.color = 'var(--text-3)'}
        >
          <ExternalLink size={12} />
          Open full size
        </a>
      </div>
    </div>
  )
}
