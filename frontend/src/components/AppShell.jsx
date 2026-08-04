import { useEffect, useMemo, useRef, useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { clearToken, createNote, getCachedUser, getMe, prefetchAppData } from '../api'
import Brand from './Brand'
import Icon from './Icon'
import { getPreferences } from '../utils/preferences'
import { t } from '../utils/i18n'
import {
  clearNotifications,
  getNotifications,
  markAllNotificationsRead,
} from '../utils/notifications'
import { getEffectiveTheme, getSavedTheme, saveTheme } from '../utils/theme'

const navItems = [
  { to: '/brain-dump', key: 'brainDump', icon: 'plus' },
  { to: '/notes', key: 'allNotes', icon: 'notes' },
  { to: '/search', key: 'search', icon: 'search' },
  { to: '/tags', key: 'tags', icon: 'tag' },
  { to: '/collections', key: 'collections', icon: 'folder' },
  { to: '/ai-suggestions', key: 'aiSuggestions', icon: 'sparkles' },
  { to: '/model-routing', key: 'modelRouting', icon: 'brain' },
  { to: '/knowledge-graph', key: 'knowledgeGraph', icon: 'connections' },
  { to: '/settings', key: 'settings', icon: 'settings' },
]

export default function AppShell({
  title,
  subtitle,
  actions,
  children,
  contentClassName = '',
  titleVariant = '',
}) {
  const navigate = useNavigate()
  const notificationRef = useRef(null)

  const [user, setUser] = useState(getCachedUser)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [creatingNote, setCreatingNote] = useState(false)
  const [preferences, setPreferences] = useState(getPreferences)
  const [theme, setTheme] = useState(getSavedTheme)
  const [notifications, setNotifications] = useState(getNotifications)
  const [notificationOpen, setNotificationOpen] = useState(false)

  useEffect(() => {
    if (!user) getMe().then(setUser).catch(() => {})
    const idleId = window.requestIdleCallback
      ? window.requestIdleCallback(() => prefetchAppData())
      : window.setTimeout(() => prefetchAppData(), 250)
    return () => {
      if (window.cancelIdleCallback && typeof idleId === 'number') {
        window.cancelIdleCallback(idleId)
      } else {
        window.clearTimeout(idleId)
      }
    }
  }, [user])

  useEffect(() => {
    const syncPreferences = (event) => {
      setPreferences(event.detail || getPreferences())
    }
    const syncTheme = (event) => {
      setTheme(event.detail?.theme || getSavedTheme())
    }
    const syncNotifications = (event) => {
      setNotifications(event.detail || getNotifications())
    }

    window.addEventListener('thoughtlinker-preferences-change', syncPreferences)
    window.addEventListener('thoughtlinker-theme-change', syncTheme)
    window.addEventListener('thoughtlinker-notifications-change', syncNotifications)

    return () => {
      window.removeEventListener(
        'thoughtlinker-preferences-change',
        syncPreferences,
      )
      window.removeEventListener('thoughtlinker-theme-change', syncTheme)
      window.removeEventListener(
        'thoughtlinker-notifications-change',
        syncNotifications,
      )
    }
  }, [])

  useEffect(() => {
    function closeOnOutsideClick(event) {
      if (
        notificationOpen &&
        notificationRef.current &&
        !notificationRef.current.contains(event.target)
      ) {
        setNotificationOpen(false)
      }
    }

    document.addEventListener('mousedown', closeOnOutsideClick)
    return () => document.removeEventListener('mousedown', closeOnOutsideClick)
  }, [notificationOpen])

  const language = preferences.language
  const unreadCount = notifications.filter((item) => !item.read).length
  const effectiveTheme = getEffectiveTheme(theme)

  const translatedTitle = useMemo(() => {
    if (title === 'Dashboard') return t('dashboard', language)
    if (title === 'Settings') return t('settings', language)
    return title
  }, [language, title])

  const translatedSubtitle = useMemo(() => {
    if (title === 'Dashboard') return t('dashboardSubtitle', language)
    if (title === 'Settings') return t('settingsSubtitle', language)
    return subtitle
  }, [language, subtitle, title])

  function logout() {
    clearToken()
    navigate('/login')
  }

  async function handleNewNote() {
    if (creatingNote) return
    setCreatingNote(true)

    try {
      const note = await createNote('Untitled note', '<p></p>', null)
      setMobileOpen(false)
      navigate(`/notes/${note.id}`)
    } catch (error) {
      window.alert(error.message || 'Unable to create a new note.')
    } finally {
      setCreatingNote(false)
    }
  }

  function openBrainDump() {
    setMobileOpen(false)
    navigate('/brain-dump')
  }

  function cycleTheme() {
    const next = effectiveTheme === 'dark' ? 'light' : 'dark'
    saveTheme(next)
    setTheme(next)
  }

  function toggleNotifications() {
    const nextOpen = !notificationOpen
    setNotificationOpen(nextOpen)

    if (nextOpen && unreadCount) {
      setNotifications(markAllNotificationsRead())
    }
  }

  return (
    <div className="app-shell">
      <aside className={`app-sidebar ${mobileOpen ? 'is-open' : ''}`}>
        <div className="sidebar-brand-full"><Brand /></div>
        <div className="sidebar-brand-compact"><Brand compact /></div>

        <nav className="app-nav" aria-label="Main navigation">
          <NavLink
            to="/dashboard"
            end
            className={({ isActive }) =>
              `app-nav__item ${isActive ? 'is-active' : ''}`
            }
            onClick={() => setMobileOpen(false)}
          >
            <Icon name="dashboard" size={18} />
            <span>{t('dashboard', language)}</span>
          </NavLink>

          <button
            type="button"
            className="app-nav__item app-nav__item--new-note"
            onClick={handleNewNote}
            disabled={creatingNote}
          >
            <Icon name="plus" size={18} />
            <span>
              {creatingNote
                ? t('creating', language)
                : t('newNote', language)}
            </span>
          </button>

          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `app-nav__item ${isActive ? 'is-active' : ''}`
              }
              onClick={() => setMobileOpen(false)}
            >
              <Icon name={item.icon} size={18} />
              <span>{t(item.key, language)}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-helper">
          <div className="sidebar-helper__art">
            <span
              className="sidebar-helper__brain"
              role="img"
              aria-label="Brain"
            >
              🧠
            </span>
            <span className="sidebar-helper__spark sidebar-helper__spark--one">
              ✦
            </span>
            <span className="sidebar-helper__spark sidebar-helper__spark--two">
              ✦
            </span>
          </div>
          <span className="sidebar-helper__label">
            {t('quickCapture', language)}
          </span>
          <strong>{t('quickCaptureText', language)}</strong>
          <p>
            Use Brain Dump to capture them first. You can organize and edit
            them later.
          </p>
          <button type="button" onClick={openBrainDump}>
            <span>Start writing</span>
            <Icon name="chevronRight" size={14} />
          </button>
        </div>

        <div className="sidebar-footer">
          <div className="sidebar-user">
            <span className="avatar">
              {user?.email?.[0]?.toUpperCase() || 'U'}
            </span>
            <span className="sidebar-user__copy">
              <strong>{user?.email?.split('@')[0] || 'User'}</strong>
              <small>{user?.email || 'Signed in'}</small>
            </span>
          </div>
          <button
            type="button"
            className="icon-button sidebar-logout"
            onClick={logout}
            title={t('logOut', language)}
          >
            <Icon name="logout" size={18} />
          </button>
        </div>
      </aside>

      {mobileOpen && (
        <button
          type="button"
          className="sidebar-scrim"
          aria-label="Close menu"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <main className="app-main">
        <header className="app-header">
          <div className="app-header__left">
            <button
              type="button"
              className="mobile-menu-button"
              onClick={() => setMobileOpen(true)}
              aria-label="Open menu"
            >
              <Icon name="list" size={20} />
            </button>

            <div
              className={`app-title-block ${
                titleVariant ? `app-title-block--${titleVariant}` : ''
              }`}
            >
              <div className="app-title-row">
                <h1>{translatedTitle}</h1>
                {titleVariant === 'dashboard' && (
                  <span
                    className="dashboard-title-sparkles"
                    aria-hidden="true"
                  >
                    ✦
                  </span>
                )}
              </div>
              {translatedSubtitle && <p>{translatedSubtitle}</p>}
            </div>
          </div>

          <div className="app-header__actions">
            {actions}

            <button
              type="button"
              className="icon-button"
              title="Toggle light and dark theme"
              onClick={cycleTheme}
            >
              <Icon name={effectiveTheme === 'dark' ? 'moon' : 'sun'} />
            </button>

            <div className="notification-center" ref={notificationRef}>
              <button
                type="button"
                className="icon-button notification-button"
                title="Notifications"
                onClick={toggleNotifications}
              >
                <Icon name="bell" />
                {unreadCount > 0 && (
                  <span className="notification-badge">
                    {Math.min(unreadCount, 9)}
                  </span>
                )}
              </button>

              {notificationOpen && (
                <section className="notification-popover">
                  <header>
                    <div>
                      <strong>Notifications</strong>
                      <small>{notifications.length} saved update(s)</small>
                    </div>
                    {notifications.length > 0 && (
                      <button
                        type="button"
                        className="text-button"
                        onClick={() => {
                          clearNotifications()
                          setNotifications([])
                        }}
                      >
                        Clear
                      </button>
                    )}
                  </header>

                  <div className="notification-list">
                    {notifications.length ? (
                      notifications.slice(0, 8).map((item) => (
                        <button
                          type="button"
                          className="notification-item"
                          key={item.id}
                          onClick={() => {
                            setNotificationOpen(false)
                            if (item.href) navigate(item.href)
                          }}
                        >
                          <span className="notification-item__icon">
                            <Icon
                              name={
                                item.type === 'ai'
                                  ? 'sparkles'
                                  : item.type === 'brainDump'
                                    ? 'brain'
                                    : item.type === 'connection'
                                      ? 'link'
                                      : 'bell'
                              }
                              size={16}
                            />
                          </span>
                          <span>
                            <strong>{item.title}</strong>
                            <small>{item.message}</small>
                          </span>
                        </button>
                      ))
                    ) : (
                      <div className="notification-empty">
                        <Icon name="bell" size={25} />
                        <strong>No new notifications</strong>
                        <small>
                          Enable and test notifications from Settings.
                        </small>
                      </div>
                    )}
                  </div>
                </section>
              )}
            </div>

            <span className="header-avatar">
              {user?.email?.[0]?.toUpperCase() || 'U'}
            </span>
          </div>
        </header>

        <div className={`app-content ${contentClassName}`}>{children}</div>
      </main>
    </div>
  )
}
