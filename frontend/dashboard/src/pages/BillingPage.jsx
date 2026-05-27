import { useState, useEffect } from 'react'
import { CreditCard, ExternalLink, CheckCircle, AlertCircle, Clock, XCircle, RefreshCw } from 'lucide-react'
import { getBillingSubscription, createBillingPortal } from '../services/api'

const TIER_LABELS = {
  starter:      'Starter',
  professional: 'Professional',
}

const TIER_FEATURES = {
  starter: [
    'AI-powered contact form responder',
    'Embeddable contact form widget',
    'Dedicated booking request page',
    'Up to 3 service types & 5 technicians',
    'Email confirmations & reminders',
    'Admin dashboard',
    'Email support (2-business-day response)',
  ],
  professional: [
    'Everything in Starter',
    'Unlimited service types & technicians',
    'Self-scheduling booking widget',
    'SMS booking agent (text-to-book)',
    'SMS confirmations, reminders & alerts',
    'On The Way technician notifications',
    'Automated Google review requests',
    'Emergency dispatch & on-call management',
    'Recurring appointment scheduling',
    'Custom AI persona & branding',
    'Priority support + monthly check-in call',
  ],
}

const STATUS_CONFIG = {
  active:    { icon: CheckCircle,   color: 'text-green-600',  bg: 'bg-green-50',  label: 'Active' },
  trialing:  { icon: Clock,         color: 'text-blue-600',   bg: 'bg-blue-50',   label: 'Trial' },
  past_due:  { icon: AlertCircle,   color: 'text-yellow-600', bg: 'bg-yellow-50', label: 'Past Due' },
  cancelled: { icon: XCircle,       color: 'text-red-600',    bg: 'bg-red-50',    label: 'Cancelled' },
  unpaid:    { icon: AlertCircle,   color: 'text-red-600',    bg: 'bg-red-50',    label: 'Unpaid' },
}

export default function BillingPage() {
  const [sub, setSub] = useState(null)
  const [loading, setLoading] = useState(true)
  const [portalLoading, setPortalLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    getBillingSubscription()
      .then(setSub)
      .catch(() => setSub(null))
      .finally(() => setLoading(false))
  }, [])

  const openPortal = async () => {
    setPortalLoading(true)
    setError('')
    try {
      const { url } = await createBillingPortal()
      window.location.href = url
    } catch (err) {
      setError(err.message)
      setPortalLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw size={24} className="animate-spin text-gray-400" />
      </div>
    )
  }

  const tier     = sub?.subscription_tier
  const status   = sub?.subscription_status
  const periodEnd = sub?.subscription_period_end
  const hasStripe = sub?.has_stripe

  const statusCfg = STATUS_CONFIG[status] || STATUS_CONFIG['active']
  const StatusIcon = statusCfg.icon

  const features = TIER_FEATURES[tier] || []

  const periodEndFormatted = periodEnd
    ? new Date(periodEnd).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
    : null

  return (
    <div className="max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Billing & Plan</h1>
        {hasStripe && (
          <button
            onClick={openPortal}
            disabled={portalLoading}
            className="flex items-center gap-2 bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 disabled:opacity-50"
          >
            {portalLoading
              ? <><RefreshCw size={15} className="animate-spin" /> Opening…</>
              : <><ExternalLink size={15} /> Manage Billing</>}
          </button>
        )}
      </div>

      {error && (
        <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg text-sm mb-4">{error}</div>
      )}

      {/* Plan card */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center">
              <CreditCard size={20} className="text-blue-600" />
            </div>
            <div>
              <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">Current Plan</p>
              <h2 className="text-xl font-bold text-gray-900">
                {tier ? TIER_LABELS[tier] : 'No active plan'}
              </h2>
            </div>
          </div>

          {status && (
            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium ${statusCfg.bg} ${statusCfg.color}`}>
              <StatusIcon size={14} />
              {statusCfg.label}
            </span>
          )}
        </div>

        {periodEndFormatted && (
          <div className="mt-4 pt-4 border-t border-gray-100">
            <p className="text-sm text-gray-500">
              {status === 'cancelled'
                ? `Access until ${periodEndFormatted}`
                : `Next billing date: ${periodEndFormatted}`}
            </p>
          </div>
        )}

        {!hasStripe && (
          <div className="mt-4 pt-4 border-t border-gray-100">
            <p className="text-sm text-gray-500">
              This account was set up manually. Contact{' '}
              <a href="mailto:support@spacecoaststudios.com" className="text-blue-600 hover:underline">
                support@spacecoaststudios.com
              </a>{' '}
              for billing questions.
            </p>
          </div>
        )}
      </div>

      {/* Features included */}
      {features.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-4">
            What's included
          </h3>
          <ul className="space-y-2.5">
            {features.map((f, i) => (
              <li key={i} className="flex items-start gap-2.5 text-sm text-gray-700">
                <CheckCircle size={16} className="text-green-500 shrink-0 mt-0.5" />
                {f}
              </li>
            ))}
          </ul>

          {tier === 'starter' && (
            <div className="mt-5 pt-5 border-t border-gray-100">
              <p className="text-sm text-gray-500 mb-3">
                Need SMS notifications, OTW alerts, and the self-scheduling widget?
              </p>
              <a
                href="mailto:support@spacecoaststudios.com?subject=Upgrade to Professional"
                className="inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
              >
                Upgrade to Professional →
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
