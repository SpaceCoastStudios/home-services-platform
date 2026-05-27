/**
 * First-login setup wizard for new business admins.
 * Shown automatically after setting a password for the first time.
 * Walks through 4 steps: Business Info → Branding → Notifications → Done.
 *
 * Once the client clicks "Go to Dashboard" (or "Skip for now" on any step),
 * the business is marked has_completed_setup = true and they land on the
 * normal dashboard.
 */

import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { getMyBusiness, updateBusiness } from '../services/api'
import {
  Building2, Palette, Bell, CheckCircle2, ArrowRight, ArrowLeft,
  ChevronRight, Users, Wrench, MessageSquare, LayoutDashboard,
} from 'lucide-react'

const TOTAL_STEPS = 3  // not counting the final Done screen

// ── Step progress bar ──────────────────────────────────────────────────────

function ProgressBar({ step }) {
  return (
    <div className="flex items-center gap-2 mb-8">
      {Array.from({ length: TOTAL_STEPS }, (_, i) => (
        <div key={i} className="flex items-center gap-2">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-colors ${
            i + 1 < step  ? 'bg-green-500 text-white'
            : i + 1 === step ? 'bg-blue-600 text-white'
            : 'bg-gray-200 text-gray-400'
          }`}>
            {i + 1 < step ? <CheckCircle2 size={16} /> : i + 1}
          </div>
          {i < TOTAL_STEPS - 1 && (
            <div className={`h-0.5 w-12 transition-colors ${i + 1 < step ? 'bg-green-400' : 'bg-gray-200'}`} />
          )}
        </div>
      ))}
      <span className="text-sm text-gray-400 ml-2">Step {step} of {TOTAL_STEPS}</span>
    </div>
  )
}

// ── Step 1: Business Info ──────────────────────────────────────────────────

function StepBusinessInfo({ form, onChange, onNext, onSkip }) {
  return (
    <div>
      <div className="flex items-center gap-3 mb-2">
        <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
          <Building2 size={20} className="text-blue-600" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-gray-900">Your Business</h2>
          <p className="text-sm text-gray-500">Confirm how your business appears to customers</p>
        </div>
      </div>

      <div className="mt-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Business / DBA Name <span className="text-red-500">*</span>
          </label>
          <input
            value={form.name}
            onChange={e => onChange('name', e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            placeholder="e.g. Peak Cooling & Heating"
          />
          <p className="text-xs text-gray-400 mt-1">
            Use the name your customers know you by — your DBA if different from your legal name.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
            <input
              value={form.phone}
              onChange={e => onChange('phone', e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
              placeholder="(321) 555-0100"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Website</label>
            <input
              value={form.website}
              onChange={e => onChange('website', e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
              placeholder="https://peakcooling.com"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Service Area / Address</label>
          <input
            value={form.address}
            onChange={e => onChange('address', e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            placeholder="123 Main St, Melbourne, FL 32901"
          />
        </div>
      </div>

      <StepNav onNext={onNext} onSkip={onSkip} nextLabel="Next: Branding" disableNext={!form.name?.trim()} />
    </div>
  )
}

// ── Step 2: Branding ───────────────────────────────────────────────────────

function StepBranding({ form, onChange, onNext, onBack, onSkip }) {
  return (
    <div>
      <div className="flex items-center gap-3 mb-2">
        <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
          <Palette size={20} className="text-purple-600" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-gray-900">Look & Feel</h2>
          <p className="text-sm text-gray-500">Personalize your dashboard and customer emails</p>
        </div>
      </div>

      <div className="mt-6 space-y-5">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Brand Color</label>
          <div className="flex items-center gap-3">
            <input
              type="color"
              value={form.brand_color || '#2563eb'}
              onChange={e => onChange('brand_color', e.target.value)}
              className="h-10 w-14 border border-gray-300 rounded-lg cursor-pointer p-0.5"
            />
            <input
              value={form.brand_color || '#2563eb'}
              onChange={e => onChange('brand_color', e.target.value)}
              className="w-32 border border-gray-300 rounded-lg px-3 py-2.5 text-sm font-mono focus:ring-2 focus:ring-blue-500 outline-none"
              placeholder="#2563eb"
            />
            <span className="text-xs text-gray-400">Used as the accent color in your dashboard sidebar and customer emails</span>
          </div>
        </div>

        {/* Live preview chip */}
        <div className="bg-gray-50 rounded-xl border border-gray-200 p-4">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">Preview</p>
          <div className="flex items-center gap-3">
            <div
              className="w-9 h-9 rounded-lg flex items-center justify-center text-white text-sm font-bold shrink-0"
              style={{ backgroundColor: form.brand_color || '#2563eb' }}
            >
              {(form.name || 'B').charAt(0).toUpperCase()}
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-900">{form.name || 'Your Business'}</p>
              <p className="text-xs text-gray-400">Admin Dashboard</p>
            </div>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Logo URL <span className="text-gray-400 font-normal">(optional)</span>
          </label>
          <input
            value={form.logo_url}
            onChange={e => onChange('logo_url', e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            placeholder="https://yourdomain.com/logo.png"
          />
          <p className="text-xs text-gray-400 mt-1">
            Paste a direct link to your logo. You can add this later in Settings.
          </p>
        </div>
      </div>

      <StepNav onNext={onNext} onBack={onBack} onSkip={onSkip} nextLabel="Next: Notifications" />
    </div>
  )
}

// ── Step 3: Notifications & Reviews ───────────────────────────────────────

function StepNotifications({ form, onChange, onNext, onBack, onSkip }) {
  return (
    <div>
      <div className="flex items-center gap-3 mb-2">
        <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
          <Bell size={20} className="text-amber-600" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-gray-900">AI & Notifications</h2>
          <p className="text-sm text-gray-500">Set up your AI assistant and review requests</p>
        </div>
      </div>

      <div className="mt-6 space-y-5">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            AI Assistant Name <span className="text-gray-400 font-normal">(optional)</span>
          </label>
          <input
            value={form.ai_agent_name}
            onChange={e => onChange('ai_agent_name', e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            placeholder="e.g. Peak Assistant, Riley, Max…"
          />
          <p className="text-xs text-gray-400 mt-1">
            This name appears when your AI auto-responds to customer messages. Leave blank to skip for now.
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Google Review Link <span className="text-gray-400 font-normal">(optional)</span>
          </label>
          <input
            value={form.google_review_url}
            onChange={e => onChange('google_review_url', e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            placeholder="https://g.page/r/XXXXXXXXX/review"
          />
          <p className="text-xs text-gray-400 mt-1">
            After each completed job, customers automatically receive a text asking for a review. Paste your Google review link here.
            Find it in your Google Business Profile → Ask for reviews.
          </p>
        </div>

        <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 text-sm text-blue-800">
          <strong>Tip:</strong> You can customize all notification message templates (confirmation, reminder, review request, and more) from the <strong>Notifications</strong> page in your dashboard at any time.
        </div>
      </div>

      <StepNav onNext={onNext} onBack={onBack} onSkip={onSkip} nextLabel="Finish Setup" />
    </div>
  )
}

// ── Done screen ────────────────────────────────────────────────────────────

function StepDone({ businessName, onFinish }) {
  const nextSteps = [
    { icon: Wrench, label: 'Add your services', desc: 'Define what you offer and set pricing', to: '/services' },
    { icon: Users, label: 'Add your technicians', desc: 'Create profiles for your team', to: '/technicians' },
    { icon: MessageSquare, label: 'Customize notifications', desc: 'Edit SMS and email message templates', to: '/notification-templates' },
    { icon: LayoutDashboard, label: 'Explore your dashboard', desc: 'Book appointments, manage customers, and more', to: '/' },
  ]

  return (
    <div className="text-center">
      <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
        <CheckCircle2 size={32} className="text-green-600" />
      </div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">You're all set!</h2>
      <p className="text-gray-500 mb-8">
        Welcome to Space Coast Studios, <strong className="text-gray-700">{businessName}</strong>.
        Here are a few things to do next.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-left mb-8">
        {nextSteps.map(({ icon: Icon, label, desc, to }) => (
          <Link
            key={to}
            to={to}
            onClick={onFinish}
            className="flex items-start gap-3 p-4 bg-gray-50 rounded-xl border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors group"
          >
            <div className="w-9 h-9 bg-white rounded-lg border border-gray-200 flex items-center justify-center shrink-0 group-hover:border-blue-300">
              <Icon size={16} className="text-gray-500 group-hover:text-blue-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">{label}</p>
              <p className="text-xs text-gray-400 mt-0.5">{desc}</p>
            </div>
            <ChevronRight size={14} className="text-gray-300 group-hover:text-blue-400 ml-auto shrink-0 mt-1" />
          </Link>
        ))}
      </div>

      <button
        onClick={onFinish}
        className="w-full bg-blue-600 text-white py-3 rounded-xl font-semibold hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
      >
        Go to Dashboard <ArrowRight size={16} />
      </button>
    </div>
  )
}

// ── Shared nav buttons ─────────────────────────────────────────────────────

function StepNav({ onNext, onBack, onSkip, nextLabel = 'Next', disableNext = false }) {
  return (
    <div className="flex items-center justify-between mt-8 pt-6 border-t border-gray-100">
      <div className="flex gap-3">
        {onBack && (
          <button
            onClick={onBack}
            className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <ArrowLeft size={14} /> Back
          </button>
        )}
        <button
          onClick={onSkip}
          className="text-sm text-gray-400 hover:text-gray-600 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
        >
          Skip for now
        </button>
      </div>
      <button
        onClick={onNext}
        disabled={disableNext}
        className="flex items-center gap-2 bg-blue-600 text-white px-5 py-2.5 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors text-sm"
      >
        {nextLabel} <ArrowRight size={14} />
      </button>
    </div>
  )
}

// ── Main page ──────────────────────────────────────────────────────────────

export default function SetupPage() {
  const { user } = useAuth()
  const navigate = useNavigate()

  const [step, setStep]       = useState(1)
  const [done, setDone]       = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving]   = useState(false)
  const [bizId, setBizId]     = useState(null)

  const [form, setForm] = useState({
    name: '', phone: '', address: '', website: '',
    brand_color: '#2563eb', logo_url: '',
    ai_agent_name: '', google_review_url: '',
  })

  // Platform admins don't need the setup wizard
  useEffect(() => {
    if (user && user.isPlatformAdmin) {
      navigate('/', { replace: true })
      return
    }
  }, [user])

  // Load existing business data to pre-fill the form
  useEffect(() => {
    if (!user || user.isPlatformAdmin) return
    getMyBusiness()
      .then(biz => {
        setBizId(biz.id)
        // If setup already completed, skip straight to dashboard
        if (biz.has_completed_setup) {
          navigate('/', { replace: true })
          return
        }
        setForm({
          name:             biz.name || '',
          phone:            biz.phone || '',
          address:          biz.address || '',
          website:          biz.website || '',
          brand_color:      biz.brand_color || '#2563eb',
          logo_url:         biz.logo_url || '',
          ai_agent_name:    biz.ai_agent_name || '',
          google_review_url: biz.google_review_url || '',
        })
      })
      .catch(err => {
        console.error('Setup page: failed to load business', err)
      })
      .finally(() => setLoading(false))
  }, [user])

  const onChange = (field, value) => setForm(f => ({ ...f, [field]: value }))

  // Save current form data and advance
  const saveAndAdvance = async (nextStep) => {
    if (!bizId) { setStep(nextStep); return }
    setSaving(true)
    try {
      await updateBusiness(bizId, form)
    } catch (err) {
      console.error('Setup save error:', err)
    } finally {
      setSaving(false)
    }
    setStep(nextStep)
  }

  // Mark setup complete and go to dashboard
  const finish = async (to = '/') => {
    if (bizId) {
      try {
        await updateBusiness(bizId, { ...form, has_completed_setup: true })
      } catch (err) {
        console.error('Setup complete error:', err)
      }
    }
    navigate(to, { replace: true })
  }

  const skip = () => finish('/')

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-400 text-sm">Loading…</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 w-full max-w-xl p-8">

        {/* Header */}
        {!done && (
          <div className="mb-6">
            <div className="flex items-center justify-between mb-1">
              <h1 className="text-lg font-bold text-gray-900">Space Coast Studios</h1>
              <button
                onClick={skip}
                className="text-xs text-gray-400 hover:text-gray-600 underline underline-offset-2"
              >
                Skip setup
              </button>
            </div>
            <p className="text-sm text-gray-500">Let's get your account configured in just a few steps.</p>
          </div>
        )}

        {!done && <ProgressBar step={step} />}

        {saving && (
          <div className="text-xs text-blue-500 text-right mb-2 -mt-6">Saving…</div>
        )}

        {/* Step content */}
        {step === 1 && (
          <StepBusinessInfo
            form={form}
            onChange={onChange}
            onNext={() => saveAndAdvance(2)}
            onSkip={skip}
          />
        )}
        {step === 2 && (
          <StepBranding
            form={form}
            onChange={onChange}
            onNext={() => saveAndAdvance(3)}
            onBack={() => setStep(1)}
            onSkip={skip}
          />
        )}
        {step === 3 && (
          <StepNotifications
            form={form}
            onChange={onChange}
            onNext={async () => {
              await saveAndAdvance(4)
              setDone(true)
            }}
            onBack={() => setStep(2)}
            onSkip={skip}
          />
        )}
        {done && (
          <StepDone
            businessName={form.name}
            onFinish={() => finish('/')}
          />
        )}
      </div>
    </div>
  )
}
