import { useState, useEffect } from 'react'
import { MessageSquare, Clock, CheckCircle, AlertCircle, RefreshCw, Send, Bot, User, X } from 'lucide-react'
import {
  getContactSubmissions,
  updateContactSubmission,
  triggerAiResponse,
  approveAiResponse,
  sendManualResponse,
} from '../services/api'
import { useBusinessContext } from '../hooks/useBusinessContext'

const STATUS_CONFIG = {
  new:                 { label: 'New',              color: 'bg-blue-100 text-blue-700',    icon: MessageSquare },
  pending_approval:    { label: 'Needs Approval',   color: 'bg-amber-100 text-amber-700',  icon: AlertCircle },
  ai_responded:        { label: 'AI Responded',     color: 'bg-green-100 text-green-700',  icon: CheckCircle },
  ai_response_failed:  { label: 'AI Failed',        color: 'bg-red-100 text-red-700',      icon: AlertCircle },
  responded:           { label: 'Responded',        color: 'bg-teal-100 text-teal-700',    icon: CheckCircle },
  human_review:        { label: 'Needs Review',     color: 'bg-amber-100 text-amber-700',  icon: AlertCircle },
  appointment_booked:  { label: 'Booked',           color: 'bg-purple-100 text-purple-700', icon: CheckCircle },
  error:               { label: 'Error',            color: 'bg-red-100 text-red-700',      icon: AlertCircle },
  closed:              { label: 'Closed',           color: 'bg-gray-100 text-gray-600',    icon: CheckCircle },
}

