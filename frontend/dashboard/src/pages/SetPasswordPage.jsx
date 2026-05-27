import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, CheckCircle } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'

const API_ROOT = (typeof window !== 'undefined' &&
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'))
  ? '' : 'https://api.spacecoaststudios.com'

export default function SetPasswordPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { login: authLogin } = useAuth()
  const token = searchParams.get('token') || ''
  const isReset = searchParams.get('mode') === 'reset'

  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [done, setDone] = useState(false)

  useEffect(() => {
    if (!token) setError('Invalid or missing link. Please contact support.')
  }, [token])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (password.length < 8) { setError('Password must be at least 8 characters'); return }
    if (password !== confirm)  { setError('Passwords do not match'); return }

    setLoading(true)
    try {
      const res = await fetch(`${API_ROOT}/api/auth/set-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, password, confirm_password: confirm }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Something went wrong')

      // Auto-login with the tokens returned from set-password
      if (data.access_token) {
        localStorage.setItem('access_token', data.access_token)
        if (data.refresh_token) localStorage.setItem('refresh_token', data.refresh_token)
        // Password resets go to dashboard; initial account setup goes to the setup wizard
        setTimeout(() => navigate(isReset ? '/' : '/setup', { replace: true }), 800)
      }
      setDone(true)
    } catch (err) {
      setError(err.message)
    }
    setLoading(false)
  }

  if (done) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 w-full max-w-md p-8 text-center">
          <div className="w-14 h-14 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle size={28} className="text-green-600" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">
            {isReset ? 'Password reset!' : 'Password set!'}
          </h2>
          <p className="text-gray-500 text-sm mb-6">You can now log in to your dashboard.</p>
          <button
            onClick={() => navigate('/login')}
            className="w-full bg-blue-600 text-white py-2.5 rounded-lg font-medium hover:bg-blue-700"
          >
            Go to Login
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 w-full max-w-md p-8">
        {/* Logo / branding */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Space Coast Studios</h1>
          <p className="text-gray-500 text-sm mt-1">
            {isReset ? 'Choose a new password for your account' : 'Set your account password to get started'}
          </p>
        </div>

        {error && (
          <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg text-sm mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <div className="relative">
              <input
                type={showPw ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Min. 8 characters"
                className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm pr-10 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                required
                autoFocus
              />
              <button
                type="button"
                onClick={() => setShowPw(v => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Confirm Password</label>
            <input
              type={showPw ? 'text' : 'password'}
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              placeholder="Re-enter your password"
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading || !token}
            className="w-full bg-blue-600 text-white py-2.5 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Saving…' : (isReset ? 'Reset Password' : 'Set Password & Continue')}
          </button>
        </form>

        <p className="text-center text-xs text-gray-400 mt-6">
          Having trouble?{' '}
          <a href="mailto:support@spacecoaststudios.com" className="text-blue-600 hover:underline">
            Contact support
          </a>
        </p>
      </div>
    </div>
  )
}
