/**
 * NotificationTemplatesPage — edit per-business SMS and email notification templates.
 *
 * Displays all 4 templates (confirmation SMS/email, reminder SMS/email) as editable
 * cards with token reference chips and a live character count for SMS.
 */

import { useState, useEffect, useCallback } from 'react'
import {
  getNotificationTemplates,
  saveNotificationTemplates,
  resetNotificationTemplates,
} from '../services/api'
import { useBusinessContext } from '../hooks/useBusinessContext'
import { CheckCircle, AlertCircle, RotateCcw, Save, MessageSquare, Mail } from 'lucide-react'

// ── Constants ──────────────────────────────────────────────────────────────────

const EVENT_LABELS = {
  confirmation: 'Booking Confirmation',
  reminder_24h: '24-Hour Reminder',
  review_request: 'Review Request',
  otw_tech_prompt: 'OTW — Tech Prompt (1 hr before)',
  otw_customer: 'OTW — Customer Notification',
  otw_tech_complete_prompt: 'OTW — Job Complete Prompt',
  otw_morning_kickoff: 'OTW — Morning Kickoff',
  otw_next_stop: 'OTW — Next Stop',
  otw_day_complete: 'OTW — Day Complete',
}

const CHANNEL_LABELS = {
  sms: 'SMS',
  email: 'Email',
}

const SMS_LIMIT = 320  // approx 2 segments; warn above this

// ── Helpers ────────────────────────────────────────────────────────────────────

function TokenChip({ token, label, onClick }) {
  return (
    <button
      type="button"
      title={label}
      onClick={() => onClick(token)}
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-mono
                 bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100
                 transition-colors cursor-pointer select-none"
    >
      {token}
    </button>
  )
}

