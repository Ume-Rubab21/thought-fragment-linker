const BACKEND_URL =
  import.meta.env.VITE_BACKEND_URL ||
  'http://localhost:8000'

const TOKEN_KEY = 'tfl_token'


const USER_CACHE_KEY = 'tfl_cached_user'
const GET_CACHE_PREFIX = 'tfl_api_cache:'
const DEFAULT_GET_CACHE_MS = 2 * 60 * 1000
const requestCache = new Map()
const inFlightRequests = new Map()
let backendWarmRequest = null
let keepAliveTimer = null

function cacheDurationFor(path) {
  if (path === '/auth/me') return 30 * 60 * 1000
  if (path.startsWith('/suggestions')) return 60 * 1000
  if (path.startsWith('/model-calls')) return 60 * 1000
  if (path.startsWith('/brain-dumps')) return 15 * 1000
  return DEFAULT_GET_CACHE_MS
}

function getCacheKey(path) {
  const token = getToken()
  const tokenScope = token ? token.slice(-12) : 'public'
  return `${tokenScope}:${path}`
}

function readSessionCache(key, maxAge) {
  const memoryValue = requestCache.get(key)
  if (memoryValue && Date.now() - memoryValue.savedAt < maxAge) {
    return memoryValue.data
  }

  try {
    const raw = sessionStorage.getItem(`${GET_CACHE_PREFIX}${key}`)
    if (!raw) return undefined
    const parsed = JSON.parse(raw)
    if (Date.now() - parsed.savedAt >= maxAge) {
      sessionStorage.removeItem(`${GET_CACHE_PREFIX}${key}`)
      return undefined
    }
    requestCache.set(key, parsed)
    return parsed.data
  } catch {
    return undefined
  }
}

function writeSessionCache(key, data) {
  const value = { data, savedAt: Date.now() }
  requestCache.set(key, value)
  try {
    sessionStorage.setItem(`${GET_CACHE_PREFIX}${key}`, JSON.stringify(value))
  } catch {
    // A full or disabled sessionStorage must never block the application.
  }
}

function clearGetCache(matcher = null) {
  for (const key of requestCache.keys()) {
    if (!matcher || matcher(key)) requestCache.delete(key)
  }

  try {
    for (let index = sessionStorage.length - 1; index >= 0; index -= 1) {
      const storageKey = sessionStorage.key(index)
      if (!storageKey?.startsWith(GET_CACHE_PREFIX)) continue
      const cacheKey = storageKey.slice(GET_CACHE_PREFIX.length)
      if (!matcher || matcher(cacheKey)) sessionStorage.removeItem(storageKey)
    }
  } catch {
    // Ignore storage cleanup failures.
  }
}

function invalidateAfterMutation(path) {
  const resources = ['/dashboard', '/notes', '/tags', '/collections', '/suggestions', '/knowledge-graph', '/model-calls']
  const affected = resources.filter((resource) => path.startsWith(resource) || path.includes(resource.slice(1)))
  clearGetCache((key) => affected.some((resource) => key.includes(resource)))
  clearGetCache((key) => key.includes('/dashboard/summary'))
}


export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}


export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}


export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_CACHE_KEY)
  clearGetCache()
}


function buildQuery(params = {}) {
  const query = new URLSearchParams()

  Object.entries(params).forEach(([key, value]) => {
    if (
      value !== undefined &&
      value !== null &&
      value !== ''
    ) {
      query.set(key, value)
    }
  })

  const value = query.toString()

  return value ? `?${value}` : ''
}


async function apiFetch(
  path,
  options = {},
  includeMeta = false,
) {
  const method = String(options.method || 'GET').toUpperCase()
  const isGet = method === 'GET' && !includeMeta && !options.signal
  const cacheKey = isGet ? getCacheKey(path) : null

  if (isGet) {
    const cached = readSessionCache(cacheKey, cacheDurationFor(path))
    if (cached !== undefined) return cached
    if (inFlightRequests.has(cacheKey)) return inFlightRequests.get(cacheKey)
  }

  const request = (async () => {
    const controller = new AbortController()
    const timeoutId = window.setTimeout(() => controller.abort(), 25_000)
    const token = getToken()
    const headers = { ...options.headers }

    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = headers['Content-Type'] || 'application/json'
    }

    if (token) headers.Authorization = `Bearer ${token}`

    try {
      const response = await fetch(`${BACKEND_URL}${path}`, {
        ...options,
        headers,
        signal: options.signal || controller.signal,
      })

      const contentType = response.headers.get('content-type') || ''
      const data = contentType.includes('application/json')
        ? await response.json().catch(() => null)
        : null

      if (!response.ok) {
        if (response.status === 401) clearToken()
        const detail = data?.detail
        const message = Array.isArray(detail)
          ? detail.map((item) => item.msg).join(', ')
          : detail || 'Something went wrong'
        throw new Error(message)
      }

      const result = response.status === 204 ? null : data

      if (isGet) writeSessionCache(cacheKey, result)
      if (method !== 'GET') invalidateAfterMutation(path)

      if (path === '/auth/me' && result) {
        try {
          localStorage.setItem(USER_CACHE_KEY, JSON.stringify(result))
        } catch {
          // Storage can be unavailable in private or restricted browser modes.
        }
      }

      return includeMeta
        ? { data: result, status: response.status, headers: response.headers }
        : result
    } finally {
      window.clearTimeout(timeoutId)
    }
  })()

  if (isGet) {
    inFlightRequests.set(cacheKey, request)
    request.then(
      () => inFlightRequests.delete(cacheKey),
      () => inFlightRequests.delete(cacheKey),
    )
  }

  return request
}