export default function ContactsPage() {
  const { activeBusinessId } = useBusinessContext()
  const [submissions, setSubmissions] = useState([])
  const [filter, setFilter] = useState('')
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(false)
  const [triggering, setTriggering] = useState(false)
  const [manualMode, setManualMode] = useState(false)
  const [manualText, setManualText] = useState('')
  const [sendingSms, setSendingSms] = useState(false)
  const [actionMsg, setActionMsg] = useState('')

  const load = async () => {
    if (activeBusinessId == null) return
    setLoading(true)
    try {
      const data = await getContactSubmissions(filter || null, activeBusinessId)
      setSubmissions(data)
      // Refresh the selected item if it's still in the list
      if (selected) {
        const refreshed = data.find(s => s.id === selected.id)
        if (refreshed) setSelected(refreshed)
      }
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [filter, activeBusinessId])

  const handleStatusChange = async (id, status) => {
    await updateContactSubmission(id, { status }, activeBusinessId)
    load()
  }

  const handleTriggerAI = async () => {
    if (!selected) return
    setTriggering(true)
    setActionMsg('')
    try {
      await triggerAiResponse(selected.id, activeBusinessId)
      setActionMsg('AI response queued — refresh in a few seconds.')
      // Poll for completion
      setTimeout(() => load(), 3000)
      setTimeout(() => load(), 7000)
    } catch (err) {
      setActionMsg('Failed to trigger AI response.')
    } finally {
      setTriggering(false)
    }
  }

  const handleApprove = async () => {
    if (!selected) return
    setTriggering(true)
    setActionMsg('')
    try {
      const updated = await approveAiResponse(selected.id, activeBusinessId)
      setSelected(updated)
      setActionMsg('AI response approved and sent.')
      load()
    } catch (err) {
      setActionMsg('Failed to approve response.')
    } finally {
      setTriggering(false)
    }
  }

  const handleManualSend = async () => {
    if (!selected || !manualText.trim()) return
    setTriggering(true)
    setActionMsg('')
    try {
      const updated = await sendManualResponse(
        selected.id,
        { message: manualText.trim(), send_email: true, send_sms: sendingSms },
        activeBusinessId
      )
      setSelected(updated)
      setManualText('')
      setManualMode(false)
      setActionMsg('Response sent successfully.')
      load()
    } catch (err) {
      setActionMsg('Failed to send response.')
    } finally {
      setTriggering(false)
    }
  }

  if (activeBusinessId == null) {
    return <div className="p-8 text-gray-400">Select a business to view contact submissions.</div>
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Contact Submissions</h1>
        <button onClick={load} className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700">
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Status filters */}
      <div className="flex flex-wrap gap-2 mb-4">
        {['', 'new', 'pending_approval', 'ai_responded', 'human_review', 'appointment_booked', 'closed'].map((s) => (
          <button key={s} onClick={() => setFilter(s)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              filter === s ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 border border-gray-300 hover:bg-gray-50'
            }`}>
            {s ? STATUS_CONFIG[s]?.label || s : 'All'}
          </button>
        ))}
      </div>

      <div className="flex gap-6">
        {/* Submission list */}
        <div className="flex-1 min-w-0">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 divide-y divide-gray-100">
            {submissions.length === 0 ? (
              <div className="p-8 text-center text-gray-400">
                {loading ? 'Loading…' : 'No submissions found'}
              </div>
            ) : (
              submissions.map((sub) => {
                const cfg = STATUS_CONFIG[sub.status] || STATUS_CONFIG.new
                const Icon = cfg.icon
                return (
                  <div key={sub.id} onClick={() => { setSelected(sub); setManualMode(false); setActionMsg('') }}
                    className={`px-5 py-4 cursor-pointer hover:bg-gray-50 transition-colors ${selected?.id === sub.id ? 'bg-blue-50 border-l-2 border-blue-500' : ''}`}>
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="font-medium text-gray-900 truncate">{sub.name}</p>
                        <p className="text-sm text-gray-500 truncate">{sub.email}</p>
                      </div>
                      <span className={`shrink-0 flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-full ${cfg.color}`}>
                        <Icon size={10} />
                        {cfg.label}
                      </span>
                    </div>
                    {sub.service_requested && (
                      <p className="text-xs font-medium text-blue-600 mt-1.5">{sub.service_requested}</p>
                    )}
                    <p className="text-sm text-gray-600 mt-1 line-clamp-2">{sub.message}</p>
                    <div className="flex items-center gap-2 mt-2 text-xs text-gray-400">
                      <Clock size={11} />
                      {new Date(sub.created_at).toLocaleString()}
                      {sub.ai_response && (
                        <span className="flex items-center gap-0.5 text-green-600">
                          <Bot size={11} /> AI replied
                        </span>
                      )}
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>

        {/* Detail panel */}
        {selected && (
          <div className="w-[420px] shrink-0">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden sticky top-8">
              {/* Panel header */}
              <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-gray-900">{selected.name}</h3>
                  <p className="text-xs text-gray-500">{selected.email}{selected.phone ? ` · ${selected.phone}` : ''}</p>
                </div>
                <button onClick={() => setSelected(null)} className="text-gray-400 hover:text-gray-600">
                  <X size={16} />
                </button>
              </div>

              <div className="p-5 space-y-4 max-h-[80vh] overflow-y-auto">
                {/* Submission info */}
                <div className="space-y-2 text-sm">
                  {selected.service_requested && (
                    <div className="flex gap-2">
                      <span className="text-gray-400 w-24 shrink-0">Service</span>
                      <span className="text-gray-900 font-medium">{selected.service_requested}</span>
                    </div>
                  )}
                  {selected.preferred_date && (
                    <div className="flex gap-2">
                      <span className="text-gray-400 w-24 shrink-0">Preferred</span>
                      <span className="text-gray-900">{selected.preferred_date} {selected.preferred_time || ''}</span>
                    </div>
                  )}
                  <div className="flex gap-2">
                    <span className="text-gray-400 w-24 shrink-0">Submitted</span>
                    <span className="text-gray-900">{new Date(selected.created_at).toLocaleString()}</span>
                  </div>
                </div>

                {/* Customer message */}
                <div>
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1.5">Customer Message</p>
                  <div className="bg-gray-50 rounded-lg p-3 text-sm text-gray-700 whitespace-pre-wrap">
                    {selected.message}
                  </div>
                </div>

                {/* AI response */}
                {selected.status === 'pending_approval' && selected.ai_response ? (
                  <div>
                    <div className="flex items-center gap-1.5 mb-1.5">
                      <Bot size={13} className="text-amber-500" />
                      <p className="text-xs font-semibold text-amber-600 uppercase tracking-wide">AI Draft — Awaiting Approval</p>
                    </div>
                    <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-gray-700 whitespace-pre-wrap mb-3">
                      {selected.ai_response}
                    </div>
                    <button
                      onClick={handleApprove}
                      disabled={triggering}
                      className="w-full flex items-center justify-center gap-1.5 px-3 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 disabled:opacity-60 transition-colors">
                      {triggering ? <RefreshCw size={13} className="animate-spin" /> : <Send size={13} />}
                      {triggering ? 'Sending…' : 'Approve & Send'}
                    </button>
                  </div>
                ) : selected.ai_response ? (
                  <div>
                    <div className="flex items-center gap-1.5 mb-1.5">
                      <Bot size={13} className="text-blue-500" />
                      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide">AI Reply Sent</p>
                      {selected.responded_at && (
                        <span className="text-xs text-gray-400 ml-auto">
                          {new Date(selected.responded_at).toLocaleString()}
                        </span>
                      )}
                    </div>
                    <div className="bg-blue-50 border border-blue-100 rounded-lg p-3 text-sm text-gray-700 whitespace-pre-wrap">
                      {selected.ai_response}
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-between bg-amber-50 border border-amber-100 rounded-lg p-3">
                    <div className="flex items-center gap-2 text-sm text-amber-700">
                      <Bot size={14} />
                      No AI response yet
                    </div>
                    <button
                      onClick={handleTriggerAI}
                      disabled={triggering}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white text-xs font-medium rounded-lg hover:bg-blue-700 disabled:opacity-60 transition-colors">
                      {triggering ? <RefreshCw size={12} className="animate-spin" /> : <Bot size={12} />}
                      {triggering ? 'Sending…' : 'Send AI Reply'}
                    </button>
                  </div>
                )}

                {/* Re-trigger button (if already sent) */}
                {selected.ai_response && selected.status !== 'pending_approval' && (
                  <button
                    onClick={handleTriggerAI}
                    disabled={triggering}
                    className="w-full flex items-center justify-center gap-1.5 px-3 py-2 border border-gray-300 text-gray-600 text-sm rounded-lg hover:bg-gray-50 disabled:opacity-60 transition-colors">
                    {triggering ? <RefreshCw size={13} className="animate-spin" /> : <Bot size={13} />}
                    Re-send AI Reply
                  </button>
                )}

                {/* Action feedback */}
                {actionMsg && (
                  <p className="text-xs text-center text-green-600">{actionMsg}</p>
                )}

                {/* Manual reply toggle */}
                <div>
                  <button
                    onClick={() => setManualMode(!manualMode)}
                    className="w-full flex items-center justify-center gap-1.5 px-3 py-2 border border-gray-300 text-gray-600 text-sm rounded-lg hover:bg-gray-50 transition-colors">
                    <User size={13} />
                    {manualMode ? 'Cancel Manual Reply' : 'Write Manual Reply'}
                  </button>

                  {manualMode && (
                    <div className="mt-3 space-y-3">
                      <textarea
                        value={manualText}
                        onChange={(e) => setManualText(e.target.value)}
                        placeholder="Type your reply to the customer…"
                        rows={5}
                        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm resize-y focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <div className="flex items-center justify-between">
                        {selected.phone ? (
                          <label className="flex items-center gap-2 text-xs text-gray-500 cursor-pointer">
                            <input type="checkbox" checked={sendingSms} onChange={(e) => setSendingSms(e.target.checked)} className="rounded" />
                            Also send SMS
                          </label>
                        ) : <div />}
                        <button
                          onClick={handleManualSend}
                          disabled={triggering || !manualText.trim()}
                          className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-60 transition-colors">
                          <Send size={13} />
                          {triggering ? 'Sending…' : 'Send Reply'}
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {/* Status */}
                <div>
                  <label className="text-xs font-semibold text-gray-400 uppercase tracking-wide block mb-1.5">Status</label>
                  <select
                    value={selected.status}
                    onChange={(e) => handleStatusChange(selected.id, e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                    {Object.entries(STATUS_CONFIG).map(([k, v]) => (
                      <option key={k} value={k}>{v.label}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
