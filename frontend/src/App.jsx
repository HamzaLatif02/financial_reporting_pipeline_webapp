import { useState, useEffect } from 'react'
import { Clock, ChevronRight, CalendarCheck, X } from 'lucide-react'
import AssetSelector from './components/AssetSelector'
import Dashboard from './components/Dashboard'
import ScheduleManager from './components/ScheduleManager'
import { runPipeline, getPreviousRuns, listReports } from './api/client'
import './App.css'

// ── Custom logo icon ───────────────────────────────────────────────────────

function LogoIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <polyline
        points="2,15 6,9 10,12 15,4 18,7"
        stroke="var(--accent)"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="15" cy="4" r="2" fill="var(--accent)" />
      <line x1="2" y1="18" x2="18" y2="18" stroke="var(--border-bright)" strokeWidth="1" strokeLinecap="round" />
    </svg>
  )
}

// ── Previous Runs Modal ────────────────────────────────────────────────────

function PreviousRunsModal({ onClose, onSelect }) {
  const [runs,      setRuns]      = useState(null)
  const [loading,   setLoading]   = useState(true)
  const [error,     setError]     = useState(null)
  const [selecting, setSelecting] = useState(null)

  useEffect(() => {
    getPreviousRuns()
      .then(setRuns)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  async function handleSelect(run) {
    setSelecting(run.symbol)
    try {
      const reports = await listReports(run.symbol)
      onSelect(run, reports)
    } catch {
      setSelecting(null)
    }
  }

  return (
    <div
      className="fp-modal-backdrop"
      onClick={e => e.target === e.currentTarget && onClose()}
    >
      <div className="fp-modal-panel" style={{ width: '100%', maxWidth: '520px' }}>

        {/* Header */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '18px 24px',
          borderBottom: '1px solid var(--border-subtle)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 32, height: 32, borderRadius: 'var(--r-md)',
              background: 'var(--bg-raised)', border: '1px solid var(--border-default)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Clock size={15} color="var(--text-2)" />
            </div>
            <div>
              <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '15px', color: 'var(--text-1)' }}>
                Previous Runs
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-3)', marginTop: 1 }}>
                Reload a past analysis
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none', border: 'none', cursor: 'pointer', padding: 6,
              color: 'var(--text-3)', borderRadius: 'var(--r-sm)',
              transition: 'color var(--t-fast) var(--ease)',
              lineHeight: 1,
            }}
            onMouseEnter={e => e.currentTarget.style.color = 'var(--text-1)'}
            onMouseLeave={e => e.currentTarget.style.color = 'var(--text-3)'}
          >
            <X size={17} />
          </button>
        </div>

        {/* Body */}
        <div style={{ overflowY: 'auto', flex: 1, padding: '8px' }}>
          {loading && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '48px 0', gap: 10, color: 'var(--text-3)' }}>
              <svg className="fp-spinner" width="18" height="18" viewBox="0 0 18 18" fill="none">
                <circle cx="9" cy="9" r="7" stroke="var(--border-bright)" strokeWidth="2" />
                <path d="M9 2a7 7 0 0 1 7 7" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" />
              </svg>
              <span style={{ fontSize: '13px' }}>Loading runs…</span>
            </div>
          )}
          {error && (
            <div style={{ padding: '16px', fontSize: '13px', color: 'var(--negative)' }}>
              {error}
            </div>
          )}
          {runs?.length === 0 && (
            <div style={{ padding: '48px 16px', textAlign: 'center', fontSize: '13px', color: 'var(--text-3)' }}>
              No previous runs found.
            </div>
          )}
          {runs?.map((run, i) => (
            <button
              key={i}
              onClick={() => handleSelect(run)}
              disabled={selecting === run.symbol}
              style={{
                width: '100%', textAlign: 'left', background: 'none', border: 'none',
                cursor: selecting === run.symbol ? 'wait' : 'pointer',
                padding: '12px 14px', borderRadius: 'var(--r-lg)',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12,
                transition: 'background var(--t-fast) var(--ease)',
              }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
              onMouseLeave={e => e.currentTarget.style.background = 'none'}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 500, fontSize: '14px', color: 'var(--text-1)' }}>
                    {run.symbol}
                  </span>
                  {run.name && (
                    <span style={{ fontSize: '12px', color: 'var(--text-3)' }}>— {run.name}</span>
                  )}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-3)', marginTop: 3, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  <span style={{
                    background: 'var(--bg-raised)', border: '1px solid var(--border-default)',
                    borderRadius: 'var(--r-sm)', padding: '1px 6px', fontFamily: 'var(--font-mono)',
                    fontSize: '10px', color: 'var(--text-2)',
                  }}>
                    {run.asset_type}
                  </span>
                  <span>{new Date(run.run_at).toLocaleString()}</span>
                  {run.row_count != null && <span>{run.row_count.toLocaleString()} rows</span>}
                </div>
              </div>
              {selecting === run.symbol ? (
                <svg className="fp-spinner" width="15" height="15" viewBox="0 0 15 15" fill="none" style={{ flexShrink: 0 }}>
                  <circle cx="7.5" cy="7.5" r="6" stroke="var(--border-bright)" strokeWidth="1.5" />
                  <path d="M7.5 1.5a6 6 0 0 1 6 6" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              ) : (
                <ChevronRight size={14} color="var(--text-4)" style={{ flexShrink: 0 }} />
              )}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

