/**
 * tokenStore — localStorage persistence for per-job schedule tokens.
 *
 * Storage key: "schedule_tokens"
 * Storage value: JSON object mapping job_id → token string
 *
 * Tokens are secret credentials — this module never logs them.
 */

const STORAGE_KEY = 'schedule_tokens'

function _read() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}')
  } catch {
    return {}
  }
}

function _write(store) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(store))
}

/**
 * Save or overwrite the token for a given jobId.
 */
export function saveToken(jobId, token) {
  const store = _read()
  store[jobId] = token
  _write(store)
}

/**
 * Return the token for jobId, or null if not found.
 */
export function getToken(jobId) {
  return _read()[jobId] ?? null
}

/**
 * Return an array of all stored token values (not job IDs).
 * Used to build the X-Schedule-Token header for list requests.
 */
export function getAllTokens() {
  return Object.values(_read())
}

/**
 * Remove the token entry for jobId.
 */
export function removeToken(jobId) {
  const store = _read()
  delete store[jobId]
  _write(store)
}

/**
 * Return true if at least one token is stored in this browser.
 */
export function hasAnyTokens() {
  return Object.keys(_read()).length > 0
}
