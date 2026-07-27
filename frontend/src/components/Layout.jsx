import { useEffect, useState } from 'react'
import { getMe } from '../api'
import Sidebar from './Sidebar'

function Layout({ children }) {
  const [userEmail, setUserEmail] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(false)

  useEffect(() => {
    getMe()
      .then((user) => setUserEmail(user.email))
      .catch(() => {})
  }, [])

  return (
    <div className="flex min-h-screen bg-app-bg">
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <div
        className={`fixed lg:sticky top-0 z-50 lg:z-auto h-screen transition-transform duration-200 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <Sidebar userEmail={userEmail} onNavigate={() => setSidebarOpen(false)} />
      </div>

      <div className="flex-1 min-w-0 flex flex-col">
        <header className="lg:hidden flex items-center gap-3 px-4 py-3 bg-sidebar text-white shrink-0">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-1 rounded hover:bg-white/10"
            aria-label="Open menu"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <span className="font-bold text-sm">ThoughtLinker</span>
        </header>
        <main className="flex-1 min-h-0">{children}</main>
      </div>
    </div>
  )
}

export default Layout
