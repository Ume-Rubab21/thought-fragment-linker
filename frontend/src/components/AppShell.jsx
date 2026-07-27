import { useEffect, useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { clearToken, getMe } from '../api'
import Brand from './Brand'
import Icon from './Icon'

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: 'dashboard' },
  { to: '/notes', label: 'All Notes', icon: 'notes' },
  { to: '/search', label: 'Search', icon: 'search' },
  { to: '/tags', label: 'Tags', icon: 'tag' },
  { to: '/collections', label: 'Collections', icon: 'folder' },
  { to: '/settings', label: 'Settings', icon: 'settings' },
]

export default function AppShell({ title, subtitle, actions, children, contentClassName = '' }) {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [mobileOpen, setMobileOpen] = useState(false)

  useEffect(() => {
    getMe().then(setUser).catch(() => {})
  }, [])

  function logout() {
    clearToken()
    navigate('/login')
  }

  return (
    <div className="app-shell">
      <aside className={`app-sidebar ${mobileOpen ? 'is-open' : ''}`}>
        <div className="sidebar-brand-full"><Brand /></div>
        <div className="sidebar-brand-compact"><Brand compact /></div>

        <nav className="app-nav" aria-label="Main navigation">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/dashboard'}
              className={({ isActive }) => `app-nav__item ${isActive ? 'is-active' : ''}`}
              onClick={() => setMobileOpen(false)}
            >
              <Icon name={item.icon} size={18} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-user">
            <span className="avatar">{user?.email?.[0]?.toUpperCase() || 'U'}</span>
            <span className="sidebar-user__copy">
              <strong>{user?.email?.split('@')[0] || 'User'}</strong>
              <small>{user?.email || 'Signed in'}</small>
            </span>
          </div>
          <button className="icon-button sidebar-logout" onClick={logout} title="Log out">
            <Icon name="logout" size={18} />
          </button>
        </div>
      </aside>

      {mobileOpen && <button className="sidebar-scrim" aria-label="Close menu" onClick={() => setMobileOpen(false)} />}

      <main className="app-main">
        <header className="app-header">
          <div className="app-header__left">
            <button className="mobile-menu-button" onClick={() => setMobileOpen(true)} aria-label="Open menu">
              <Icon name="list" size={20} />
            </button>
            <div>
              <h1>{title}</h1>
              {subtitle && <p>{subtitle}</p>}
            </div>
          </div>
          <div className="app-header__actions">
            {actions}
            <button className="icon-button" title="Theme"><Icon name="sun" /></button>
            <button className="icon-button" title="Notifications"><Icon name="bell" /></button>
            <span className="header-avatar">{user?.email?.[0]?.toUpperCase() || 'U'}</span>
          </div>
        </header>
        <div className={`app-content ${contentClassName}`}>{children}</div>
      </main>
    </div>
  )
}
