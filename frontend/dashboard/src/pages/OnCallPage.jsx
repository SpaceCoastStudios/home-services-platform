import { useState, useEffect, useCallback } from 'react'
import { useBusinessContext } from '../hooks/useBusinessContext'
import {
  Phone, PhoneCall, PhoneOff, RotateCcw, UserCheck,
  AlertCircle, CheckCircle, Clock, ChevronDown, Trash2, Plus, Save
} from 'lucide-react'
import {
  getOnCallConfig, updateOnCallConfig,
  addRotationEntry, deleteRotationEntry,
  setOnCallOverride, clearOnCallOverride,
  getTechnicians, getCurrentOnCall,
} from '../services/api'

const DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

export default function OnCallPage() {
  const { activeBusiness } = useBusinessContext()
  const businessId = activeBusiness?.id

  const [config, setConfig]           = useState(null)
  const [currentOnCallData, setCurrentOnCallData] = useState(null)
  const [techs, setTechs]             = useState([])
  const [loading, setLoading]         = useState(true)
  const [saving, setSaving]           = useState(false)
  const [toast, setToast]             = useState(null)
  const [activeTab, setActiveTab]     = useState('config') // 'config' | 'rotation' | 'override'

  // Config form state
  const [form, setForm] = useState({
    is_enabled: false,
    after_hours_start: '18:00',
    after_hours_end: '08:00',
    emergency_window_enabled: false,
    emergency_window_start: '21:00',
    emergency_window_end: '07:00',
    rotation_type: 'day_of_week',
    rolling_start_date: '',
    fallback_phone: '',
    fallback_name: '',
    emergency_fee_enabled: false,
    emergency_fee: '',
    escalation_sms_phone: '',
    escalation_email: '',
    escalation_notify_oncall: false,
  })

  // Rotation form state
  const [rotForm, setRotForm] = useState({ technician_id: '', day_of_week: '0', position: '0' })

  // Override form state
  const [ovForm, setOvForm] = useState({ technician_id: '', note: '', hours: '24' })

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3500)
  }

  const load = useCallback(async () => {
    if (!businessId) return
    setLoading(true)
    try {
      const [cfg, techList, oncallNow] = await Promise.all([
        getOnCallConfig(businessId),
        getTechnicians(businessId, true),
        getCurrentOnCall(businessId).catch(() => null),
      ])
      setConfig(cfg)
      setTechs(techList)
      setCurrentOnCallData(oncallNow)
      setForm({
        is_enabled: cfg.is_enabled,
        after_hours_start: cfg.after_hours_start,
        after_hours_end: cfg.after_hours_end,
        emergency_window_enabled: cfg.emergency_window_enabled,
        emergency_window_start: cfg.emergency_window_start || '21:00',
        emergency_window_end: cfg.emergency_window_end || '07:00',
        rotation_type: cfg.rotation_type,
        rolling_start_date: cfg.rolling_start_date || '',
        fallback_phone: cfg.fallback_phone || '',
        fallback_name: cfg.fallback_name || '',
        emergency_fee_enabled: cfg.emergency_fee_enabled || false,
        emergency_fee: cfg.emergency_fee != null ? String(cfg.emergency_fee) : '',
        escalation_sms_phone: cfg.escalation_sms_phone || '',
        escalation_email: cfg.escalation_email || '',
        escalation_notify_oncall: cfg.escalation_notify_oncall || false,
      })
    } catch (e) {
      showToast('Failed to load on-call settings', 'error')
    } finally {
      setLoading(false)
    }
  }, [businessId])

  useEffect(() => { load() }, [load])

  // ── Save config ────────────────────────────────────────────────────────────
  const handleSaveConfig = async () => {
    setSaving(true)
    try {
      const payload = {
        ...form,
        rolling_start_date: form.rolling_start_date || null,
        emergency_fee: form.emergency_fee !== '' ? parseFloat(form.emergency_fee) : null,
      }
      await updateOnCallConfig(payload, businessId)
      showToast('On-call settings saved')
      load()
    } catch {
      showToast('Failed to save settings', 'error')
    } finally {
      setSaving(false)
    }
  }

  // ── Add rotation entry ─────────────────────────────────────────────────────
  const handleAddRotation = async () => {
    if (!rotForm.technician_id) return showToast('Select a technician', 'error')
    try {
      const payload = { technician_id: parseInt(rotForm.technician_id) }
      if (form.rotation_type === 'day_of_week') {
        payload.day_of_week = parseInt(rotForm.day_of_week)
      } else {
        payload.position = parseInt(rotForm.position)
      }
      await addRotationEntry(payload, businessId)
      showToast('Rotation entry added')
      setRotForm({ technician_id: '', day_of_week: '0', position: '0' })
      load()
    } catch {
      showToast('Failed to add rotation entry', 'error')
    }
  }

  const handleDeleteRotation = async (id) => {
    try {
      await deleteRotationEntry(id, businessId)
      showToast('Rotation entry removed')
      load()
    } catch {
      showToast('Failed to remove entry', 'error')
    }
  }

  // ── Override ───────────────────────────────────────────────────────────────
  const handleSetOverride = async () => {
    if (!ovForm.technician_id) return showToast('Select a technician', 'error')
    try {
      const res = await setOnCallOverride({
        technician_id: parseInt(ovForm.technician_id),
        note: ovForm.note || null,
        hours: parseInt(ovForm.hours) || 24,
      }, businessId)
      showToast(res.message)
      setOvForm({ technician_id: '', note: '', hours: '24' })
      load()
    } catch {
      showToast('Failed to set override', 'error')
    }
  }

  const handleClearOverride = async () => {
    try {
      await clearOnCallOverride(businessId)
      showToast('Override cleared — rotation is active')
      load()
    } catch {
      showToast('Failed to clear override', 'error')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400">
        Loading on-call settings…
      </div>
    )
  }

  // Use the server-computed on-call result — handles both day_of_week and weekly_rolling correctly.
  const activeTech = currentOnCallData?.on_call ?? null
  const isOverride = currentOnCallData?.source === 'override'
  const isFallback = currentOnCallData?.source === 'fallback'

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 flex items-center gap-2 px-4 py-3 rounded-lg shadow-lg text-white text-sm
          ${toast.type === 'error' ? 'bg-red-500' : 'bg-green-600'}`}>
          {toast.type === 'error' ? <AlertCircle size={16} /> : <CheckCircle size={16} />}
          {toast.msg}
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">On-Call Routing</h1>
          <p className="text-sm text-gray-500 mt-1">
            Route after-hours calls to the right technician automatically
          </p>
        </div>
        {/* Status badge */}
        <span className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium
          ${config?.is_enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
          {config?.is_enabled ? <PhoneCall size={14} /> : <PhoneOff size={14} />}
          {config?.is_enabled ? 'Active' : 'Disabled'}
        </span>
      </div>

      {/* Current on-call card */}
      {config?.is_enabled && (
        <div className={`rounded-xl border p-4 mb-6 flex items-center gap-4
          ${isOverride ? 'bg-amber-50 border-amber-200' : 'bg-blue-50 border-blue-200'}`}>
          <div className={`p-2 rounded-full ${isOverride ? 'bg-amber-100' : 'bg-blue-100'}`}>
            <UserCheck size={20} className={isOverride ? 'text-amber-600' : 'text-blue-600'} />
          </div>
          <div className="flex-1">
            {activeTech ? (
              <>
                <p className="text-sm font-semibold text-gray-900">
                  {isFallback ? 'Fallback contact' : 'On-call now'}: {activeTech.name}
                  {isOverride && (
                    <span className="ml-2 text-xs font-normal text-amber-600 bg-amber-100 px-2 py-0.5 rounded-full">
                      Manual override
                    </span>
                  )}
                  {isFallback && (
                    <span className="ml-2 text-xs font-normal text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
                      No rotation match
                    </span>
                  )}
                </p>
                {isOverride && config.active_override && (
                  <p className="text-xs text-gray-500 mt-0.5">
                    Expires {new Date(config.active_override.expires_at).toLocaleString()}
                    {config.active_override.note && ` · ${config.active_override.note}`}
                  </p>
                )}
              </>
            ) : (
              <p className="text-sm text-gray-500">No on-call tech assigned for today</p>
            )}
          </div>
          {isOverride && (
            <button onClick={handleClearOverride}
              className="text-xs text-amber-700 hover:text-amber-900 underline">
              Clear override
            </button>
          )}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-gray-100 p-1 rounded-lg w-fit">
        {[
          { id: 'config', label: 'Settings', icon: Phone },
          { id: 'rotation', label: 'Rotation Schedule', icon: RotateCcw },
          { id: 'override', label: 'Manual Override', icon: UserCheck },
        ].map(({ id, label, icon: Icon }) => (
          <button key={id} onClick={() => setActiveTab(id)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-md text-sm font-medium transition-colors
              ${activeTab === id ? 'bg-surface text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}>
            <Icon size={14} /> {label}
          </button>
        ))}
      </div>

      {/* ── Settings Tab ─────────────────────────────────────────────────── */}
      {activeTab === 'config' && (
        <div className="bg-surface rounded-xl border border-gray-200 p-6 space-y-6">

          {/* Enable toggle */}
          <div className="flex items-center justify-between pb-4 border-b border-gray-100">
            <div>
              <p className="font-medium text-gray-900">Enable On-Call Routing</p>
              <p className="text-sm text-gray-500">After-hours calls will be routed to the on-call technician</p>
            </div>
            <button onClick={() => setForm(f => ({ ...f, is_enabled: !f.is_enabled }))}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                ${form.is_enabled ? 'bg-blue-600' : 'bg-gray-300'}`}>
              <span className={`inline-block h-4 w-4 transform rounded-full bg-surface shadow transition-transform
                ${form.is_enabled ? 'translate-x-6' : 'translate-x-1'}`} />
            </button>
          </div>

          {/* After-hours window */}
          <div>
            <p className="font-medium text-gray-900 mb-3">After-Hours Window</p>
            <p className="text-sm text-gray-500 mb-3">
              Calls received outside business hours during this window route to the on-call tech
            </p>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Start time</label>
                <input type="time" value={form.after_hours_start}
                  onChange={e => setForm(f => ({ ...f, after_hours_start: e.target.value }))}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">End time</label>
                <input type="time" value={form.after_hours_end}
                  onChange={e => setForm(f => ({ ...f, after_hours_end: e.target.value }))}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm" />
              </div>
            </div>
          </div>

          {/* Emergency window */}
          <div className="pt-4 border-t border-gray-100">
            <div className="flex items-center justify-between mb-3">
              <div>
                <p className="font-medium text-gray-900">Emergency Window</p>
                <p className="text-sm text-gray-500">Optional tighter window for urgent calls only</p>
              </div>
              <button onClick={() => setForm(f => ({ ...f, emergency_window_enabled: !f.emergency_window_enabled }))}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                  ${form.emergency_window_enabled ? 'bg-orange-500' : 'bg-gray-300'}`}>
                <span className={`inline-block h-4 w-4 transform rounded-full bg-surface shadow transition-transform
                  ${form.emergency_window_enabled ? 'translate-x-6' : 'translate-x-1'}`} />
              </button>
            </div>
            {form.emergency_window_enabled && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Start time</label>
                  <input type="time" value={form.emergency_window_start}
                    onChange={e => setForm(f => ({ ...f, emergency_window_start: e.target.value }))}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">End time</label>
                  <input type="time" value={form.emergency_window_end}
                    onChange={e => setForm(f => ({ ...f, emergency_window_end: e.target.value }))}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm" />
                </div>
              </div>
            )}
          </div>

          {/* Fallback contact */}
          <div className="pt-4 border-t border-gray-100">
            <p className="font-medium text-gray-900 mb-1">Fallback Contact</p>
            <p className="text-sm text-gray-500 mb-3">
              If no on-call tech is assigned, calls route here
            </p>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Name</label>
                <input type="text" value={form.fallback_name} placeholder="Owner / Office Manager"
                  onChange={e => setForm(f => ({ ...f, fallback_name: e.target.value }))}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Phone (E.164)</label>
                <input type="text" value={form.fallback_phone} placeholder="+13215550100"
                  onChange={e => setForm(f => ({ ...f, fallback_phone: e.target.value }))}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm" />
              </div>
            </div>
          </div>

          {/* Emergency Fee */}
          <div className="pt-4 border-t border-gray-100">
            <div className="flex items-center justify-between mb-3">
              <div>
                <p className="font-medium text-gray-900">Emergency Fee</p>
                <p className="text-sm text-gray-500">AI will disclose the fee and get customer confirmation before dispatching</p>
              </div>
              <button onClick={() => setForm(f => ({ ...f, emergency_fee_enabled: !f.emergency_fee_enabled }))}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                  ${form.emergency_fee_enabled ? 'bg-blue-600' : 'bg-gray-300'}`}>
                <span className={`inline-block h-4 w-4 transform rounded-full bg-surface shadow transition-transform
                  ${form.emergency_fee_enabled ? 'translate-x-6' : 'translate-x-1'}`} />
              </button>
            </div>
            {form.emergency_fee_enabled && (
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Fee amount ($)</label>
                <div className="flex items-center gap-2">
                  <span className="text-gray-500 text-sm">$</span>
                  <input
                    type="number"
                    min="0"
                    step="1"
                    value={form.emergency_fee}
                    onChange={e => setForm(f => ({ ...f, emergency_fee: e.target.value }))}
                    placeholder="150"
                    className="w-32 border border-gray-200 rounded-lg px-3 py-2 text-sm"
                  />
                </div>
                <p className="text-xs text-gray-400 mt-1.5">
                  The AI will say: "An emergency service fee of ${form.emergency_fee || '___'} applies. Reply YES to confirm."
                </p>
              </div>
            )}
          </div>

          {/* Escalation Alerts */}
          <div className="pt-4 border-t border-gray-100">
            <p className="font-medium text-gray-900 mb-1">Escalation Alerts</p>
            <p className="text-sm text-gray-500 mb-4">
              Who gets notified when Scout escalates a conversation — whether a customer
              needs urgent help or the AI flags something for human follow-up.
            </p>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Alert SMS number <span className="text-gray-400">(E.164, e.g. +13215550100)</span>
                </label>
                <input type="text" value={form.escalation_sms_phone}
                  placeholder="+13215550100"
                  onChange={e => setForm(f => ({ ...f, escalation_sms_phone: e.target.value }))}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm" />
                <p className="text-xs text-gray-400 mt-1">Office manager, owner, or any mobile number</p>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Alert email</label>
                <input type="email" value={form.escalation_email}
                  placeholder="manager@yourbusiness.com"
                  onChange={e => setForm(f => ({ ...f, escalation_email: e.target.value }))}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm" />
                <p className="text-xs text-gray-400 mt-1">Receives a full email with conversation details</p>
              </div>
            </div>

            <div className="flex items-center justify-between py-3 px-4 bg-gray-50 rounded-lg">
              <div>
                <p className="text-sm font-medium text-gray-900">Also notify the on-call tech</p>
                <p className="text-xs text-gray-500 mt-0.5">
                  Sends the alert to whoever is currently on-call in addition to the contacts above
                </p>
              </div>
              <button
                onClick={() => setForm(f => ({ ...f, escalation_notify_oncall: !f.escalation_notify_oncall }))}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors shrink-0
                  ${form.escalation_notify_oncall ? 'bg-blue-600' : 'bg-gray-300'}`}>
                <span className={`inline-block h-4 w-4 transform rounded-full bg-surface shadow transition-transform
                  ${form.escalation_notify_oncall ? 'translate-x-6' : 'translate-x-1'}`} />
              </button>
            </div>

            {!form.escalation_sms_phone && !form.escalation_email && !form.escalation_notify_oncall && (
              <p className="text-xs text-amber-600 mt-3 flex items-center gap-1.5">
                <AlertCircle size={12} />
                No escalation contacts set — alerts will fall back to the Fallback Contact phone above
              </p>
            )}
          </div>

          {/* Rotation type */}
          <div className="pt-4 border-t border-gray-100">
            <p className="font-medium text-gray-900 mb-3">Rotation Style</p>
            <div className="grid grid-cols-2 gap-3">
              {[
                { value: 'day_of_week', label: 'Day of Week', desc: 'Same tech every Monday, etc.' },
                { value: 'weekly_rolling', label: 'Weekly Rolling', desc: 'Rotates through techs each week' },
              ].map(opt => (
                <button key={opt.value} onClick={() => setForm(f => ({ ...f, rotation_type: opt.value }))}
                  className={`text-left p-3 rounded-lg border-2 transition-colors
                    ${form.rotation_type === opt.value
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'}`}>
                  <p className="font-medium text-sm text-gray-900">{opt.label}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{opt.desc}</p>
                </button>
              ))}
            </div>
            {form.rotation_type === 'weekly_rolling' && (
              <div className="mt-3">
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Rotation start date <span className="text-gray-400">(pick a Monday)</span>
                </label>
                <input type="date" value={form.rolling_start_date}
                  onChange={e => setForm(f => ({ ...f, rolling_start_date: e.target.value }))}
                  className="border border-gray-200 rounded-lg px-3 py-2 text-sm" />
              </div>
            )}
          </div>

          <div className="pt-2">
            <button onClick={handleSaveConfig} disabled={saving}
              className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
              <Save size={14} /> {saving ? 'Saving…' : 'Save Settings'}
            </button>
          </div>
        </div>
      )}

      {/* ── Rotation Tab ──────────────────────────────────────────────────── */}
      {activeTab === 'rotation' && (
        <div className="space-y-4">
          {/* Existing entries */}
          <div className="bg-surface rounded-xl border border-gray-200 divide-y divide-gray-100">
            {config?.rotations?.length === 0 && (
              <div className="px-6 py-10 text-center text-gray-400 text-sm">
                No rotation entries yet — add one below
              </div>
            )}
            {config?.rotations?.map(entry => (
              <div key={entry.id} className="flex items-center justify-between px-5 py-3">
                <div>
                  <span className="font-medium text-gray-900 text-sm">{entry.technician_name}</span>
                  <span className="ml-3 text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
                    {form.rotation_type === 'day_of_week'
                      ? DAY_NAMES[entry.day_of_week]
                      : `Week ${entry.position + 1}`}
                  </span>
                </div>
                <button onClick={() => handleDeleteRotation(entry.id)}
                  className="text-gray-400 hover:text-red-500 transition-colors p-1">
                  <Trash2 size={15} />
                </button>
              </div>
            ))}
          </div>

          {/* Add entry form */}
          <div className="bg-surface rounded-xl border border-gray-200 p-5">
            <p className="font-medium text-gray-900 mb-4 text-sm">Add Rotation Entry</p>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Technician</label>
                <select value={rotForm.technician_id}
                  onChange={e => setRotForm(f => ({ ...f, technician_id: e.target.value }))}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm">
                  <option value="">Select…</option>
                  {techs.map(t => (
                    <option key={t.id} value={t.id}>{t.name}</option>
                  ))}
                </select>
              </div>

              {form.rotation_type === 'day_of_week' ? (
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Day</label>
                  <select value={rotForm.day_of_week}
                    onChange={e => setRotForm(f => ({ ...f, day_of_week: e.target.value }))}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm">
                    {DAY_NAMES.map((d, i) => (
                      <option key={i} value={i}>{d}</option>
                    ))}
                  </select>
                </div>
              ) : (
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Week in Rotation</label>
                  <select value={rotForm.position}
                    onChange={e => setRotForm(f => ({ ...f, position: e.target.value }))}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm">
                    {[1,2,3,4,5,6,7,8].map(n => (
                      <option key={n} value={n - 1}>Week {n}</option>
                    ))}
                  </select>
                </div>
              )}

              <div className="flex items-end">
                <button onClick={handleAddRotation}
                  className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 w-full justify-center">
                  <Plus size={14} /> Add
                </button>
              </div>
            </div>
          </div>

          {/* Webhook instructions */}
          <div className="bg-gray-50 rounded-xl border border-gray-200 p-5">
            <p className="font-medium text-gray-900 text-sm mb-2 flex items-center gap-1.5">
              <Phone size={14} /> Twilio Webhook URL
            </p>
            <p className="text-xs text-gray-500 mb-2">
              Set this as the Voice webhook URL on your Twilio phone number:
            </p>
            <code className="block bg-surface border border-gray-200 rounded-lg px-3 py-2 text-xs text-blue-700 break-all">
              {`https://your-api-domain.com/api/oncall/webhook/voice?business_id=${businessId}`}
            </code>
            <p className="text-xs text-gray-400 mt-2">
              Replace <strong>your-api-domain.com</strong> with your DigitalOcean app URL.
              Set HTTP method to <strong>POST</strong>.
            </p>
          </div>
        </div>
      )}

      {/* ── Override Tab ──────────────────────────────────────────────────── */}
      {activeTab === 'override' && (
        <div className="space-y-4">
          {/* Active override */}
          {config?.active_override ? (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-medium text-amber-900 text-sm">Active Override</p>
                  <p className="text-lg font-bold text-gray-900 mt-1">
                    {config.active_override.technician_name}
                  </p>
                  <p className="text-sm text-gray-500 mt-0.5 flex items-center gap-1">
                    <Clock size={12} />
                    Expires {new Date(config.active_override.expires_at).toLocaleString()}
                  </p>
                  {config.active_override.note && (
                    <p className="text-sm text-gray-600 mt-1 italic">"{config.active_override.note}"</p>
                  )}
                </div>
                <button onClick={handleClearOverride}
                  className="px-3 py-1.5 text-sm text-amber-700 border border-amber-300 rounded-lg hover:bg-amber-100">
                  Clear Override
                </button>
              </div>
            </div>
          ) : (
            <div className="bg-gray-50 border border-gray-200 rounded-xl p-5 text-sm text-gray-500 text-center">
              No active override — rotation schedule is in effect
            </div>
          )}

          {/* Set new override */}
          <div className="bg-surface rounded-xl border border-gray-200 p-5">
            <p className="font-medium text-gray-900 mb-4 text-sm">Set Manual Override</p>
            <p className="text-xs text-gray-500 mb-4">
              Use this when a tech calls in sick or swaps shifts. The override
              expires automatically and rotation resumes.
            </p>
            <div className="grid grid-cols-2 gap-3 mb-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Technician</label>
                <select value={ovForm.technician_id}
                  onChange={e => setOvForm(f => ({ ...f, technician_id: e.target.value }))}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm">
                  <option value="">Select…</option>
                  {techs.map(t => (
                    <option key={t.id} value={t.id}>{t.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Duration (hours)</label>
                <input type="number" min="1" max="168" value={ovForm.hours}
                  onChange={e => setOvForm(f => ({ ...f, hours: e.target.value }))}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm" />
              </div>
            </div>
            <div className="mb-4">
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Reason <span className="text-gray-400">(optional)</span>
              </label>
              <input type="text" value={ovForm.note} placeholder="e.g. Tech A called in sick"
                onChange={e => setOvForm(f => ({ ...f, note: e.target.value }))}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm" />
            </div>
            <button onClick={handleSetOverride}
              className="flex items-center gap-2 px-5 py-2.5 bg-orange-500 text-white rounded-lg text-sm font-medium hover:bg-orange-600">
              <UserCheck size={14} /> Set Override
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
