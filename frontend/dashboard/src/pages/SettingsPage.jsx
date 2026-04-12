import { useState, useEffect } from 'react'
import { Save, Plus, Trash2, Copy, Check } from 'lucide-react'
import {
  getBusinessHours, updateBusinessHours,
  getBlockedTimes, createBlockedTime, deleteBlockedTime,
  getSettings, updateSetting,
} from '../services/api'
import { useBusinessContext } from '../hooks/useBusinessContext'

const API_BASE = 'https://api.spacecoaststudios.com'

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

export default function SettingsPage() {
  const { activeBusinessId, activeBusiness } = useBusinessContext()
  const [copied, setCopied] = useState(false)
  const [hours, setHours] = useState([])
  const [blocked, setBlocked] = useState([])
  const [settings, setSettings] = useState([])
  const [blockForm, setBlockForm] = useState({ start_datetime: '', end_datetime: '', reason: '' })
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  const load = async () => {
    if (activeBusinessId == null) return
    try {
      const [h, b, s] = await Promise.all([
        getBusinessHours(activeBusinessId),
        getBlockedTimes(activeBusinessId),
        getSettings(activeBusinessId),
      ])
      const full = DAYS.map((_, i) => {
        const existing = h.find(x => x.day_of_week === i)
        return existing || { day_of_week: i, open_time: '08:00', close_time: '17:00', is_active: false }
      })
      setHours(full)
      setBlocked(b)
      setSettings(s)
    } catch (err) { console.error(err) }
  }
  useEffect(() => { load() }, [activeBusinessId])

  const updateHour = (idx, field, value) => {
    setHours(h => h.map((item, i) => i === idx ? { ...item, [field]: value } : item))
  }

  const saveHours = async () => {
    setSaving(true)
    setMessage('')
    try {
      await updateBusinessHours(hours.map(h => ({
        day_of_week: h.day_of_week,
        open_time: h.open_time,
        close_time: h.close_time,
        is_active: h.is_active,
      })), activeBusinessId)
      setMessage('Business hours saved')
    } catch (err) { setMessage('Error: ' + err.message) }
    setSaving(false)
  }

  const addBlock = async (e) => {
    e.preventDefault()
    try {
      await createBlockedTime({
        start_datetime: new Date(blockForm.start_datetime).toISOString(),
        end_datetime: new Date(blockForm.end_datetime).toISOString(),
        reason: blockForm.reason || null,
      }, activeBusinessId)
      setBlockForm({ start_datetime: '', end_datetime: '', reason: '' })
      load()
    } catch (err) { console.error(err) }
  }

  const removeBlock = async (id) => {
    await deleteBlockedTime(id, activeBusinessId)
    load()
  }

  const saveSetting = async (key, value) => {
    try {
      await updateSetting(key, value, activeBusinessId)
      setMessage(`Setting "${key}" updated`)
    } catch (err) { console.error(err) }
  }

  if (activeBusinessId == null) {
    return <div className="flex items-center justify-center h-64 text-gray-400">Select a business to manage settings.</div>
  }

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-gray-900">Settings</h1>

      {message && <div className="bg-green-50 text-green-700 px-4 py-2 rounded-lg text-sm">{message}</div>}

      {/* Business Hours */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Business Hours</h2>
        <div className="space-y-3">
          {hours.map((h, i) => (
            <div key={i} className="flex items-center gap-4">
              <label className="flex items-center gap-2 w-32">
                <input type="checkbox" checked={h.is_active} onChange={(e) => updateHour(i, 'is_active', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
                <span className="text-sm font-medium text-gray-700">{DAYS[i]}</span>
              </label>
              <input type="time" value={h.open_time} onChange={(e) => updateHour(i, 'open_time', e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm" disabled={!h.is_active} />
              <span className="text-gray-400">to</span>
              <input type="time" value={h.close_time} onChange={(e) => updateHour(i, 'close_time', e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm" disabled={!h.is_active} />
            </div>
          ))}
        </div>
        <button onClick={saveHours} disabled={saving}
          className="mt-4 flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
          <Save size={16} /> {saving ? 'Saving...' : 'Save Hours'}
        </button>
      </section>

      {/* Blocked Times */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Blocked Times</h2>
        {blocked.length > 0 && (
          <div className="space-y-2 mb-4">
            {blocked.map((b) => (
              <div key={b.id} className="flex items-center justify-between bg-red-50 px-4 py-2.5 rounded-lg">
                <div className="text-sm">
                  <span className="font-medium">{new Date(b.start_datetime).toLocaleString()}</span>
                  <span className="text-gray-400 mx-2">to</span>
                  <span className="font-medium">{new Date(b.end_datetime).toLocaleString()}</span>
                  {b.reason && <span className="text-gray-500 ml-2">({b.reason})</span>}
                </div>
                <button onClick={() => removeBlock(b.id)} className="text-red-500 hover:text-red-700"><Trash2 size={16} /></button>
              </div>
            ))}
          </div>
        )}
        <form onSubmit={addBlock} className="flex items-end gap-3 flex-wrap">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Start</label>
            <input type="datetime-local" value={blockForm.start_datetime} onChange={(e) => setBlockForm({ ...blockForm, start_datetime: e.target.value })}
              className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm" required />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">End</label>
            <input type="datetime-local" value={blockForm.end_datetime} onChange={(e) => setBlockForm({ ...blockForm, end_datetime: e.target.value })}
              className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm" required />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Reason</label>
            <input type="text" value={blockForm.reason} onChange={(e) => setBlockForm({ ...blockForm, reason: e.target.value })} placeholder="e.g., Holiday"
              className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm" />
          </div>
          <button type="submit" className="flex items-center gap-1 bg-red-600 text-white px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-red-700">
            <Plus size={16} /> Block Time
          </button>
        </form>
      </section>

      {/* Embed Code */}
      {activeBusiness?.slug && (
        <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-1">Contact Form Embed</h2>
          <p className="text-sm text-gray-500 mb-4">
            Paste this snippet into any page on the client's website to embed the contact form.
          </p>
          <div className="relative">
            <pre className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-xs text-gray-700 overflow-x-auto whitespace-pre-wrap break-all">
{`<iframe
  src="${API_BASE}/embed/${activeBusiness.slug}/contact"
  width="100%"
  height="620"
  frameborder="0"
  style="border:none; border-radius:8px;"
></iframe>`}
            </pre>
            <button
              onClick={() => {
                navigator.clipboard.writeText(
                  `<iframe\n  src="${API_BASE}/embed/${activeBusiness.slug}/contact"\n  width="100%"\n  height="620"\n  frameborder="0"\n  style="border:none; border-radius:8px;"\n></iframe>`
                )
                setCopied(true)
                setTimeout(() => setCopied(false), 2000)
              }}
              className="absolute top-3 right-3 flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium
                         bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              {copied ? <><Check size={12} className="text-green-600" /> Copied</> : <><Copy size={12} /> Copy</>}
            </button>
          </div>
          <p className="text-xs text-gray-400 mt-2">
            Preview: <a href={`${API_BASE}/embed/${activeBusiness.slug}/contact`} target="_blank" rel="noreferrer"
              className="text-blue-500 hover:underline">
              {API_BASE}/embed/{activeBusiness.slug}/contact
            </a>
          </p>
        </section>
      )}

      {/* Scheduling Settings */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Scheduling Settings</h2>
        <div className="space-y-4">
          {settings.map((s) => (
            <div key={s.key} className="flex items-center gap-4">
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700">{s.key.replace(/_/g, ' ')}</label>
                {s.description && <p className="text-xs text-gray-400">{s.description}</p>}
              </div>
              <input type="text" defaultValue={s.value}
                onBlur={(e) => { if (e.target.value !== s.value) saveSetting(s.key, e.target.value) }}
                className="w-32 border border-gray-300 rounded-lg px-3 py-1.5 text-sm text-right" />
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
