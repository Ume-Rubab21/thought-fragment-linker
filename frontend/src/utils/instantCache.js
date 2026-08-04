const CACHE_PREFIX = 'thoughtlinker-instant-v2'

function scope() {
  const token = localStorage.getItem('tfl_token') || 'guest'
  return token.slice(-16).replace(/[^a-zA-Z0-9_-]/g, '') || 'guest'
}

function fullKey(key) {
  return `${CACHE_PREFIX}:${scope()}:${key}`
}

export function readInstantCache(key, fallback = null) {
  try {
    const raw = localStorage.getItem(fullKey(key))
    if (!raw) return fallback
    const parsed = JSON.parse(raw)
    return parsed?.data ?? fallback
  } catch {
    return fallback
  }
}

export function writeInstantCache(key, data) {
  try {
    localStorage.setItem(fullKey(key), JSON.stringify({
      savedAt: Date.now(),
      data,
    }))
  } catch {
    // Storage can be unavailable or full. The page still works from the API.
  }
  return data
}

export function removeInstantCache(key) {
  try { localStorage.removeItem(fullKey(key)) } catch { /* no-op */ }
}

export function clearInstantUserCache() {
  try {
    const prefix = `${CACHE_PREFIX}:${scope()}:`
    Object.keys(localStorage)
      .filter((key) => key.startsWith(prefix))
      .forEach((key) => localStorage.removeItem(key))
  } catch {
    // no-op
  }
}
