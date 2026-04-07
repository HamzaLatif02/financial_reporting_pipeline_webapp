import { useEffect, useState } from 'react'
import { CheckCircle, XCircle, Search, AlertCircle } from 'lucide-react'
import { getCategories, getPeriods, getIntervals, validateTicker } from '../../api/client'

// ── Single-asset picker panel ─────────────────────────────────────────────────

function AssetPanel({ label, accentColor, categories, selected, onSelect }) {
  const [activeCategory,   setActiveCategory]   = useState(null)
  const [customSymbol,     setCustomSymbol]     = useState('')
  const [validating,       setValidating]       = useState(false)
  const [validationResult, setValidationResult] = useState(null)

  useEffect(() => {
    if (categories && Object.keys(categories).length > 0 && !activeCategory) {
      setActiveCategory(Object.keys(categories)[0])
    }
  }, [categories, activeCategory])

  function selectExample(example) {
    onSelect({
      symbol:     example.symbol,
      name:       example.name,
      asset_type: activeCategory,
      currency:   'USD',
    })
    setCustomSymbol('')
    setValidationResult(null)
  }

  async function handleValidate() {
    const sym = customSymbol.trim().toUpperCase()
    if (!sym) return
    setValidating(true)
    setValidationResult(null)
    try {
      const result = await validateTicker(sym)
      setValidationResult(result)
      if (result.valid) {
        onSelect({
          symbol:     result.info.symbol,
          name:       result.info.name,
          asset_type: result.info.type ?? 'Custom',
          currency:   result.info.currency ?? 'USD',
        })
      } else {
        onSelect(null)
      }
    } catch (err) {
      setValidationResult({ valid: false, error: err.message })
      onSelect(null)
    } finally {
      setValidating(false)
    }
  }

  const examples = activeCategory ? (categories[activeCategory]?.examples ?? []) : []

  return (
    <div style={{
      flex: 1, minWidth: 0,
      border: `1.5px solid ${accentColor}33`,
      borderRadius: 'var(--r-lg)',
      background: 'var(--bg-surface)',
      padding: '20px',
      display: 'flex', flexDirection: 'column', gap: 16,
    }}>
      {/* Panel label */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <div style={{
          width: 10, height: 10, borderRadius: '50%',
          background: accentColor, flexShrink: 0,
        }} />
        <span style={{
          fontFamily: 'var(--font-display)', fontWeight: 700,
          fontSize: '13px', color: accentColor,
          letterSpacing: '0.04em', textTransform: 'uppercase',
        }}>
          {label}
        </span>
        {selected && (
          <span style={{
            marginLeft: 'auto',
            fontFamily: 'var(--font-mono)', fontWeight: 600,
            fontSize: '12px', color: accentColor,
            background: `${accentColor}18`,
            border: `1px solid ${accentColor}44`,
            borderRadius: 'var(--r-sm)', padding: '2px 8px',
          }}>
            {selected.symbol}
          </span>
        )}
      </div>

      {/* Category tabs */}
      <div style={{ overflowX: 'auto' }}>
        <div style={{ display: 'flex', gap: 4, minWidth: 'max-content' }}>
          {Object.keys(categories).map(cat => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              style={{
                padding: '5px 10px', fontSize: '11px', fontWeight: 500,
                fontFamily: 'var(--font-body)',
                border: `1px solid ${activeCategory === cat ? accentColor + '66' : 'var(--border-default)'}`,
                borderRadius: 'var(--r-md)', cursor: 'pointer',
                background: activeCategory === cat ? `${accentColor}18` : 'var(--bg-raised)',
                color: activeCategory === cat ? accentColor : 'var(--text-2)',
                transition: 'all var(--t-fast) var(--ease)',
                whiteSpace: 'nowrap',
              }}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Example cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(90px, 1fr))',
        gap: 6,
      }}>
        {examples.map(ex => {
          const isSel = selected?.symbol === ex.symbol
          return (
            <button
              key={ex.symbol}
              onClick={() => selectExample(ex)}
              style={{
                background: isSel ? `${accentColor}1A` : 'var(--bg-raised)',
                border: `1px solid ${isSel ? accentColor + '66' : 'var(--border-default)'}`,
                borderRadius: 'var(--r-md)', cursor: 'pointer',
                padding: '8px 8px', textAlign: 'left',
                transition: 'all var(--t-fast) var(--ease)',
              }}
              onMouseEnter={e => { if (!isSel) e.currentTarget.style.borderColor = accentColor + '44' }}
              onMouseLeave={e => { if (!isSel) e.currentTarget.style.borderColor = 'var(--border-default)' }}
            >
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 3 }}>
                <span style={{
                  fontFamily: 'var(--font-mono)', fontWeight: 500,
                  fontSize: '11px', color: 'var(--text-1)',
                }}>
                  {ex.symbol}
                </span>
                {isSel && <CheckCircle size={11} color={accentColor} style={{ flexShrink: 0, marginTop: 1 }} />}
              </div>
              <span style={{ fontSize: '10px', color: 'var(--text-3)', lineHeight: 1.3, display: 'block' }}>
                {ex.name}
              </span>
            </button>
          )
        })}
      </div>

      {/* Custom ticker */}
      <div>
        <div style={{ fontSize: '10px', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--text-3)', marginBottom: 6 }}>
          Custom Ticker
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search size={12} color="var(--text-3)" style={{ position: 'absolute', left: 9, top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }} />
            <input
              type="text"
              placeholder="e.g. TSLA"
              value={customSymbol}
              onChange={e => { setCustomSymbol(e.target.value); setValidationResult(null) }}
              onKeyDown={e => e.key === 'Enter' && handleValidate()}
              className="fp-input"
              style={{ paddingLeft: 28, fontFamily: 'var(--font-mono)', fontSize: '12px', textTransform: 'uppercase', padding: '7px 8px 7px 28px' }}
            />
          </div>
          <button
            onClick={handleValidate}
            disabled={!customSymbol.trim() || validating}
            className="fp-btn-ghost"
            style={{ padding: '6px 12px', fontSize: '12px', flexShrink: 0 }}
          >
            {validating ? (
              <svg className="fp-spinner" width="12" height="12" viewBox="0 0 12 12" fill="none">
                <circle cx="6" cy="6" r="4.5" stroke="var(--border-bright)" strokeWidth="1.5" />
                <path d="M6 1.5a4.5 4.5 0 0 1 4.5 4.5" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
            ) : 'Validate'}
          </button>
        </div>
        {validationResult && (
          <div style={{
            marginTop: 6, display: 'flex', alignItems: 'flex-start', gap: 6,
            padding: '7px 10px', borderRadius: 'var(--r-md)', fontSize: '11px',
            background: validationResult.valid ? 'var(--positive-dim)' : 'var(--negative-dim)',
            border: `1px solid ${validationResult.valid ? 'rgba(43,196,138,0.25)' : 'rgba(240,100,112,0.25)'}`,
            color: validationResult.valid ? 'var(--positive)' : 'var(--negative)',
          }}>
            {validationResult.valid
              ? <CheckCircle size={12} style={{ marginTop: 1, flexShrink: 0 }} />
              : <XCircle    size={12} style={{ marginTop: 1, flexShrink: 0 }} />
            }
            <span>
              {validationResult.valid
                ? `${validationResult.info.name} · ${validationResult.info.type}`
                : (validationResult.error ?? 'Not found on Yahoo Finance')
              }
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

// ── Main export ───────────────────────────────────────────────────────────────

export default function AssetPairSelector({ onSubmit, isLoading }) {
  const [categories, setCategories] = useState({})
  const [periods,    setPeriods]    = useState([])
  const [intervals,  setIntervals]  = useState([])
  const [fetching,   setFetching]   = useState(true)
  const [fetchError, setFetchError] = useState(null)

  const [assetA, setAssetA] = useState(null)
  const [assetB, setAssetB] = useState(null)
  const [period,    setPeriod]   = useState(null)
  const [interval,  setInterval] = useState(null)

  function loadData() {
    setFetching(true)
    setFetchError(null)
    Promise.all([getCategories(), getPeriods(), getIntervals()])
      .then(([cats, per, inv]) => {
        setCategories(cats)
        setPeriods(per)
        setIntervals(inv)
      })
      .catch(err => setFetchError(err.message))
      .finally(() => setFetching(false))
  }

  useEffect(() => { loadData() }, [])

  const sameAsset = assetA && assetB && assetA.symbol === assetB.symbol
  const canSubmit = assetA && assetB && period && interval && !isLoading && !sameAsset

  function handleSubmit() {
    if (!canSubmit) return
    onSubmit(
      { ...assetA, period, interval },
      { ...assetB, period, interval },
    )
  }

  if (fetching) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '64px 0', gap: 12, color: 'var(--text-3)' }}>
        <svg className="fp-spinner" width="20" height="20" viewBox="0 0 20 20" fill="none">
          <circle cx="10" cy="10" r="8" stroke="var(--border-bright)" strokeWidth="1.5" />
          <path d="M10 2a8 8 0 0 1 8 8" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
        <span style={{ fontSize: '13px' }}>Loading asset data…</span>
      </div>
    )
  }

  if (fetchError) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16, padding: '48px 0', textAlign: 'center' }}>
        <p style={{ fontSize: '13px', color: 'var(--negative)' }}>Failed to load: {fetchError}</p>
        <button className="fp-btn-ghost" onClick={loadData} style={{ padding: '8px 18px' }}>Retry</button>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

      {/* ── Asset panels ────────────────────────────────────────────────── */}
      <div style={{
        display: 'flex', gap: 16, flexWrap: 'wrap',
        alignItems: 'stretch',
      }}>
        <AssetPanel
          label="Asset A"
          accentColor="#2563EB"
          categories={categories}
          selected={assetA}
          onSelect={setAssetA}
        />
        <AssetPanel
          label="Asset B"
          accentColor="#EA580C"
          categories={categories}
          selected={assetB}
          onSelect={setAssetB}
        />
      </div>

      {/* ── Same-asset error ─────────────────────────────────────────────── */}
      {sameAsset && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8,
          padding: '10px 14px', borderRadius: 'var(--r-md)',
          background: 'var(--negative-dim)', border: '1px solid rgba(240,100,112,0.25)',
          fontSize: '13px', color: 'var(--negative)',
        }}>
          <AlertCircle size={14} style={{ flexShrink: 0 }} />
          Cannot compare an asset with itself. Please select a different asset for B.
        </div>
      )}

      {/* ── Shared period + interval ─────────────────────────────────────── */}
      <div style={{
        background: 'var(--bg-raised)', border: '1px solid var(--border-default)',
        borderRadius: 'var(--r-lg)', padding: '16px 20px',
        display: 'flex', flexDirection: 'column', gap: 16,
      }}>
        <div style={{
          fontSize: '11px', color: 'var(--text-3)', display: 'flex', alignItems: 'center', gap: 6,
        }}>
          Both assets will be analysed over the same period for a meaningful comparison.
        </div>

        <div>
          <span className="fp-section-label">Period</span>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 6 }}>
            {periods.map(p => (
              <button
                key={p.value}
                onClick={() => setPeriod(p.value)}
                className={`fp-pill-btn ${period === p.value ? 'active' : ''}`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <span className="fp-section-label">Interval</span>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 6 }}>
            {intervals.map(iv => (
              <button
                key={iv.value}
                onClick={() => setInterval(iv.value)}
                className={`fp-pill-btn ${interval === iv.value ? 'active' : ''}`}
              >
                {iv.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── Submit ──────────────────────────────────────────────────────── */}
      <button
        onClick={handleSubmit}
        disabled={!canSubmit}
        className="fp-btn-accent"
        style={{ width: '100%', padding: '14px 24px', fontSize: '15px', borderRadius: 'var(--r-lg)' }}
      >
        {isLoading ? (
          <>
            <svg className="fp-spinner" width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="6" stroke="rgba(4,8,16,0.35)" strokeWidth="1.5" />
              <path d="M8 2a6 6 0 0 1 6 6" stroke="#040810" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
            Running Comparison…
          </>
        ) : 'Run Comparison'}
      </button>
    </div>
  )
}
