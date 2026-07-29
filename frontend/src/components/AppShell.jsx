import { useEffect, useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { clearToken, createNote, getMe } from '../api'
import Brand from './Brand'
import Icon from './Icon'

const navItems = [
  {
    to: '/notes',
    label: 'All Notes',
    icon: 'notes',
  },
  {
    to: '/brain-dump',
    label: 'Brain Dump',
    icon: 'brain',
  },
  {
    to: '/search',
    label: 'Search',
    icon: 'search',
  },
  {
    to: '/tags',
    label: 'Tags',
    icon: 'tag',
  },
  {
    to: '/collections',
    label: 'Collections',
    icon: 'folder',
  },
  {
    to: '/settings',
    label: 'Settings',
    icon: 'settings',
  },
]

export default function AppShell({
  title,
  subtitle,
  actions,
  children,
  contentClassName = '',
}) {
  const navigate = useNavigate()

  const [user, setUser] = useState(null)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [creatingNote, setCreatingNote] = useState(false)

  useEffect(() => {
    getMe()
      .then(setUser)
      .catch(() => {})
  }, [])

  function logout() {
    clearToken()
    navigate('/login')
  }

  async function handleNewNote() {
    if (creatingNote) {
      return
    }

    setCreatingNote(true)

    try {
      const note = await createNote(
        'Untitled note',
        '<p></p>',
        null,
      )

      setMobileOpen(false)
      navigate(`/notes/${note.id}`)
    } catch (error) {
      window.alert(
        error.message || 'Unable to create a new note.',
      )
    } finally {
      setCreatingNote(false)
    }
  }

  function openBrainDump() {
    setMobileOpen(false)
    navigate('/brain-dump')
  }

  return (
    <div className="app-shell">
      <aside
        className={`app-sidebar ${
          mobileOpen ? 'is-open' : ''
        }`}
      >
        <div className="sidebar-brand-full">
          <Brand />
        </div>

        <div className="sidebar-brand-compact">
          <Brand compact />
        </div>

        <nav
          className="app-nav"
          aria-label="Main navigation"
        >
          <NavLink
            to="/dashboard"
            end
            className={({ isActive }) =>
              `app-nav__item ${
                isActive ? 'is-active' : ''
              }`
            }
            onClick={() => setMobileOpen(false)}
          >
            <Icon name="dashboard" size={18} />
            <span>Dashboard</span>
          </NavLink>

          <button
            type="button"
            className="app-nav__item app-nav__item--new-note"
            onClick={handleNewNote}
            disabled={creatingNote}
            title="Create a new note"
          >
            <Icon name="plus" size={18} />

            <span>
              {creatingNote ? 'Creating…' : 'New note'}
            </span>
          </button>

          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `app-nav__item ${
                  isActive ? 'is-active' : ''
                }`
              }
              onClick={() => setMobileOpen(false)}
            >
              <Icon name={item.icon} size={18} />
              <span>{item.label}</span>
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
            Quick capture
          </span>

          <strong>
            Thoughts do not need to be perfect.
          </strong>

          <p>
            Use Brain Dump to capture them first. You can
            organize and edit them later.
          </p>

          <button
            type="button"
            onClick={openBrainDump}
          >
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
              <strong>
                {user?.email?.split('@')[0] || 'User'}
              </strong>

              <small>
                {user?.email || 'Signed in'}
              </small>
            </span>
          </div>

          <button
            type="button"
            className="icon-button sidebar-logout"
            onClick={logout}
            title="Log out"
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

            <div>
              <h1>{title}</h1>

              {subtitle && (
                <p>{subtitle}</p>
              )}
            </div>
          </div>

          <div className="app-header__actions">
            {actions}

            <button
              type="button"
              className="icon-button"
              title="Theme"
            >
              <Icon name="sun" />
            </button>

            <button
              type="button"
              className="icon-button"
              title="Notifications"
            >
              <Icon name="bell" />
            </button>

            <span className="header-avatar">
              {user?.email?.[0]?.toUpperCase() || 'U'}
            </span>
          </div>
        </header>

        <div
          className={`app-content ${contentClassName}`}
        >
          {children}
        </div>
      </main>
    </div>
  )
}