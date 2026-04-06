import axios from 'axios'
import { saveToken, getToken, getAllTokens, removeToken } from '../utils/tokenStore'

const http = axios.create({ baseURL: '/api' })

function unwrap(response) {
  const data = response.data
  if (data?.error) throw new Error(data.error)
  return data
}

// ── API functions ─────────────────────────────────────────────────────────────

export async function getCategories() {
  const res = await http.get('/assets/categories')
  return unwrap(res).categories
}

export async function getPeriods() {
  const res = await http.get('/assets/periods')
  return unwrap(res).periods
}

export async function getIntervals() {
  const res = await http.get('/assets/intervals')
  return unwrap(res).intervals
}

export async function validateTicker(symbol) {
  const res = await http.get('/assets/validate', { params: { symbol } })
  return unwrap(res)
}

export async function runPipeline(config) {
  const res = await http.post('/pipeline/run', config)
  const data = res.data
  if (data?.status === 'error') {
    const msg = data.stage ? `[${data.stage}] ${data.error}` : data.error
    throw new Error(msg)
  }
  return data
}

export async function getPreviousRuns() {
  const res = await http.get('/pipeline/status')
  return unwrap(res).assets
}

export function getChartUrl(filename) {
  return `/api/reports/charts/${filename}`
}

export function getPdfUrl(symbol) {
  return `/api/reports/pdf/${symbol}`
}

export function getViewUrl(symbol) {
  return `/api/reports/view/${symbol}`
}

export async function listReports(symbol) {
  const res = await http.get(`/reports/list/${symbol}`)
  return unwrap(res)
}

export async function addSchedule(payload) {
  const res = await http.post('/schedule/add', payload)
  const data = unwrap(res)
  if (data.job_id && data.token) {
    saveToken(data.job_id, data.token)
  }
  return data
}

export async function confirmSchedule(confirmToken) {
  const res = await http.get('/schedule/confirm', { params: { ct: confirmToken } })
  const data = res.data
  if (data?.error) throw new Error(data.error)
  return data
}

export async function getPendingSchedules() {
  const tokens = getAllTokens()
  if (tokens.length === 0) return []
  const res = await http.get('/schedule/pending', {
    headers: { 'X-Schedule-Token': tokens.join(',') },
  })
  return unwrap(res).jobs
}

export async function resendConfirmation(jobId) {
  const token = getToken(jobId)
  if (!token) throw new Error('No token found for this job')
  const res = await http.post('/schedule/resend-confirmation',
    { job_id: jobId },
    { headers: { 'X-Schedule-Token': token } },
  )
  return unwrap(res)
}

export async function getSchedules() {
  const tokens = getAllTokens()
  if (tokens.length === 0) return []
  const res = await http.get('/schedule/list', {
    headers: { 'X-Schedule-Token': tokens.join(',') },
  })
  return unwrap(res).jobs
}

export async function sendNow(jobId) {
  const token = getToken(jobId)
  if (!token) throw new Error('No token found for this job')
  try {
    const res = await http.post(`/schedule/send-now/${jobId}`, null, {
      headers: { 'X-Schedule-Token': token },
    })
    return unwrap(res)
  } catch (err) {
    if (err.response?.status === 403) {
      throw new Error('Invalid token — cannot send this report')
    }
    throw err
  }
}

export async function removeSchedule(jobId) {
  const token = getToken(jobId)
  if (!token) throw new Error('No token found for this job')
  try {
    const res = await http.delete(`/schedule/remove/${jobId}`, {
      headers: { 'X-Schedule-Token': token },
    })
    const data = unwrap(res)
    removeToken(jobId)
    return data
  } catch (err) {
    if (err.response?.status === 403) {
      throw new Error('Invalid token — cannot cancel this job')
    }
    throw err
  }
}
