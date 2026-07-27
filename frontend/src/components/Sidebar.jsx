import { NavLink, useNavigate } from 'react-router-dom'
import { clearToken } from '../api'

const navItems = [
  { to: '/dashboard', label: 'All Notes' },
  { to: '/search', label: 'Search' },
  { to: '/tags', label: 'Tags' },
  { to: '/collections', label: 'Collections' },
]

function Sidebar({ userEmail, onNavigate }) {
  const navigate = useNavigate()

  function handleLogout() {
    clearToken()
    navigate('/login')
  }

  return (
    <div className="w-56 bg-sidebar shrink-0 p-4 text-white/90 text-sm flex flex-col h-full">
      <div className="flex items-center gap-2 mb-8 px-1">
        <div className="w-6 h-6 rounded bg-accent shrink-0" />
        <span className="font-bold text-white">ThoughtLinker</span>
      </div>

      <nav className="space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            onClick={onNavigate}
            className={({ isActive }) =>
              `block px-2 py-1.5 rounded-lg ${
                isActive ? 'bg-white/10 text-white font-medium' : 'text-white/60 hover:text-white/90'
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto pt-4 border-t border-white/10">
        <p className="text-xs text-white/50 font-mono truncate mb-2">{userEmail}</p>
        <button
          onClick={handleLogout}
          className="w-full text-left text-xs text-white/60 hover:text-white/90"
        >
          Log out
        </button>
      </div>
    </div>
  )
}

export default Sidebar