export function register(email, password) {
  return apiFetch('/auth/register', {
    method: 'POST',
    body: JSON.stringify({
      email,
      password,
    }),
  })
}


export function login(email, password) {
  return apiFetch('/auth/login', {
    method: 'POST',
    body: JSON.stringify({
      email,
      password,
    }),
  })
}


export function getMe() {
  return apiFetch('/auth/me')
}


export function listNotes(filters = {}) {
  return apiFetch(
    `/notes${buildQuery(filters)}`,
  )
}


export function searchNotes(
  q,
  filters = {},
) {
  return apiFetch(
    `/notes/search${buildQuery({
      q,
      ...filters,
    })}`,
  )
}


export function createNote(
  title,
  body_md = '',
  collection_id = null,
) {
  return apiFetch('/notes', {
    method: 'POST',
    body: JSON.stringify({
      title,
      body_md,
      collection_id,
    }),
  })
}


export function getNote(id) {
  return apiFetch(`/notes/${id}`)
}


export function getRelatedNotes(
  id,
  limit = 5,
) {
  return apiFetch(
    `/notes/${id}/related${buildQuery({
      limit,
    })}`,
  )
}


export function updateNote(
  id,
  updates,
  options = {},
) {
  return apiFetch(
    `/notes/${id}`,
    {
      method: 'PUT',
      body: JSON.stringify(updates),
    },
    options.includeMeta === true,
  )
}


export function deleteNote(id) {
  return apiFetch(`/notes/${id}`, {
    method: 'DELETE',
  })
}


export function listTags() {
  return apiFetch('/tags')
}


export function createTag(name) {
  return apiFetch('/tags', {
    method: 'POST',
    body: JSON.stringify({
      name,
    }),
  })
}


export function updateTag(id, name) {
  return apiFetch(`/tags/${id}`, {
    method: 'PUT',
    body: JSON.stringify({
      name,
    }),
  })
}


export function deleteTag(id) {
  return apiFetch(`/tags/${id}`, {
    method: 'DELETE',
  })
}


export function attachTagToNote(
  noteId,
  name,
) {
  return apiFetch(
    `/tags/notes/${noteId}`,
    {
      method: 'POST',
      body: JSON.stringify({
        name,
      }),
    },
  )
}


export function removeTagFromNote(
  noteId,
  tagId,
) {
  return apiFetch(
    `/tags/notes/${noteId}/${tagId}`,
    {
      method: 'DELETE',
    },
  )
}


export function listCollections() {
  return apiFetch('/collections')
}


export function createCollection(name) {
  return apiFetch('/collections', {
    method: 'POST',
    body: JSON.stringify({
      name,
    }),
  })
}


export function updateCollection(
  id,
  name,
) {
  return apiFetch(
    `/collections/${id}`,
    {
      method: 'PUT',
      body: JSON.stringify({
        name,
      }),
    },
  )
}


export function deleteCollection(id) {
  return apiFetch(
    `/collections/${id}`,
    {
      method: 'DELETE',
    },
  )
}

export function submitBrainDump(raw_text) {
  return apiFetch('/brain-dumps', {
    method: 'POST',
    body: JSON.stringify({ raw_text }),
  })
}

export function getBrainDumpStatus(id) {
  return apiFetch(`/brain-dumps/${id}/status`)
}

export function getBrainDump(id) {
  return apiFetch(`/brain-dumps/${id}`)
}


export function getBrainDumpSuggestion(id) {
  return apiFetch(
    `/brain-dumps/${id}/suggestion`,
  )
}


