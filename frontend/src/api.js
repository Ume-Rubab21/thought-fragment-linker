const BACKEND_URL =
  import.meta.env.VITE_BACKEND_URL ||
  'http://localhost:8000'

const TOKEN_KEY = 'tfl_token'


export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}


export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}


export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
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
  const token = getToken()
  const headers = {
    ...options.headers,
  }

  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] =
      headers['Content-Type'] ||
      'application/json'
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const response = await fetch(
    `${BACKEND_URL}${path}`,
    {
      ...options,
      headers,
    },
  )

  const contentType =
    response.headers.get('content-type') || ''

  const data = contentType.includes(
    'application/json',
  )
    ? await response.json().catch(() => null)
    : null

  if (!response.ok) {
    if (response.status === 401) {
      clearToken()
    }

    const detail = data?.detail

    const message = Array.isArray(detail)
      ? detail
          .map((item) => item.msg)
          .join(', ')
      : detail || 'Something went wrong'

    throw new Error(message)
  }

  const result =
    response.status === 204
      ? null
      : data

  if (includeMeta) {
    return {
      data: result,
      status: response.status,
      headers: response.headers,
    }
  }

  return result
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