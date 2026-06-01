import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { CheckCircle, Mail, ArrowRight } from 'lucide-react'

const API_ROOT = (typeof window !== 'undefined' &&
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'))
  ? '' : 'https://api.spacecoaststudios.com'

export default function WelcomePage() {
  const [searchParams] = useSearchParams()
  const sessionId = searchParams.get('session_id') || ''

  // Stripe will include session_id on success — we just use it for display;
  // provisioning happens server-side in the webhook.
  const [email, setEmail] = useState('')

  useEffect(() => {
    // Optionally retrieve session email from Stripe checkout session
    if (!sessionId) return
    fetch(`${API_ROOT}/api/billing/checkout-session?session_id=${encodeURIComponent(sessionId)}`)
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data?.email) setEmail(data.email) })
      .catch(() => {})
  }, [sessionId])

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-lg border border-gray-100 w-full max-w-lg p-10 text-center">

        {/* Success icon */}
        <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <CheckCircle size={40} className="text-green-600" />
        </div>

        <h1 className="text-3xl font-bold text-gray-900 mb-3">
          Payment successful!
        </h1>
        <p className="text-gray-600 mb-6 text-lg leading-relaxed">
          Welcome to Launchpad.{' '}
          {email
            ? <>We've sent a setup link to <strong>{email}</strong>.</>
            : <>Check your email for a link to set your password and access your new dashboard.</>
          }
        </p>

        {/* Steps */}
        <div className="bg-gray-50 rounded-xl p-6 mb-8 text-left space-y-4">
          <p className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">What happens next</p>

          <div className="flex items-start gap-3">
            <div className="w-7 h-7 rounded-full bg-blue-600 text-white text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">1</div>
            <div>
              <p className="font-semibold text-gray-900 text-sm">Check your email</p>
              <p className="text-gray-500 text-sm">You'll receive a "Set your password" link within a few minutes. Check your spam folder if you don't see it.</p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="w-7 h-7 rounded-full bg-blue-600 text-white text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">2</div>
            <div>
              <p className="font-semibold text-gray-900 text-sm">Set your password</p>
              <p className="text-gray-500 text-sm">Click the link to create your account password and log in to your dashboard.</p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="w-7 h-7 rounded-full bg-blue-600 text-white text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">3</div>
            <div>
              <p className="font-semibold text-gray-900 text-sm">We'll reach out to onboard you</p>
              <p className="text-gray-500 text-sm">A member of the Launchpad team will contact you within one business day to get your platform configured.</p>
            </div>
          </div>
        </div>

        {/* Email CTA */}
        <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
          <Mail size={15} className="text-gray-400" />
          <span>
            Need help?{' '}
            <a href="mailto:support@spacecoaststudios.com" className="text-blue-600 font-medium hover:underline">
              support@spacecoaststudios.com
            </a>
          </span>
        </div>

        {/* Go to login */}
        <div className="mt-6">
          <a
            href="/login"
            className="inline-flex items-center gap-2 text-sm font-medium text-gray-500 hover:text-gray-800 transition-colors"
          >
            Go to login <ArrowRight size={14} />
          </a>
        </div>
      </div>
    </div>
  )
}