export function acceptBrainDumpSuggestion(
  id,
  updates = {},
) {
  return apiFetch(
    `/brain-dumps/${id}/suggestion/accept`,
    {
      method: 'POST',
      body: JSON.stringify({
        title:
          updates.title?.trim() || null,
        body_md:
          updates.body_md ?? null,
        tags:
          Array.isArray(updates.tags)
            ? updates.tags
            : null,
        selected_related_note_ids:
          Array.isArray(updates.selected_related_note_ids)
            ? updates.selected_related_note_ids
            : null,
      }),
    },
  )
}


export function rejectBrainDumpSuggestion(
  id,
  reason = null,
) {
  return apiFetch(
    `/brain-dumps/${id}/suggestion/reject`,
    {
      method: 'POST',
      body: JSON.stringify({
        reason:
          reason?.trim() || null,
      }),
    },
  )
}


export function getModelCallDashboard(
  limit = 25,
) {
  return apiFetch(
    `/model-calls/dashboard${buildQuery({
      limit,
    })}`,
  )
}


export function listAISuggestions(
  status = null,
  limit = 50,
  offset = 0,
) {
  return apiFetch(
    `/suggestions${buildQuery({
      status,
      limit,
      offset,
    })}`,
  )
}

export function getAISuggestion(id) {
  return apiFetch(`/suggestions/${id}`)
}

let dashboardSummaryCache = null
let dashboardSummaryCachedAt = 0
let dashboardSummaryRequest = null
const DASHBOARD_CACHE_MS = 30_000

export function getDashboardSummary(options = {}) {
  const now = Date.now()
  const force = options.force === true

  if (
    !force &&
    dashboardSummaryCache &&
    now - dashboardSummaryCachedAt < DASHBOARD_CACHE_MS
  ) {
    return Promise.resolve(dashboardSummaryCache)
  }

  if (!force && dashboardSummaryRequest) {
    return dashboardSummaryRequest
  }

  dashboardSummaryRequest = apiFetch('/dashboard/summary')
    .then((data) => {
      dashboardSummaryCache = data
      dashboardSummaryCachedAt = Date.now()
      return data
    })
    .finally(() => {
      dashboardSummaryRequest = null
    })

  return dashboardSummaryRequest
}

export function clearDashboardSummaryCache() {
  dashboardSummaryCache = null
  dashboardSummaryCachedAt = 0
}


export function getBrainDumpGaps(id) {
  return apiFetch(`/brain-dumps/${id}/gaps`)
}

export function inspectBrainDumpGraph() {
  return apiFetch('/brain-dumps/graph/inspect')
}


export function importBrainDumpFile(file, instruction = 'Import this file into my notes.') {
  const form = new FormData()
  form.append('file', file)
  form.append('instruction', instruction)
  return apiFetch('/file-imports/brain-dump', {
    method: 'POST',
    body: form,
  })
}

export function inspectMCPServer() {
  return apiFetch('/file-imports/mcp/inspect')
}


export function getKnowledgeGraph(filters = {}) {
  return apiFetch(
    `/knowledge-graph${buildQuery(filters)}`,
  )
}

export function warmBackend() {
  if (backendWarmRequest) return backendWarmRequest
  backendWarmRequest = fetch(`${BACKEND_URL}/health`, {
    method: 'GET',
    cache: 'no-store',
  })
    .catch(() => null)
    .finally(() => {
      window.setTimeout(() => { backendWarmRequest = null }, 15_000)
    })
  return backendWarmRequest
}

export function startBackendKeepAlive() {
  warmBackend()
  if (keepAliveTimer) return () => undefined
  keepAliveTimer = window.setInterval(warmBackend, 4 * 60 * 1000)
  return () => {
    if (keepAliveTimer) window.clearInterval(keepAliveTimer)
    keepAliveTimer = null
  }
}

export function getCachedUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_CACHE_KEY) || 'null')
  } catch {
    return null
  }
}

export function prefetchAppData() {
  if (!getToken()) return Promise.resolve([])
  return Promise.allSettled([
    getMe(),
    getDashboardSummary(),
    listNotes(),
    listTags(),
    listCollections(),
    listAISuggestions(),
    getKnowledgeGraph(),
    getModelCallDashboard(50),
  ])
}

export function resetPasswordDirect(email, newPassword) {
  return apiFetch('/auth/password-reset/direct', {
    method: 'POST',
    body: JSON.stringify({
      email,
      new_password: newPassword,
    }),
  })
}

export function deleteAccount(password, confirmation = 'DELETE') {
  return apiFetch('/auth/account', {
    method: 'DELETE',
    body: JSON.stringify({
      password,
      confirmation,
    }),
  })
}

