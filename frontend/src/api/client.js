import axios from 'axios'

const http = axios.create({ baseURL: '/api' })

function unwrap(response) {
  const data = response.data
  if (data?.error) throw new Error(data.error)
  return data
}

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

export async function listReports(symbol) {
  const res = await http.get(`/reports/list/${symbol}`)
  return unwrap(res)
}

export async function addSchedule(payload) {
  const res = await http.post('/schedule/add', payload)
  return unwrap(res)
}

export async function removeSchedule(jobId) {
  const res = await http.delete(`/schedule/remove/${jobId}`)
  return unwrap(res)
}

export async function listSchedules() {
  const res = await http.get('/schedule/list')
  return unwrap(res).jobs
}
