import { Trophy } from 'lucide-react'

const METRIC_LABELS = {
  total_return_pct:      'Total Return',
  annualised_return_pct: 'Annualised Return',
  volatility_pct:        'Volatility (Ann.)',
  sharpe_ratio:          'Sharpe Ratio',
  max_drawdown_pct:      'Max Drawdown',
  best_day_pct:          'Best Day',
  worst_day_pct:         'Worst Day',
}

const PCT_KEYS = new Set([
  'total_return_pct', 'annualised_return_pct', 'volatility_pct',
  'max_drawdown_pct', 'best_day_pct', 'worst_day_pct',
])

function fmt(key, val) {
  if (val == null) return 'N/A'
  if (PCT_KEYS.has(key)) return `${val >= 0 ? '+' : ''}${val.toFixed(2)}%`
  if (key === 'sharpe_ratio') return val.toFixed(2)
  return String(val)
}

function valColor(key, val) {
  if (val == null) return 'var(--text-1)'
  if (PCT_KEYS.has(key)) return val >= 0 ? 'var(--positive)' : 'var(--negative)'
  if (key === 'sharpe_ratio') return val >= 0 ? 'var(--positive)' : 'var(--negative)'
  return 'var(--text-1)'
}

export default function ComparisonMetricsTable({ metrics, symbol_a, symbol_b }) {
  if (!metrics) return null

  const rows = Object.entries(METRIC_LABELS)
  const wins_a = rows.filter(([k]) => metrics[k]?.winner === 'a').length
  const wins_b = rows.filter(([k]) => metrics[k]?.winner === 'b').length
  const total  = rows.length

  const thStyle = (color) => ({
    padding: '10px 12px',
    fontFamily: 'var(--font-body)', fontWeight: 700,
    fontSize: '11px', letterSpacing: '0.04em',
    textTransform: 'uppercase', color,
    textAlign: 'center', whiteSpace: 'nowrap',
  })

  return (
    <div>
      <div style={{ overflowX: 'auto' }}>
        <table style={{
          width: '100%', borderCollapse: 'collapse',
          fontSize: '13px',
        }}>
          <thead>
            <tr style={{ background: 'var(--bg-surface)' }}>
              <th style={{ ...thStyle('var(--text-2)'), textAlign: 'left' }}>Metric</th>
              <th style={thStyle('#2563EB')}>{symbol_a}</th>
              <th style={thStyle('#EA580C')}>{symbol_b}</th>
              <th style={thStyle('var(--text-3)')}>Winner</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(([key, label], idx) => {
              const data   = metrics[key] || {}
              const val_a  = data.a
              const val_b  = data.b
              const winner = data.winner

              const rowBg = idx % 2 === 0 ? 'var(--bg-raised)' : 'var(--bg-base)'

              return (
                <tr key={key} style={{ background: rowBg }}>
                  <td style={{
                    padding: '9px 12px',
                    color: 'var(--text-2)', fontWeight: 500,
                    borderBottom: '1px solid var(--border-subtle)',
                    whiteSpace: 'nowrap',
                  }}>
                    {label}
                  </td>
                  <td style={{
                    padding: '9px 12px', textAlign: 'center',
                    fontFamily: 'var(--font-mono)', fontSize: '12px',
                    fontWeight: winner === 'a' ? 700 : 400,
                    color: valColor(key, val_a),
                    borderBottom: '1px solid var(--border-subtle)',
                  }}>
                    {fmt(key, val_a)}
                  </td>
                  <td style={{
                    padding: '9px 12px', textAlign: 'center',
                    fontFamily: 'var(--font-mono)', fontSize: '12px',
                    fontWeight: winner === 'b' ? 700 : 400,
                    color: valColor(key, val_b),
                    borderBottom: '1px solid var(--border-subtle)',
                  }}>
                    {fmt(key, val_b)}
                  </td>
                  <td style={{
                    padding: '9px 12px', textAlign: 'center',
                    borderBottom: '1px solid var(--border-subtle)',
                  }}>
                    {winner === 'a' && (
                      <span style={{
                        display: 'inline-flex', alignItems: 'center', gap: 4,
                        fontWeight: 700, fontSize: '12px', color: 'var(--positive)',
                      }}>
                        <Trophy size={11} />
                        {symbol_a}
                      </span>
                    )}
                    {winner === 'b' && (
                      <span style={{
                        display: 'inline-flex', alignItems: 'center', gap: 4,
                        fontWeight: 700, fontSize: '12px', color: 'var(--positive)',
                      }}>
                        <Trophy size={11} />
                        {symbol_b}
                      </span>
                    )}
                    {winner === 'tie' && (
                      <span style={{ fontSize: '12px', color: 'var(--text-3)' }}>Tie</span>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Score summary */}
      <div style={{
        marginTop: 12, padding: '10px 14px',
        background: 'var(--bg-raised)', borderRadius: 'var(--r-md)',
        border: '1px solid var(--border-default)',
        display: 'flex', gap: 16, flexWrap: 'wrap', justifyContent: 'center',
        fontSize: '13px',
      }}>
        <span style={{ color: wins_a >= wins_b ? 'var(--positive)' : 'var(--text-2)', fontWeight: wins_a >= wins_b ? 700 : 400 }}>
          {symbol_a}: {wins_a}/{total}
        </span>
        <span style={{ color: 'var(--text-4)' }}>·</span>
        <span style={{ color: wins_b >= wins_a ? 'var(--positive)' : 'var(--text-2)', fontWeight: wins_b >= wins_a ? 700 : 400 }}>
          {symbol_b}: {wins_b}/{total}
        </span>
        {wins_a === wins_b && (
          <span style={{ color: 'var(--text-3)', fontSize: '12px' }}>(Tied)</span>
        )}
      </div>
    </div>
  )
}
