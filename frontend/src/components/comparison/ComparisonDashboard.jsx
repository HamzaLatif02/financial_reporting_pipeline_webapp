import { Eye, Download, RefreshCw } from 'lucide-react'
import ComparisonMetricsTable from './ComparisonMetricsTable'
import ComparisonChartViewer  from './ComparisonChartViewer'
import { getComparisonViewUrl, getComparisonDownloadUrl } from '../../api/client'

function correlationBorderColor(label) {
  const l = (label || '').toLowerCase()
  if (l.includes('strong positive'))    return 'var(--positive)'
  if (l.includes('positive'))           return '#2563EB'
  if (l.includes('strong negative'))    return 'var(--negative)'
  if (l.includes('negative'))           return '#F97316'
  return 'var(--border-default)'
}

function correlationTextColor(label) {
  const l = (label || '').toLowerCase()
  if (l.includes('positive'))  return 'var(--positive)'
  if (l.includes('negative'))  return 'var(--negative)'
  return 'var(--text-2)'
}

export default function ComparisonDashboard({ result, onReset }) {
  const {
    symbol_a, symbol_b, name_a, name_b,
    correlation, metrics, overlap_days,
    chart_urls = [],
  } = result

  const corr  = correlation || {}
  const label = corr.label || ''
  const rVal  = corr.value

  const viewUrl     = getComparisonViewUrl(symbol_a, symbol_b)
  const downloadUrl = getComparisonDownloadUrl(symbol_a, symbol_b)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

      {/* ── Header bar ───────────────────────────────────────────────────── */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        flexWrap: 'wrap', gap: 12,
        padding: '16px 20px',
        background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--r-lg)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <span style={{
            fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '16px',
            color: '#2563EB',
          }}>
            {name_a}
          </span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: '#2563EB', opacity: 0.7 }}>
            ({symbol_a})
          </span>
          <span style={{ fontSize: '13px', color: 'var(--text-3)', margin: '0 4px' }}>vs</span>
          <span style={{
            fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '16px',
            color: '#EA580C',
          }}>
            {name_b}
          </span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: '#EA580C', opacity: 0.7 }}>
            ({symbol_b})
          </span>
          {result.period && (
            <span className="fp-badge fp-badge-neutral" style={{ marginLeft: 4 }}>{result.period}</span>
          )}
          {result.interval && (
            <span className="fp-badge fp-badge-neutral">{result.interval}</span>
          )}
        </div>
        <button
          onClick={onReset}
          className="fp-btn-ghost"
          style={{ padding: '7px 14px', gap: 6, fontSize: '13px' }}
        >
          <RefreshCw size={13} />
          New comparison
        </button>
      </div>

      {/* ── Correlation card ─────────────────────────────────────────────── */}
      <div style={{
        padding: '24px 28px',
        background: 'var(--bg-surface)',
        border: `1.5px solid ${correlationBorderColor(label)}`,
        borderRadius: 'var(--r-lg)',
        display: 'flex', alignItems: 'center', gap: 24, flexWrap: 'wrap',
      }}>
        <div>
          <div style={{
            fontSize: '11px', fontWeight: 600, letterSpacing: '0.07em',
            textTransform: 'uppercase', color: 'var(--text-3)', marginBottom: 6,
          }}>
            Correlation
          </div>
          <div style={{
            fontFamily: 'var(--font-display)', fontWeight: 800,
            fontSize: '40px', lineHeight: 1,
            color: correlationTextColor(label),
          }}>
            {rVal != null ? `r = ${rVal}` : '—'}
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <span style={{
            display: 'inline-block',
            padding: '4px 14px', borderRadius: 'var(--r-lg)',
            background: `${correlationBorderColor(label)}22`,
            border: `1px solid ${correlationBorderColor(label)}55`,
            fontSize: '12px', fontWeight: 600,
            color: correlationTextColor(label),
          }}>
            {label || '—'}
          </span>
          <span style={{ fontSize: '12px', color: 'var(--text-3)' }}>
            Based on {overlap_days?.toLocaleString() ?? '—'} overlapping trading days
          </span>
        </div>
      </div>

      {/* ── Metrics + Charts ─────────────────────────────────────────────── */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(0, 2fr) minmax(0, 3fr)',
        gap: 20,
      }}
        className="fp-comparison-grid"
      >
        {/* Metrics table */}
        <div className="fp-card" style={{ padding: '20px' }}>
          <div style={{
            fontSize: '11px', fontWeight: 600, letterSpacing: '0.07em',
            textTransform: 'uppercase', color: 'var(--text-3)', marginBottom: 14,
          }}>
            Performance Metrics
          </div>
          <ComparisonMetricsTable
            metrics={metrics}
            symbol_a={symbol_a}
            symbol_b={symbol_b}
            name_a={name_a}
            name_b={name_b}
          />
        </div>

        {/* Chart viewer */}
        <ComparisonChartViewer
          chart_urls={chart_urls}
          symbol_a={symbol_a}
          symbol_b={symbol_b}
        />
      </div>

      {/* ── Report download ──────────────────────────────────────────────── */}
      <div style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12,
        padding: '20px',
        background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--r-lg)',
      }}>
        <div style={{
          fontSize: '13px', fontWeight: 600, color: 'var(--text-2)',
        }}>
          Combined Comparison Report
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <a
            href={viewUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="fp-btn-primary"
            style={{ padding: '10px 20px', textDecoration: 'none' }}
          >
            <Eye size={14} />
            View Report
          </a>
          <a
            href={downloadUrl}
            download={`${symbol_a}_vs_${symbol_b}_comparison_report.pdf`}
            className="fp-btn-accent"
            style={{ padding: '10px 20px', textDecoration: 'none' }}
          >
            <Download size={14} />
            Download Report
          </a>
        </div>
        <div style={{ fontSize: '11px', color: 'var(--text-4)' }}>
          Not financial advice. Data sourced from Yahoo Finance.
        </div>
      </div>
    </div>
  )
}
