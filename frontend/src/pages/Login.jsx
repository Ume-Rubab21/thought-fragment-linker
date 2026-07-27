import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { login, setToken } from '../api'
import AuthShowcase from '../components/AuthShowcase'
import Icon from '../components/Icon'

function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    setEmail(localStorage.getItem('tfl_remember_email') || '')
  }, [])

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      const data = await login(email, password)
      setToken(data.access_token)
      localStorage.setItem('tfl_remember_email', email)
      navigate('/dashboard')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShowcase title="Welcome back to ThoughtLinker">
      <form onSubmit={handleSubmit}>
        <label className="auth-field">
          <span>Email Address</span>
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="Enter your email..."
            autoComplete="email"
            required
          />
        </label>

        <label className="auth-field">
          <span>Password</span>
          <span className="auth-password-control">
            <input
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Password"
              autoComplete="current-password"
              required
            />
            <button
              type="button"
              className="auth-password-toggle"
              onClick={() => setShowPassword((visible) => !visible)}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              <Icon name={showPassword ? 'eyeOff' : 'eye'} size={15} />
            </button>
          </span>
        </label>

        <div className="auth-forgot-row">
          <button type="button" onClick={() => setError('Password reset is not part of the current build.')}>Forgot Password?</button>
        </div>

        {error && <div className="auth-error" role="alert">{error}</div>}

        <button className="auth-submit" type="submit" disabled={loading}>
          {loading ? 'Logging In…' : 'Log In'}
        </button>
      </form>

      <p className="auth-footer">
        New to ThoughtLinker? <Link to="/register">[link to create account]</Link>
      </p>
    </AuthShowcase>
  )
}

export default Login