// ── Loading Overlay ────────────────────────────────────────────────────────

function LoadingOverlay({ message }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      minHeight: '60vh',
      animation: 'fp-fade-in var(--t-base) var(--ease)',
    }}>
      <div className="fp-card" style={{
        padding: '48px 40px',
        maxWidth: '380px', width: '100%',
        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 28,
        textAlign: 'center',
      }}>
        {/* Animated spinner ring */}
        <div style={{ position: 'relative', width: 60, height: 60 }}>
          {/* Outer ring track */}
          <svg
            width="60" height="60" viewBox="0 0 60 60" fill="none"
            style={{ position: 'absolute', inset: 0 }}
          >
            <circle cx="30" cy="30" r="26" stroke="var(--border-default)" strokeWidth="2" />
          </svg>
          {/* Spinning arc */}
          <svg
            width="60" height="60" viewBox="0 0 60 60" fill="none"
            className="fp-spinner"
            style={{ position: 'absolute', inset: 0 }}
          >
            <path
              d="M30 4 A 26 26 0 0 1 56 30"
              stroke="var(--accent)"
              strokeWidth="2"
              strokeLinecap="round"
              fill="none"
            />
          </svg>
          {/* Logo inside */}
          <div style={{
            position: 'absolute', inset: 0, display: 'flex',
            alignItems: 'center', justifyContent: 'center',
          }}>
            <LogoIcon />
          </div>
        </div>

        <div>
          <div style={{
            fontFamily: 'var(--font-display)', fontWeight: 700,
            fontSize: '16px', color: 'var(--text-1)', marginBottom: 8,
          }}>
            Analysing…
          </div>
          <div style={{
            fontSize: '13px', color: 'var(--text-2)',
            minHeight: '20px',
            transition: 'opacity var(--t-base) var(--ease)',
          }}>
            {message}
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-3)', marginTop: 6 }}>
            Usually takes 20–40 seconds
          </div>
        </div>

        {/* Progress dots */}
        <div style={{ display: 'flex', gap: 6 }}>
          {[0, 1, 2].map(i => (
            <div key={i} style={{
              width: 5, height: 5, borderRadius: '50%',
              background: 'var(--accent)',
              opacity: 0.3,
              animation: `fp-fade-in 0.8s ease ${i * 0.25}s infinite alternate`,
            }} />
          ))}
        </div>
      </div>
    </div>
  )
}

// ── App ────────────────────────────────────────────────────────────────────

