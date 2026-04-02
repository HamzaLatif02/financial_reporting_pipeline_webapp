import { useState } from 'react'
import { X, CalendarCheck, Loader2, CheckCircle } from 'lucide-react'
import { addSchedule } from '../api/client'

const DAYS_OF_WEEK = [
  { value: 'mon', label: 'Monday' },
  { value: 'tue', label: 'Tuesday' },
  { value: 'wed', label: 'Wednesday' },
  { value: 'thu', label: 'Thursday' },
  { value: 'fri', label: 'Friday' },
  { value: 'sat', label: 'Saturday' },
  { value: 'sun', label: 'Sunday' },
]

const HOURS = Array.from({ length: 24 }, (_, i) => ({
  value: i,
  label: String(i).padStart(2, '0'),
}))

const MINUTES = [
  { value: 0,  label: '00' },
  { value: 30, label: '30' },
]

const DAYS_OF_MONTH = Array.from({ length: 28 }, (_, i) => ({
  value: i + 1,
  label: String(i + 1),
}))

function schedulePreview({ symbol, frequency, hour, minute, dayOfWeek, day }) {
  const hm = `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`
  if (frequency === 'daily')
    return `You will receive a report for ${symbol} every day at ${hm}.`
  if (frequency === 'weekly') {
    const dow = DAYS_OF_WEEK.find(d => d.value === dayOfWeek)?.label ?? dayOfWeek
    return `You will receive a report for ${symbol} every ${dow} at ${hm}.`
  }
  if (frequency === 'monthly')
    return `You will receive a report for ${symbol} on day ${day} of every month at ${hm}.`
  return ''
}

export default function ScheduleModal({ config, symbol, name, onClose }) {
  const [email,     setEmail]     = useState('')
  const [frequency, setFrequency] = useState('daily')
  const [hour,      setHour]      = useState(8)
  const [minute,    setMinute]    = useState(0)
  const [dayOfWeek, setDayOfWeek] = useState('mon')
  const [day,       setDay]       = useState(1)

  const [submitting, setSubmitting] = useState(false)
  const [error,      setError]      = useState(null)
  const [success,    setSuccess]    = useState(null) // { next_run }

  const preview = schedulePreview({ symbol, frequency, hour, minute, dayOfWeek, day })

  async function handleSubmit() {
    setError(null)
    setSubmitting(true)
    try {
      const payload = {
        config,
        email,
        frequency,
        hour,
        minute,
        ...(frequency === 'weekly'  && { day_of_week: dayOfWeek }),
        ...(frequency === 'monthly' && { day }),
      }
      const res = await addSchedule(payload)
      setSuccess({ next_run: res.next_run })
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
      onClick={e => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md flex flex-col">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <h2 className="font-semibold text-slate-900 flex items-center gap-2">
            <CalendarCheck size={16} className="text-blue-600" />
            Schedule Report — {name ?? symbol}
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors">
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-5">

          {success ? (
            <div className="flex flex-col items-center gap-3 py-4 text-center">
              <CheckCircle size={40} className="text-green-500" />
              <p className="font-semibold text-slate-800">Scheduled!</p>
              {success.next_run && (
                <p className="text-sm text-slate-500">
                  Your first report will arrive on{' '}
                  <span className="font-medium text-slate-700">
                    {new Date(success.next_run).toLocaleString()}
                  </span>.
                </p>
              )}
              <button
                onClick={onClose}
                className="mt-2 px-5 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium
                           hover:bg-blue-700 transition-colors"
              >
                Close
              </button>
            </div>
          ) : (
            <>
              {/* Email */}
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5">
                  Email Address
                </label>
                <input
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm
                             focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent"
                />
              </div>

              {/* Frequency */}
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5">
                  Frequency
                </label>
                <div className="flex gap-2">
                  {['daily', 'weekly', 'monthly'].map(f => (
                    <button
                      key={f}
                      onClick={() => setFrequency(f)}
                      className={[
                        'flex-1 py-2 rounded-lg border text-sm font-medium capitalize transition-colors',
                        frequency === f
                          ? 'border-blue-500 bg-blue-50 text-blue-700'
                          : 'border-slate-200 text-slate-600 hover:border-slate-400',
                      ].join(' ')}
                    >
                      {f}
                    </button>
                  ))}
                </div>
              </div>

              {/* Time */}
              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5">
                  Time
                </label>
                <div className="flex gap-2">
                  <select
                    value={hour}
                    onChange={e => setHour(Number(e.target.value))}
                    className="flex-1 px-3 py-2 rounded-lg border border-slate-300 text-sm
                               focus:outline-none focus:ring-2 focus:ring-blue-400"
                  >
                    {HOURS.map(h => (
                      <option key={h.value} value={h.value}>{h.label}h</option>
                    ))}
                  </select>
                  <select
                    value={minute}
                    onChange={e => setMinute(Number(e.target.value))}
                    className="flex-1 px-3 py-2 rounded-lg border border-slate-300 text-sm
                               focus:outline-none focus:ring-2 focus:ring-blue-400"
                  >
                    {MINUTES.map(m => (
                      <option key={m.value} value={m.value}>{m.label}m</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Day of week (weekly only) */}
              {frequency === 'weekly' && (
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5">
                    Day of Week
                  </label>
                  <select
                    value={dayOfWeek}
                    onChange={e => setDayOfWeek(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm
                               focus:outline-none focus:ring-2 focus:ring-blue-400"
                  >
                    {DAYS_OF_WEEK.map(d => (
                      <option key={d.value} value={d.value}>{d.label}</option>
                    ))}
                  </select>
                </div>
              )}

              {/* Day of month (monthly only) */}
              {frequency === 'monthly' && (
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5">
                    Day of Month
                  </label>
                  <select
                    value={day}
                    onChange={e => setDay(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm
                               focus:outline-none focus:ring-2 focus:ring-blue-400"
                  >
                    {DAYS_OF_MONTH.map(d => (
                      <option key={d.value} value={d.value}>{d.label}</option>
                    ))}
                  </select>
                </div>
              )}

              {/* Preview */}
              {preview && (
                <p className="text-sm text-slate-500 bg-slate-50 border border-slate-200
                               rounded-lg px-4 py-3 leading-relaxed">
                  {preview}
                </p>
              )}

              {/* Error */}
              {error && (
                <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
                  {error}
                </p>
              )}

              {/* Submit */}
              <button
                onClick={handleSubmit}
                disabled={!email || submitting}
                className="w-full py-2.5 rounded-lg bg-blue-600 text-white text-sm font-semibold
                           hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed
                           transition-colors flex items-center justify-center gap-2"
              >
                {submitting && <Loader2 size={15} className="animate-spin" />}
                {submitting ? 'Scheduling…' : 'Schedule'}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
