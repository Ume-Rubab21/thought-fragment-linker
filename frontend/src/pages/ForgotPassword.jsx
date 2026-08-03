import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import AuthShowcase from '../components/AuthShowcase'
import Icon from '../components/Icon'
import { resetPasswordDirect } from '../api'

export default function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const navigate = useNavigate()

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')

    if (password.length < 6) {
      setError('Password must contain at least 6 characters.')
      return
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setLoading(true)

    try {
      await resetPasswordDirect(email.trim(), password)

      navigate('/login', {
        replace: true,
        state: {
          message: 'Password updated successfully. Please log in.',
        },
      })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShowcase title="Reset your password" graph={false} register>
      <form onSubmit={handleSubmit}>
        <Link className="auth-back-link" to="/login" aria-label="Back to login">
          <span aria-hidden="true">←</span>
          Back to login
        </Link>

        <p className="auth-help">
          Enter your registered email and choose a new password.
        </p>

        <label className="auth-field">
          <span>Email Address</span>
          <span className="auth-input-wrap">
            <Icon name="mail" size={19} />
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="Enter your registered email"
              autoComplete="email"
              required
            />
          </span>
        </label>

        <label className="auth-field">
          <span>New Password</span>
          <span className="auth-input-wrap auth-password-control">
            <Icon name="lock" size={19} />
            <input
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Minimum 6 characters"
              autoComplete="new-password"
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

        <label className="auth-field">
          <span>Confirm Password</span>
          <span className="auth-input-wrap">
            <Icon name="lock" size={19} />
            <input
              type={showPassword ? 'text' : 'password'}
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              placeholder="Confirm your new password"
              autoComplete="new-password"
              minLength={6}
              required
            />
          </span>
        </label>

        {error && (
          <div className="auth-error" role="alert">
            {error}
          </div>
        )}

        <button className="auth-submit" type="submit" disabled={loading}>
          {loading ? 'Updating password…' : 'Update Password'}
        </button>
      </form>
    </AuthShowcase>
  )
}