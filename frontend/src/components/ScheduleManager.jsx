import { useEffect, useState } from 'react'
import { X, CalendarCheck, Trash2 } from 'lucide-react'
import { listSchedules, removeSchedule } from '../api/client'

export default function ScheduleManager({ onClose }) {
  const [jobs,     setJobs]     = useState(null)
  const [loading,  setLoading]  = useState(true)
  const [error,    setError]    = useState(null)
  const [removing, setRemoving] = useState(null)

  function load() {
    setLoading(true)
    setError(null)
    listSchedules()
      .then(setJobs)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function handleRemove(job) {
    if (!window.confirm(`Cancel the scheduled report for ${job.symbol}? This cannot be undone.`)) return
    setRemoving(job.job_id)
    try {
      await removeSchedule(job.job_id)
      setJobs(prev => prev.filter(j => j.job_id !== job.job_id))
    } catch (err) {
      alert(`Failed to cancel: ${err.message}`)
    } finally {
      setRemoving(null)
    }
  }

  function fmtFrequency(job) {
    if (job.frequency === 'daily')   return 'Daily'
    if (job.frequency === 'weekly')  return 'Weekly'
    if (job.frequency === 'monthly') return 'Monthly'
    return job.frequency
  }

  return (
    <div
      className="fp-drawer-backdrop"
      onClick={e => e.target === e.currentTarget && onClose()}
    >
      <div className="fp-drawer-panel">

        {/* ── Header ─────────────────────────────────────────────────── */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '20px 28px',
          borderBottom: '1px solid var(--border-subtle)',
          flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{
              width: 36, height: 36, borderRadius: 'var(--r-md)',
              background: 'var(--accent-dim)', border: '1px solid rgba(79,172,247,0.22)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <CalendarCheck size={16} color="var(--accent)" />
            </div>
            <div>
              <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '16px', color: 'var(--text-1)' }}>
                Scheduled Reports
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-3)', marginTop: 1 }}>
                Manage automated report delivery
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none', border: 'none', cursor: 'pointer', padding: 8,
              color: 'var(--text-3)', borderRadius: 'var(--r-md)',
              lineHeight: 1, transition: 'all var(--t-fast) var(--ease)',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.background = 'var(--bg-hover)'
              e.currentTarget.style.color = 'var(--text-1)'
            }}
            onMouseLeave={e => {
              e.currentTarget.style.background = 'none'
              e.currentTarget.style.color = 'var(--text-3)'
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* ── Body ───────────────────────────────────────────────────── */}
        <div style={{ overflowY: 'auto', flex: 1, padding: '16px 28px' }}>

          {loading && (
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              padding: '64px 0', gap: 10, color: 'var(--text-3)',
            }}>
              <svg className="fp-spinner" width="18" height="18" viewBox="0 0 18 18" fill="none">
                <circle cx="9" cy="9" r="7" stroke="var(--border-bright)" strokeWidth="1.5" />
                <path d="M9 2a7 7 0 0 1 7 7" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
              <span style={{ fontSize: '13px' }}>Loading schedules…</span>
            </div>
          )}

          {error && (
            <div style={{ padding: '32px 0', textAlign: 'center', display: 'flex', flexDirection: 'column', gap: 12, alignItems: 'center' }}>
              <p style={{ fontSize: '13px', color: 'var(--negative)', margin: 0 }}>{error}</p>
              <button className="fp-btn-ghost" onClick={load} style={{ padding: '7px 16px' }}>
                Retry
              </button>
            </div>
          )}

          {!loading && !error && jobs?.length === 0 && (
            <div style={{ padding: '64px 0', textAlign: 'center' }}>
              <div style={{ marginBottom: 12 }}>
                <CalendarCheck size={32} color="var(--text-4)" style={{ margin: '0 auto' }} />
              </div>
              <p style={{ fontSize: '14px', color: 'var(--text-2)', margin: '0 0 6px', fontWeight: 500 }}>
                No scheduled reports yet
              </p>
              <p style={{ fontSize: '13px', color: 'var(--text-3)', margin: 0 }}>
                Run an analysis and click <span style={{ color: 'var(--text-2)', fontWeight: 500 }}>Schedule Report</span> to set one up.
              </p>
            </div>
          )}

          {jobs?.length > 0 && (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  <th style={{ textAlign: 'left', padding: '8px 12px 10px 0', fontSize: '10px', fontWeight: 600, letterSpacing: '0.07em', textTransform: 'uppercase', color: 'var(--text-3)', fontFamily: 'var(--font-body)' }}>Asset</th>
                  <th style={{ textAlign: 'left', padding: '8px 12px 10px', fontSize: '10px', fontWeight: 600, letterSpacing: '0.07em', textTransform: 'uppercase', color: 'var(--text-3)', fontFamily: 'var(--font-body)' }}>Frequency</th>
                  <th style={{ textAlign: 'left', padding: '8px 12px 10px', fontSize: '10px', fontWeight: 600, letterSpacing: '0.07em', textTransform: 'uppercase', color: 'var(--text-3)', fontFamily: 'var(--font-body)' }}>Next Report</th>
                  <th style={{ textAlign: 'left', padding: '8px 12px 10px', fontSize: '10px', fontWeight: 600, letterSpacing: '0.07em', textTransform: 'uppercase', color: 'var(--text-3)', fontFamily: 'var(--font-body)' }}>Email</th>
                  <th style={{ padding: '8px 0 10px' }} />
                </tr>
              </thead>
              <tbody>
                {jobs.map(job => (
                  <tr
                    key={job.job_id}
                    className="fp-table-row"
                    style={{ borderBottom: '1px solid var(--border-subtle)', borderRadius: 'var(--r-md)' }}
                  >
                    <td style={{ padding: '12px 12px 12px 0' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 500, fontSize: '13px', color: 'var(--text-1)' }}>
                        {job.symbol}
                      </span>
                      {job.name && job.name !== job.symbol && (
                        <span style={{ display: 'block', fontSize: '11px', color: 'var(--text-3)', marginTop: 2 }}>
                          {job.name}
                        </span>
                      )}
                    </td>
                    <td style={{ padding: '12px' }}>
                      <span className="fp-badge fp-badge-neutral" style={{ fontSize: '10px' }}>
                        {fmtFrequency(job)}
                      </span>
                    </td>
                    <td style={{ padding: '12px', fontSize: '12px', color: 'var(--text-2)', fontFamily: 'var(--font-mono)' }}>
                      {job.next_run_time
                        ? new Date(job.next_run_time).toLocaleString()
                        : <span style={{ color: 'var(--text-4)' }}>—</span>
                      }
                    </td>
                    <td style={{ padding: '12px', maxWidth: 180 }}>
                      <span style={{ fontSize: '12px', color: 'var(--text-3)', display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {job.email}
                      </span>
                    </td>
                    <td style={{ padding: '12px 0', textAlign: 'right' }}>
                      <button
                        onClick={() => handleRemove(job)}
                        disabled={removing === job.job_id}
                        className="fp-cancel-btn"
                      >
                        {removing === job.job_id ? (
                          <svg className="fp-spinner" width="12" height="12" viewBox="0 0 12 12" fill="none">
                            <circle cx="6" cy="6" r="4.5" stroke="var(--border-bright)" strokeWidth="1.5" />
                            <path d="M6 1.5a4.5 4.5 0 0 1 4.5 4.5" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round" />
                          </svg>
                        ) : (
                          <Trash2 size={12} />
                        )}
                        Cancel
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
