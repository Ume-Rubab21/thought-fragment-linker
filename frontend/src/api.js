const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

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

// Every backend call goes through this function. It automatically
// attaches "Authorization: Bearer <token>" if the user is logged in,
// and throws a readable error if the backend responds with a problem.
async function apiFetch(path, options = {}) {
  const token = getToken()

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${BACKEND_URL}${path}`, {
    ...options,
    headers,
  })

  const data = await response.json().catch(() => null)

  if (!response.ok) {
    const message = data?.detail || 'Something went wrong'
    throw new Error(message)
  }

  return data
}

export function register(email, password) {
  return apiFetch('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export function login(email, password) {
  return apiFetch('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export function getMe() {
  return apiFetch('/auth/me')
}

export function listNotes() {
  return apiFetch('/notes')
}

export function createNote(title, body_md = '') {
  return apiFetch('/notes', {
    method: 'POST',
    body: JSON.stringify({ title, body_md }),
  })
}

export function getNote(id) {
  return apiFetch(`/notes/${id}`)
}

export function updateNote(id, updates) {
  return apiFetch(`/notes/${id}`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  })
}

export function deleteNote(id) {
  return apiFetch(`/notes/${id}`, {
    method: 'DELETE',
  })
}