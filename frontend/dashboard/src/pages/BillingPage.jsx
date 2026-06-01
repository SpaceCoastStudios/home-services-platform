import { useState, useEffect } from 'react'
import { CreditCard, ExternalLink, CheckCircle, AlertCircle, Clock, XCircle, RefreshCw } from 'lucide-react'
import { getBillingSubscription, createBillingPortal, getBusinesses } from '../services/api'
import { useAuth } from '../hooks/useAuth'

const TIER_LABELS = {
  starter:      'Starter',
  professional: 'Professional',
  test:         'Test',
}

const TIER_FEATURES = {
  starter: [
    'AI-powered contact form responder',
    'Embeddable contact form widget',
    'Dedicated booking request page',
    'Up to 5 service types & 5 technicians',
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

function StatusBadge({ status }) {
  const cfg = STATUS_CONFIG[status]
  if (!cfg) return null
  const Icon = cfg.icon
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${cfg.bg} ${cfg.color}`}>
      <Icon size={12} />
      {cfg.label}
    </span>
  )
}

// ── Platform admin view — all tenants ────────────────────────────────────────

function PlatformBillingView() {
  const [businesses, setBusinesses] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getBusinesses()
      .then(setBusinesses)
      .catch(() => setBusinesses([]))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw size={24} className="animate-spin text-gray-400" />
      </div>
    )
  }

  const active     = businesses.filter(b => b.subscription_status === 'active').length
  const pastDue    = businesses.filter(b => b.subscription_status === 'past_due').length
  const cancelled  = businesses.filter(b => b.subscription_status === 'cancelled').length
  const noSub      = businesses.filter(b => !b.subscription_tier).length

  return (
    <div className="max-w-5xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Billing Overview</h1>

      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-4 mb-8 sm:grid-cols-4">
        {[
          { label: 'Total Tenants',  value: businesses.length, color: 'text-gray-900' },
          { label: 'Active',         value: active,            color: 'text-green-600' },
          { label: 'Past Due',       value: pastDue,           color: 'text-yellow-600' },
          { label: 'No Plan',        value: noSub,             color: 'text-gray-400' },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
            <p className="text-xs text-gray-500 font-medium uppercase tracking-wider mb-1">{label}</p>
            <p className={`text-3xl font-bold ${color}`}>{value}</p>
          </div>
        ))}
      </div>

      {/* Tenant table */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50">
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Business</th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Plan</th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Next Billing</th>
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Stripe</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {businesses.map(b => (
              <tr key={b.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-5 py-3.5">
                  <p className="font-medium text-gray-900">{b.name}</p>
                  <p className="text-xs text-gray-400">{b.email || '—'}</p>
                </td>
                <td className="px-5 py-3.5">
                  <span className="text-gray-700">
                    {TIER_LABELS[b.subscription_tier] || <span className="text-gray-400">—</span>}
                  </span>
                </td>
                <td className="px-5 py-3.5">
                  {b.subscription_status
                    ? <StatusBadge status={b.subscription_status} />
                    : <span className="text-gray-400 text-xs">—</span>
                  }
                </td>
                <td className="px-5 py-3.5 text-gray-500">
                  {b.subscription_period_end
                    ? new Date(b.subscription_period_end).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
                    : <span className="text-gray-400">—</span>
                  }
                </td>
                <td className="px-5 py-3.5">
                  {b.stripe_customer_id
                    ? (
                      <a
                        href={`https://dashboard.stripe.com/customers/${b.stripe_customer_id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 text-xs"
                      >
                        View <ExternalLink size={11} />
                      </a>
                    )
                    : <span className="text-gray-400 text-xs">Manual</span>
                  }
                </td>
              </tr>
            ))}
            {businesses.length === 0 && (
              <tr>
                <td colSpan={5} className="px-5 py-8 text-center text-gray-400 text-sm">No businesses yet</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Business admin view — own plan ───────────────────────────────────────────

function BusinessBillingView() {
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

  const tier           = sub?.subscription_tier
  const status         = sub?.subscription_status
  const periodEnd      = sub?.subscription_period_end
  const hasStripe      = sub?.has_stripe
  const statusCfg      = STATUS_CONFIG[status] || null
  const StatusIcon     = statusCfg?.icon
  const features       = TIER_FEATURES[tier] || []
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
                {tier ? (TIER_LABELS[tier] || tier) : 'No active plan'}
              </h2>
            </div>
          </div>

          {statusCfg && (
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

// ── Main export ───────────────────────────────────────────────────────────────

export default function BillingPage() {
  const { user } = useAuth()
  return user?.isPlatformAdmin ? <PlatformBillingView /> : <BusinessBillingView />
}