function TemplateCard({ template, tokens, onChange, isSaving }) {
  const isEmail = template.channel === 'email'
  const isSms = template.channel === 'sms'
  const isDirty = template._dirty
  const smsLen = isSms ? (template.body || '').length : 0

  // Flatten tokens: "all" tokens + event-specific tokens
  const availableTokens = [
    ...(tokens.all || []),
    ...(tokens[template.event_type] || []),
  ]

  // Insert token at cursor position in the focused field
  function insertToken(token, field) {
    const el = document.getElementById(`field-${template.event_type}-${template.channel}-${field}`)
    if (!el) return
    const start = el.selectionStart ?? el.value.length
    const end = el.selectionEnd ?? el.value.length
    const val = el.value
    const newVal = val.slice(0, start) + token + val.slice(end)
    onChange(template.event_type, template.channel, field, newVal)
    // Restore cursor after React re-render
    setTimeout(() => {
      el.focus()
      el.setSelectionRange(start + token.length, start + token.length)
    }, 0)
  }

  return (
    <div className={`bg-white rounded-lg border ${isDirty ? 'border-amber-400 shadow-sm' : 'border-gray-200'} overflow-hidden`}>
      {/* Card header */}
      <div className="flex items-center justify-between px-4 py-3 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center gap-2">
          {isEmail
            ? <Mail size={16} className="text-blue-600" />
            : <MessageSquare size={16} className="text-green-600" />}
          <span className="font-semibold text-gray-800 text-sm">
            {EVENT_LABELS[template.event_type]} — {CHANNEL_LABELS[template.channel]}
          </span>
          {template.is_default && (
            <span className="text-xs text-gray-400 italic ml-1">(default)</span>
          )}
          {isDirty && (
            <span className="text-xs text-amber-600 font-medium ml-1">● unsaved</span>
          )}
        </div>
        <div className="flex items-center gap-1">
          <label className="flex items-center gap-1.5 text-xs text-gray-600 cursor-pointer">
            <input
              type="checkbox"
              checked={template.is_active}
              disabled={isSaving}
              onChange={e => onChange(template.event_type, template.channel, 'is_active', e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            Active
          </label>
        </div>
      </div>

      <div className="p-4 space-y-3">
        {/* Token chips */}
        <div>
          <p className="text-xs text-gray-500 mb-1.5 font-medium">Insert token:</p>
          <div className="flex flex-wrap gap-1.5">
            {availableTokens.map(([tok, lbl]) => (
              <TokenChip
                key={tok}
                token={tok}
                label={lbl}
                onClick={tok => insertToken(tok, isDirty || !isEmail ? 'body' : 'body')}
              />
            ))}
          </div>
        </div>

        {/* Subject line (email only) */}
        {isEmail && (
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Subject line
            </label>
            <div className="flex flex-wrap gap-1.5 mb-1.5">
              {availableTokens.map(([tok, lbl]) => (
                <TokenChip
                  key={tok}
                  token={tok}
                  label={lbl}
                  onClick={tok => insertToken(tok, 'subject')}
                />
              ))}
            </div>
            <input
              id={`field-${template.event_type}-${template.channel}-subject`}
              type="text"
              value={template.subject || ''}
              disabled={isSaving}
              onChange={e => onChange(template.event_type, template.channel, 'subject', e.target.value)}
              placeholder="Email subject…"
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm
                         focus:ring-2 focus:ring-blue-500 focus:border-transparent
                         disabled:bg-gray-50 disabled:text-gray-500"
            />
          </div>
        )}

        {/* Body */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="block text-xs font-medium text-gray-700">
              {isEmail ? 'Body (plain text)' : 'Message body'}
            </label>
            {isSms && (
              <span className={`text-xs font-mono ${smsLen > SMS_LIMIT ? 'text-red-600 font-semibold' : 'text-gray-400'}`}>
                {smsLen} chars{smsLen > SMS_LIMIT ? ` — over ${SMS_LIMIT} limit` : ''}
              </span>
            )}
          </div>
          <textarea
            id={`field-${template.event_type}-${template.channel}-body`}
            value={template.body || ''}
            disabled={isSaving}
            rows={isEmail ? 7 : 4}
            onChange={e => onChange(template.event_type, template.channel, 'body', e.target.value)}
            placeholder={isEmail ? 'Email body text…' : 'SMS message text…'}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm font-mono
                       focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-y
                       disabled:bg-gray-50 disabled:text-gray-500"
          />
          {isEmail && (
            <p className="text-xs text-gray-400 mt-1">
              Plain text is auto-wrapped in a branded HTML envelope using your brand color.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Main page ──────────────────────────────────────────────────────────────────

export default function NotificationTemplatesPage() {
  const { activeBusiness } = useBusinessContext()
  const businessId = activeBusiness?.id ?? null

  const [templates, setTemplates] = useState([])
  const [tokens, setTokens] = useState({ all: [], confirmation: [] })
  const [loading, setLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [toast, setToast] = useState(null)   // { type: 'success'|'error', msg: string }

  const showToast = useCallback((type, msg) => {
    setToast({ type, msg })
    setTimeout(() => setToast(null), 4000)
  }, [])

  const load = useCallback(async () => {
    if (!businessId) return
    setLoading(true)
    try {
      const data = await getNotificationTemplates(businessId)
      setTemplates(data.templates.map(t => ({ ...t, _dirty: false })))
      setTokens(data.tokens || { all: [], confirmation: [] })
    } catch (e) {
      showToast('error', `Failed to load templates: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }, [businessId, showToast])

  useEffect(() => { load() }, [load])

  function handleChange(event_type, channel, field, value) {
    setTemplates(prev =>
      prev.map(t =>
        t.event_type === event_type && t.channel === channel
          ? { ...t, [field]: value, _dirty: true }
          : t
      )
    )
  }

  const dirtyTemplates = templates.filter(t => t._dirty)
  const hasDirty = dirtyTemplates.length > 0

  async function handleSave() {
    if (!hasDirty) return
    setIsSaving(true)
    try {
      const payload = dirtyTemplates.map(({ _dirty, is_default, ...t }) => t)
      const data = await saveNotificationTemplates(payload, businessId)
      setTemplates(data.templates.map(t => ({ ...t, _dirty: false })))
      setTokens(data.tokens || tokens)
      showToast('success', `${dirtyTemplates.length} template${dirtyTemplates.length > 1 ? 's' : ''} saved.`)
    } catch (e) {
      showToast('error', `Save failed: ${e.message}`)
    } finally {
      setIsSaving(false)
    }
  }

  async function handleReset() {
    if (!window.confirm('Reset all templates to platform defaults? Any customizations will be deleted.')) return
    setIsSaving(true)
    try {
      const data = await resetNotificationTemplates(businessId)
      setTemplates(data.templates.map(t => ({ ...t, _dirty: false })))
      setTokens(data.tokens || tokens)
      showToast('success', 'Templates reset to defaults.')
    } catch (e) {
      showToast('error', `Reset failed: ${e.message}`)
    } finally {
      setIsSaving(false)
    }
  }

  // Group by event type for display
  const grouped = [
    { key: 'confirmation', label: 'Booking Confirmation', icon: '✅' },
    { key: 'reminder_24h', label: '24-Hour Reminder', icon: '⏰' },
    { key: 'review_request', label: 'Review Request', icon: '⭐' },
    { key: 'otw_morning_kickoff', label: 'OTW — Morning Kickoff', icon: '🌅' },
    { key: 'otw_tech_prompt', label: 'OTW — Tech Prompt (1 hr before)', icon: '🚗' },
    { key: 'otw_customer', label: 'OTW — Customer Notification', icon: '📲' },
    { key: 'otw_tech_complete_prompt', label: 'OTW — Job Complete Prompt', icon: '🔧' },
    { key: 'otw_next_stop', label: 'OTW — Next Stop', icon: '➡️' },
    { key: 'otw_day_complete', label: 'OTW — Day Complete', icon: '🌟' },
  ]

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Notification Templates</h1>
          <p className="text-gray-500 text-sm mt-1">
            Customize the SMS and email messages your customers receive when they book or are reminded of an appointment.
          </p>
        </div>
        <div className="flex gap-2 ml-4 shrink-0">
          <button
            onClick={handleReset}
            disabled={isSaving}
            className="flex items-center gap-1.5 px-3 py-2 text-sm text-gray-600 border border-gray-300
                       rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors"
          >
            <RotateCcw size={14} />
            Reset defaults
          </button>
          <button
            onClick={handleSave}
            disabled={!hasDirty || isSaving}
            className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white
                       bg-blue-600 rounded-lg hover:bg-blue-700
                       disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Save size={14} />
            {isSaving ? 'Saving…' : `Save${hasDirty ? ` (${dirtyTemplates.length})` : ''}`}
          </button>
        </div>
      </div>

      {/* Toast */}
      {toast && (
        <div className={`flex items-center gap-2 px-4 py-3 rounded-lg mb-5 text-sm font-medium
          ${toast.type === 'success'
            ? 'bg-green-50 text-green-800 border border-green-200'
            : 'bg-red-50 text-red-800 border border-red-200'}`}>
          {toast.type === 'success'
            ? <CheckCircle size={16} className="text-green-600 shrink-0" />
            : <AlertCircle size={16} className="text-red-600 shrink-0" />}
          {toast.msg}
        </div>
      )}

      {!businessId ? (
        <div className="text-center py-16 text-gray-400">Select a business to view its templates.</div>
      ) : loading ? (
        <div className="text-center py-16 text-gray-400">Loading templates…</div>
      ) : (
        <div className="space-y-8">
          {grouped.map(group => {
            const groupTemplates = templates.filter(t => t.event_type === group.key)
            return (
              <section key={group.key}>
                <h2 className="flex items-center gap-2 text-base font-semibold text-gray-700 mb-3">
                  <span>{group.icon}</span>
                  {group.label}
                </h2>
                <div className="grid gap-4 md:grid-cols-2">
                  {groupTemplates.map(t => (
                    <TemplateCard
                      key={`${t.event_type}-${t.channel}`}
                      template={t}
                      tokens={tokens}
                      onChange={handleChange}
                      isSaving={isSaving}
                    />
                  ))}
                </div>
              </section>
            )
          })}
        </div>
      )}

      {/* Token reference legend */}
      {businessId && !loading && (
        <div className="mt-8 bg-gray-50 rounded-lg border border-gray-200 p-4">
          <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-3">
            Available Tokens
          </h3>
          <div className="grid gap-1.5 sm:grid-cols-2">
            {[
              ...(tokens.all || []),
              ...(tokens.confirmation || []),
              ...(tokens.review_request || []),
              ...(tokens.otw_morning_kickoff || []),
              ...(tokens.otw_day_complete || []),
            ].map(([tok, lbl]) => (
              <div key={tok} className="flex items-center gap-2 text-xs text-gray-600">
                <span className="font-mono bg-white border border-gray-200 rounded px-1.5 py-0.5 text-blue-700 shrink-0">
                  {tok}
                </span>
                <span className="text-gray-500">{lbl}</span>
              </div>
            ))}
          </div>
          <p className="text-xs text-gray-400 mt-3">
            Click a token chip above any field to insert it at the cursor position.
          </p>
        </div>
      )}
    </div>
  )
}
