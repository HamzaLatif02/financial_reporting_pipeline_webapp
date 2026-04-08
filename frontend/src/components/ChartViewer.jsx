import { useState } from 'react'
import { ExternalLink, ImageOff } from 'lucide-react'
import { getChartUrl } from '../api/client'

const LABEL_MAP = {
  candlestick:         'Candlestick',
  price_ma:            'Price & MA',
  cumulative_return:   'Cum. Return',
  drawdown:            'Drawdown',
  monthly_returns:     'Monthly Returns',
  summary_stats_table: 'Summary Table',
}

function stemFromFilename(filename, symbol) {
  let stem = filename.replace(/\.[^.]+$/, '')
  if (symbol) stem = stem.replace(new RegExp(`^${symbol}_`, 'i'), '')
  return stem
}

function labelFromStem(stem) {
  if (LABEL_MAP[stem]) return LABEL_MAP[stem]
  return stem.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
}

function ChartImage({ filename, label }) {
  const [loaded,  setLoaded]  = useState(false)
  const [errored, setErrored] = useState(false)
  const url = getChartUrl(filename)

  if (errored) {
    return (
      <div style={{
        background: 'var(--bg-raised)', border: '1px solid var(--border-default)',
        borderRadius: 'var(--r-lg)', padding: '56px 24px',
        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10,
        color: 'var(--text-3)', textAlign: 'center',
      }}>
        <ImageOff size={28} color="var(--text-4)" />
        <p style={{ margin: 0, fontWeight: 500, color: 'var(--text-2)', fontSize: '13px' }}>{label}</p>
        <p style={{ margin: 0, fontSize: '12px' }}>Chart unavailable</p>
      </div>
    )
  }

  return (
    <div style={{ position: 'relative', width: '100%', overflow: 'hidden' }}>
      {!loaded && (
        <div className="fp-skeleton" style={{ position: 'absolute', inset: 0, minHeight: 280, borderRadius: 'var(--r-lg)' }} />
      )}
      <img
        src={url}
        alt={label}
        onLoad={() => setLoaded(true)}
        onError={() => setErrored(true)}
        style={{
          width: '100%', maxWidth: '100%', borderRadius: 'var(--r-lg)',
          border: '1px solid var(--border-default)',
          display: 'block',
          transition: 'opacity 0.3s ease',
          opacity: loaded ? 1 : 0,
          boxShadow: 'var(--shadow-md)',
        }}
      />
    </div>
  )
}

export default function ChartViewer({ symbol, charts = [] }) {
  const [activeIdx, setActiveIdx] = useState(0)

  if (charts.length === 0) {
    return (
      <div className="fp-card" style={{
        padding: '48px', textAlign: 'center', fontSize: '13px', color: 'var(--text-3)',
      }}>
        No charts available.
      </div>
    )
  }

  const activeFilename = charts[activeIdx]
  const activeUrl      = getChartUrl(activeFilename)

  return (
    <div className="fp-card" style={{ overflow: 'hidden', display: 'flex', flexDirection: 'column', minWidth: 0, width: '100%' }}>

      {/* ── Tab bar ────────────────────────────────────────────────────── */}
      <div className="fp-chart-tabs" style={{ paddingTop: 4, paddingLeft: 4, paddingRight: 4 }}>
        {charts.map((filename, idx) => {
          const stem  = stemFromFilename(filename, symbol)
          const label = labelFromStem(stem)
          return (
            <button
              key={filename}
              onClick={() => setActiveIdx(idx)}
              className={`fp-chart-tab ${idx === activeIdx ? 'active' : ''}`}
            >
              {label}
            </button>
          )
        })}
      </div>

      {/* ── Chart image ────────────────────────────────────────────────── */}
      <div style={{ padding: '20px' }}>
        <ChartImage
          key={activeFilename}
          filename={activeFilename}
          label={labelFromStem(stemFromFilename(activeFilename, symbol))}
        />
      </div>

      {/* ── Open full size ─────────────────────────────────────────────── */}
      <div style={{
        display: 'flex', justifyContent: 'flex-end',
        padding: '0 20px 16px',
      }}>
        <a
          href={activeUrl}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 5,
            fontSize: '12px', color: 'var(--text-3)',
            textDecoration: 'none',
            transition: 'color var(--t-fast) var(--ease)',
            padding: '4px 6px', borderRadius: 'var(--r-sm)',
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
