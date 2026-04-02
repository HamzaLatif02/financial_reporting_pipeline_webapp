import { useEffect, useState } from 'react'
import { X, Loader2, CalendarCheck, Trash2 } from 'lucide-react'
import { listSchedules, removeSchedule } from '../api/client'

export default function ScheduleManager({ onClose }) {
  const [jobs,    setJobs]    = useState(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)
  const [removing, setRemoving] = useState(null) // job_id being removed

  useEffect(() => {
    listSchedules()
      .then(setJobs)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

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
    const f = job.frequency
    if (f === 'daily')   return 'Daily'
    if (f === 'weekly')  return 'Weekly'
    if (f === 'monthly') return 'Monthly'
    return f
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
      onClick={e => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[80vh] flex flex-col">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <h2 className="font-semibold text-slate-900 flex items-center gap-2">
            <CalendarCheck size={16} className="text-blue-600" />
            Scheduled Reports
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors">
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="overflow-y-auto flex-1 px-6 py-4">
          {loading && (
            <div className="flex items-center justify-center py-12 text-slate-400">
              <Loader2 className="animate-spin mr-2" size={18} /> Loading…
            </div>
          )}

          {error && (
            <p className="text-sm text-red-600 py-4">{error}</p>
          )}

          {!loading && !error && jobs?.length === 0 && (
            <div className="py-12 text-center text-sm text-slate-400 space-y-1">
              <p className="font-medium text-slate-500">No scheduled reports yet.</p>
              <p>Run an analysis and click <span className="font-medium">Schedule Report</span> to set one up.</p>
            </div>
          )}

          {jobs?.length > 0 && (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="text-left py-2 pr-4 font-semibold text-slate-500 text-xs uppercase tracking-wide">Asset</th>
                  <th className="text-left py-2 pr-4 font-semibold text-slate-500 text-xs uppercase tracking-wide">Frequency</th>
                  <th className="text-left py-2 pr-4 font-semibold text-slate-500 text-xs uppercase tracking-wide">Next Report</th>
                  <th className="text-left py-2 pr-4 font-semibold text-slate-500 text-xs uppercase tracking-wide">Email</th>
                  <th className="py-2" />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {jobs.map(job => (
                  <tr key={job.job_id} className="group">
                    <td className="py-3 pr-4">
                      <span className="font-medium text-slate-800">{job.symbol}</span>
                      {job.name && job.name !== job.symbol && (
                        <span className="ml-1.5 text-slate-400 text-xs">{job.name}</span>
                      )}
                    </td>
                    <td className="py-3 pr-4 text-slate-600">{fmtFrequency(job)}</td>
                    <td className="py-3 pr-4 text-slate-500 text-xs">
                      {job.next_run_time
                        ? new Date(job.next_run_time).toLocaleString()
                        : '—'}
                    </td>
                    <td className="py-3 pr-4 text-slate-500 text-xs truncate max-w-[160px]">
                      {job.email}
                    </td>
                    <td className="py-3 text-right">
                      <button
                        onClick={() => handleRemove(job)}
                        disabled={removing === job.job_id}
                        className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg
                                   text-xs font-medium text-red-600 hover:bg-red-50
                                   disabled:opacity-40 transition-colors"
                      >
                        {removing === job.job_id
                          ? <Loader2 size={13} className="animate-spin" />
                          : <Trash2 size={13} />
                        }
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
