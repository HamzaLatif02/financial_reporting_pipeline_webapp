import { useState, useEffect, useRef } from 'react'
import AssetPairSelector   from '../components/comparison/AssetPairSelector'
import ComparisonDashboard from '../components/comparison/ComparisonDashboard'
import { runComparison } from '../api/client'
import { X } from 'lucide-react'

const LOADING_STEPS_TEMPLATE = (a, b) => [
  `Fetching data for ${a}...`,
  `Fetching data for ${b}...`,
  'Aligning price histories...',
  'Computing correlation and metrics...',
  'Generating comparison charts...',
  'Building combined PDF report...',
  'Almost done...',
]

function ComparisonLoading({ message }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      minHeight: '60vh',
      animation: 'fp-fade-in var(--t-base) var(--ease)',
    }}>
      <div className="fp-card" style={{
        padding: '48px 40px', maxWidth: '400px', width: '100%',
        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 28,
        textAlign: 'center',
      }}>
        {/* Spinner */}
        <div style={{ position: 'relative', width: 60, height: 60 }}>
          <svg width="60" height="60" viewBox="0 0 60 60" fill="none" style={{ position: 'absolute', inset: 0 }}>
            <circle cx="30" cy="30" r="26" stroke="var(--border-default)" strokeWidth="2" />
          </svg>
          <svg width="60" height="60" viewBox="0 0 60 60" fill="none" className="fp-spinner" style={{ position: 'absolute', inset: 0 }}>
            <path d="M30 4 A 26 26 0 0 1 56 30" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" fill="none" />
          </svg>
          {/* Two dots representing two assets */}
          <div style={{
            position: 'absolute', inset: 0, display: 'flex',
            alignItems: 'center', justifyContent: 'center', gap: 6,
          }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#2563EB' }} />
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#EA580C' }} />
          </div>
        </div>

        <div>
          <div style={{
            fontFamily: 'var(--font-display)', fontWeight: 700,
            fontSize: '16px', color: 'var(--text-1)', marginBottom: 8,
          }}>
            Comparing…
          </div>
          <div style={{
            fontSize: '13px', color: 'var(--text-2)',
            minHeight: '20px',
            transition: 'opacity var(--t-base) var(--ease)',
          }}>
            {message}
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-3)', marginTop: 6 }}>
            Usually takes 30–60 seconds
          </div>
        </div>

        <div style={{ display: 'flex', gap: 6 }}>
          {[0, 1, 2].map(i => (
            <div key={i} style={{
              width: 5, height: 5, borderRadius: '50%',
              background: 'var(--accent)', opacity: 0.3,
              animation: `fp-fade-in 0.8s ease ${i * 0.25}s infinite alternate`,
            }} />
          ))}
        </div>
      </div>
    </div>
  )
}

export default function Compare() {
  const [view,       setView]       = useState('idle')
  const [result,     setResult]     = useState(null)
  const [error,      setError]      = useState(null)
  const [loadingMsg, setLoadingMsg] = useState('')

  const intervalRef = useRef(null)

  function clearTimer() {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }

  useEffect(() => () => clearTimer(), [])

  async function handleSubmit(config_a, config_b) {
    setError(null)
    setView('loading')

    const steps = LOADING_STEPS_TEMPLATE(config_a.symbol, config_b.symbol)
    setLoadingMsg(steps[0])
    let idx = 1
    intervalRef.current = setInterval(() => {
      if (idx < steps.length) {
        setLoadingMsg(steps[idx++])
      }
    }, 5000)

    try {
      const data = await runComparison(config_a, config_b)
      clearTimer()
      setResult(data)
      setView('done')
    } catch (err) {
      clearTimer()
      setError(err.message)
      setView('idle')
    }
  }

  function handleReset() {
    setView('idle')
    setResult(null)
    setError(null)
  }

  return (
    <div>
      {/* Error banner */}
      {error && (
        <div style={{ marginBottom: 20 }}>
          <div className="fp-error-banner">
            <span>{error}</span>
            <button onClick={() => setError(null)} aria-label="Dismiss">
              <X size={15} />
            </button>
          </div>
        </div>
      )}

      <div key={view} style={{ animation: 'fp-fade-up 0.28s var(--ease) both' }}>
        {view === 'idle' && (
          <div>
            <div style={{ marginBottom: 24 }}>
              <h2 style={{
                fontFamily: 'var(--font-display)', fontWeight: 800,
                fontSize: '1.5rem', color: 'var(--text-1)',
                margin: 0, letterSpacing: '-0.01em', lineHeight: 1.2,
              }}>
                Compare Two Assets
              </h2>
              <p style={{ color: 'var(--text-2)', marginTop: 8, fontSize: '14px' }}>
                Select two assets, run side-by-side analysis, and download a combined report.
              </p>
            </div>
            <div className="fp-card" style={{ padding: '28px' }}>
              <AssetPairSelector onSubmit={handleSubmit} isLoading={false} />
            </div>
          </div>
        )}

        {view === 'loading' && <ComparisonLoading message={loadingMsg} />}

        {view === 'done' && result && (
          <ComparisonDashboard result={result} onReset={handleReset} />
        )}
      </div>
    </div>
  )
}
