function formatDuration(startStr, endStr) {
  const start = new Date(startStr)
  const end   = new Date(endStr)
  const days  = Math.round((end - start) / (1000 * 60 * 60 * 24))
  if (days <= 0) return null
  const years  = Math.floor(days / 365)
  const months = Math.floor((days % 365) / 30)
  if (days >= 365) {
    return `${years} year${years !== 1 ? 's' : ''}, ${months} month${months !== 1 ? 's' : ''} (${days.toLocaleString()} days)`
  }
  if (days >= 30) {
    return `${months} month${months !== 1 ? 's' : ''} (${days.toLocaleString()} days)`
  }
  return `${days} days`
}

export default function DateRangePicker({
  startDate, endDate, onStartChange, onEndChange, interval, errors = {},
}) {
  const today    = new Date().toISOString().split('T')[0]
  const minStart = '1970-01-01'
  const minEnd   = startDate
    ? new Date(new Date(startDate).getTime() + 86400000).toISOString().split('T')[0]
    : minStart

  const duration = startDate && endDate ? formatDuration(startDate, endDate) : null

  const start = new Date(startDate)
  const end   = new Date(endDate)
  const rangeDays = startDate && endDate
    ? Math.round((end - start) / (1000 * 60 * 60 * 24))
    : 0

  const warnWeekly  = interval === '1wk'  && rangeDays > 0 && rangeDays < 28
  const warnMonthly = interval === '1mo'  && rangeDays > 0 && rangeDays < 90

  const inputStyle = {
    background: 'var(--bg-raised)',
    border: '1px solid var(--border-default)',
    borderRadius: 'var(--r-md)',
    color: 'var(--text-1)',
    fontFamily: 'var(--font-mono)',
    fontSize: '13px',
    padding: '8px 12px',
    width: '100%',
    outline: 'none',
    colorScheme: 'dark',
    transition: 'border-color var(--t-fast) var(--ease)',
  }

  return (
    <div style={{
      marginTop: 12,
      background: 'var(--bg-raised)',
      border: '1px solid var(--border-default)',
      borderRadius: 'var(--r-lg)',
      padding: '16px',
      display: 'flex', flexDirection: 'column', gap: 12,
    }}>
      {/* Date inputs row */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr auto 1fr',
        gap: 10,
        alignItems: 'start',
      }}
        className="fp-date-grid"
      >
        {/* Start date */}
        <div>
          <div style={{
            fontSize: '10px', fontWeight: 600, letterSpacing: '0.06em',
            textTransform: 'uppercase', color: 'var(--text-3)', marginBottom: 5,
          }}>
            Start date
          </div>
          <input
            type="date"
            value={startDate || ''}
            min={minStart}
            max={today}
            onChange={e => onStartChange(e.target.value)}
            style={{
              ...inputStyle,
              borderColor: errors.start ? 'var(--negative)' : 'var(--border-default)',
            }}
            onFocus={e => e.target.style.borderColor = errors.start ? 'var(--negative)' : 'var(--accent)'}
            onBlur={e => e.target.style.borderColor = errors.start ? 'var(--negative)' : 'var(--border-default)'}
          />
          {errors.start && (
            <p style={{ margin: '4px 0 0', fontSize: '11px', color: 'var(--negative)' }}>
              {errors.start}
            </p>
          )}
        </div>

        {/* Separator */}
        <div style={{
          fontSize: '12px', color: 'var(--text-3)',
          paddingTop: 26, textAlign: 'center',
          whiteSpace: 'nowrap',
        }}>
          to
        </div>

        {/* End date */}
        <div>
          <div style={{
            fontSize: '10px', fontWeight: 600, letterSpacing: '0.06em',
            textTransform: 'uppercase', color: 'var(--text-3)', marginBottom: 5,
          }}>
            End date
          </div>
          <input
            type="date"
            value={endDate || ''}
            min={minEnd}
            max={today}
            onChange={e => onEndChange(e.target.value)}
            style={{
              ...inputStyle,
              borderColor: errors.end ? 'var(--negative)' : 'var(--border-default)',
            }}
            onFocus={e => e.target.style.borderColor = errors.end ? 'var(--negative)' : 'var(--accent)'}
            onBlur={e => e.target.style.borderColor = errors.end ? 'var(--negative)' : 'var(--border-default)'}
          />
          {errors.end && (
            <p style={{ margin: '4px 0 0', fontSize: '11px', color: 'var(--negative)' }}>
              {errors.end}
            </p>
          )}
        </div>
      </div>

      {/* Duration summary */}
      {duration && !errors.end && (
        <div style={{
          fontSize: '12px', color: 'var(--text-2)',
          borderTop: '1px solid var(--border-subtle)',
          paddingTop: 10,
        }}>
          Selected range: <span style={{ color: 'var(--accent)', fontWeight: 500 }}>{duration}</span>
        </div>
      )}

      {/* Interval warnings */}
      {(warnWeekly || warnMonthly) && (
        <div style={{
          display: 'flex', alignItems: 'flex-start', gap: 7,
          padding: '8px 12px',
          background: 'rgba(245,158,11,0.08)',
          border: '1px solid rgba(245,158,11,0.25)',
          borderRadius: 'var(--r-md)',
          fontSize: '12px', color: '#F59E0B',
        }}>
          <span style={{ flexShrink: 0, marginTop: 1 }}>&#9651;</span>
          {warnWeekly
            ? 'Weekly interval needs at least 4 weeks of data for meaningful results.'
            : 'Monthly interval needs at least 3 months of data for meaningful results.'}
        </div>
      )}

      <style>{`
        @media (max-width: 480px) {
          .fp-date-grid {
            grid-template-columns: 1fr !important;
          }
          .fp-date-grid > div:nth-child(2) { display: none; }
        }
      `}</style>
    </div>
  )
}
