import { useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { clearToken, getToken } from '../api'

const INACTIVITY_MS = 15 * 60 * 1000
const LAST_ACTIVITY = 'tfl_last_activity'

export default function SessionManager() {
  const location = useLocation()
  const navigate = useNavigate()

  useEffect(() => {
    if (!getToken()) return
    let timer
    const logout = () => { clearToken(); localStorage.removeItem(LAST_ACTIVITY); navigate('/login', { replace: true, state: { message: 'You were logged out after 15 minutes of inactivity.' } }) }
    const schedule = () => {
      window.clearTimeout(timer)
      const last = Number(localStorage.getItem(LAST_ACTIVITY) || Date.now())
      const remaining = INACTIVITY_MS - (Date.now() - last)
      if (remaining <= 0) return logout()
      timer = window.setTimeout(logout, remaining)
    }
    const activity = () => { localStorage.setItem(LAST_ACTIVITY, String(Date.now())); schedule() }
    const visibility = () => document.visibilityState === 'visible' && schedule()
    if (!localStorage.getItem(LAST_ACTIVITY)) activity(); else schedule()
    const events = ['pointerdown', 'keydown', 'scroll', 'touchstart']
    events.forEach((name) => window.addEventListener(name, activity, { passive: true }))
    document.addEventListener('visibilitychange', visibility)
    return () => { window.clearTimeout(timer); events.forEach((name) => window.removeEventListener(name, activity)); document.removeEventListener('visibilitychange', visibility) }
  }, [location.pathname, navigate])
  return null
}
