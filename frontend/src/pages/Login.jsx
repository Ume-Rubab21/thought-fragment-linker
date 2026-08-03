import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { login, setToken, warmBackend } from '../api'
import AuthShowcase from '../components/AuthShowcase'
import Icon from '../components/Icon'

function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    setEmail(localStorage.getItem('tfl_remember_email') || '')
    warmBackend()
  }, [])

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setLoading(true)

    try {
      const data = await login(email.trim(), password)
      localStorage.setItem('tfl_remember_email', email.trim())
      setToken(data.access_token)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShowcase title="Welcome back to ThoughtLinker">
      <form onSubmit={handleSubmit}>
        {location.state?.message && (
          <div className="auth-success" role="status">
            {location.state.message}
          </div>
        )}

        <label className="auth-field">
          <span>Email Address</span>
          <span className="auth-input-wrap">
            <Icon name="mail" size={19} />
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="Enter your email address"
              autoComplete="email"
              required
            />
          </span>
        </label>

        <label className="auth-field">
          <span>Password</span>
          <span className="auth-password-control auth-input-wrap">
            <Icon name="lock" size={19} />
            <input
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter your password"
              autoComplete="current-password"
              minLength={6}
              required
            />
            <button
              type="button"
              className="auth-password-toggle"
              onClick={() => setShowPassword((visible) => !visible)}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              <Icon name={showPassword ? 'eyeOff' : 'eye'} size={17} />
            </button>
          </span>
        </label>

        <div className="auth-forgot-row">
          <Link to="/forgot-password">Forgot Password?</Link>
        </div>

        {error && <div className="auth-error" role="alert">{error}</div>}

        <button className="auth-submit" type="submit" disabled={loading}>
          {loading ? 'Signing in…' : 'Log In'}
        </button>
      </form>

      <p className="auth-footer">
        New to ThoughtLinker? <Link to="/register">Create an account</Link>
      </p>
    </AuthShowcase>
  )
}

export default Login
