import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getMe, clearToken } from '../api'
import './Dashboard.css'

function Dashboard() {
  const [user, setUser] = useState(null)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    getMe()
      .then(setUser)
      .catch(() => setError('Could not load your account'))
  }, [])

  function handleLogout() {
    clearToken()
    navigate('/login')
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
        <button onClick={handleLogout}>Log out</button>
      </div>
      {error && <p className="auth-error">{error}</p>}
      {user && <p>Logged in as: <strong>{user.email}</strong></p>}
      <p style={{ color: '#888' }}>Notes will live here — coming in later steps.</p>
    </div>
  )
}

export default Dashboard