export default function App() {
  const [view,         setView]         = useState('idle')
  const [result,       setResult]       = useState(null)
  const [error,        setError]        = useState(null)
  const [loadingMsg,   setLoadingMsg]   = useState('')
  const [showRuns,     setShowRuns]     = useState(false)
  const [showSchedule, setShowSchedule] = useState(false)

  async function handleSubmit(config) {
    setError(null)
    setView('loading')

    const steps = [
      'Connecting to Yahoo Finance…',
      `Fetching price history for ${config.symbol}…`,
      'Cleaning and validating data…',
      'Running financial analysis…',
      'Generating charts…',
      'Building PDF report…',
      'Almost done…',
    ]
    setLoadingMsg(steps[0])
    let stepIndex = 1
    const interval = setInterval(() => {
      if (stepIndex < steps.length) {
        setLoadingMsg(steps[stepIndex])
        stepIndex++
      }
    }, 3000)

    try {
      const data = await runPipeline(config)
      clearInterval(interval)
      setResult({ ...data, period: config.period, interval: config.interval })
      setView('done')
    } catch (err) {
      clearInterval(interval)
      setError(err.message)
      setView('idle')
    }
  }

  function handlePreviousRunSelect(run, reports) {
    setResult({
      status:        'success',
      symbol:        run.symbol,
      summary_stats: {},
      chart_urls:    reports.charts.map(f => `/api/reports/charts/${f}`),
      latest_value:  null,
      asset_info:    {},
      period:        run.period   ?? '',
      interval:      run.interval ?? '',
      _fromHistory:  true,
    })
    setShowRuns(false)
    setView('done')
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-base)' }}>

      {/* ── Navbar ─────────────────────────────────────────────────────── */}
      <header style={{
        background: 'var(--bg-base)',
        borderBottom: '1px solid var(--border-subtle)',
        position: 'sticky', top: 0, zIndex: 40,
      }}>
        <div style={{
          maxWidth: 1200, margin: '0 auto', padding: '0 24px',
          height: 56, display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          {/* Logo + brand */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <LogoIcon />
            <span style={{
              fontFamily: 'var(--font-display)', fontWeight: 700,
              fontSize: '15px', color: 'var(--text-1)',
              letterSpacing: '0.01em',
            }}>
              Finpipe
            </span>
            <span style={{
              height: 16, width: 1, background: 'var(--border-default)',
              margin: '0 4px',
              display: 'none', // hidden on small screens, we use inline style
            }} className="sm-separator" />
            <span style={{
              fontSize: '12px', color: 'var(--text-3)',
              fontFamily: 'var(--font-mono)',
              letterSpacing: '0.02em',
            }}
              className="hidden sm:inline"
            >
              Yahoo Finance
            </span>
          </div>

          {/* Nav actions */}
          <nav style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <button className="fp-nav-btn" onClick={() => setShowSchedule(true)}>
              <CalendarCheck size={13} />
              <span className="hidden sm:inline">Scheduled Reports</span>
            </button>
            <button className="fp-nav-btn" onClick={() => setShowRuns(true)}>
              <Clock size={13} />
              <span className="hidden sm:inline">Previous Runs</span>
            </button>
          </nav>
        </div>
      </header>

      {/* ── Error Banner ───────────────────────────────────────────────── */}
      {error && (
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: '16px 24px 0' }}>
          <div className="fp-error-banner">
            <span>{error}</span>
            <button onClick={() => setError(null)} aria-label="Dismiss">
              <X size={15} />
            </button>
          </div>
        </div>
      )}

      {/* ── Main content ───────────────────────────────────────────────── */}
      <main style={{ maxWidth: 1200, margin: '0 auto', padding: '32px 24px' }}>
        <div key={view} style={{ animation: 'fp-fade-up 0.28s var(--ease) both' }}>

          {view === 'idle' && (
            <div style={{ maxWidth: 760, margin: '0 auto' }}>
              <div style={{ marginBottom: 28 }}>
                <h1 style={{
                  fontFamily: 'var(--font-display)', fontWeight: 800,
                  fontSize: '1.75rem', color: 'var(--text-1)',
                  margin: 0, letterSpacing: '-0.01em', lineHeight: 1.2,
                }}>
                  Run a Financial Analysis
                </h1>
                <p style={{ color: 'var(--text-2)', marginTop: 8, fontSize: '14px' }}>
                  Select an asset, configure the date range, and generate charts and metrics.
                </p>
              </div>
              <div className="fp-card" style={{ padding: '32px 28px' }}>
                <AssetSelector onSubmit={handleSubmit} isLoading={false} />
              </div>
            </div>
          )}

          {view === 'loading' && <LoadingOverlay message={loadingMsg} />}

          {view === 'done' && result && (
            <Dashboard result={result} onReset={() => { setView('idle'); setResult(null) }} />
          )}
        </div>
      </main>

      {/* ── Modals ─────────────────────────────────────────────────────── */}
      {showRuns && (
        <PreviousRunsModal
          onClose={() => setShowRuns(false)}
          onSelect={handlePreviousRunSelect}
        />
      )}
      {showSchedule && (
        <ScheduleManager onClose={() => setShowSchedule(false)} />
      )}
    </div>
  )
}
