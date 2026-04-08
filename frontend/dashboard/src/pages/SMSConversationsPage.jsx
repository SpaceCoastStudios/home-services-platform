import { useState, useEffect, useRef } from 'react'
import { useBusinessContext } from '../hooks/useBusinessContext'
import {
  getSmsConversations,
  getSmsConversation,
  closeSmsConversation,
  sendManualSms,
} from '../services/api'
import {
  MessageSquare,
  CheckCircle,
  AlertCircle,
  Clock,
  X,
  Send,
  RefreshCw,
  ChevronRight,
  User,
  Bot,
} from 'lucide-react'

const STATUS_COLORS = {
  active:    'bg-blue-100 text-blue-700',
  booked:    'bg-green-100 text-green-700',
  escalated: 'bg-orange-100 text-orange-700',
  closed:    'bg-gray-100 text-gray-500',
}

const STATUS_ICONS = {
  active:    Clock,
  booked:    CheckCircle,
  escalated: AlertCircle,
  closed:    X,
}

function StatusBadge({ status }) {
  const Icon = STATUS_ICONS[status] || Clock
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[status] || 'bg-gray-100 text-gray-500'}`}>
      <Icon size={11} />
      {status}
    </span>
  )
}

function formatPhone(phone) {
  const digits = (phone || '').replace(/\D/g, '')
  if (digits.length === 11 && digits.startsWith('1')) {
    return `(${digits.slice(1,4)}) ${digits.slice(4,7)}-${digits.slice(7)}`
  }
  if (digits.length === 10) {
    return `(${digits.slice(0,3)}) ${digits.slice(3,6)}-${digits.slice(6)}`
  }
  return phone
}

function formatRelativeTime(isoStr) {
  if (!isoStr) return ''
  const diff = Date.now() - new Date(isoStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  return `${days}d ago`
}

function formatTime(isoStr) {
  if (!isoStr) return ''
  return new Date(isoStr).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
}

function formatDate(isoStr) {
  if (!isoStr) return ''
  return new Date(isoStr).toLocaleDateString([], { month: 'short', day: 'numeric' })
}

// ── Conversation Thread ──────────────────────────────────────────────────────

function ConversationThread({ convo, onClose, onSend, onMarkClosed, businessId }) {
  const [replyText, setReplyText] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [convo?.messages])

  if (!convo) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
        Select a conversation to view
      </div>
    )
  }

  const messages = convo.messages || []
  const isClosed = convo.status === 'closed'

  async function handleSend() {
    if (!replyText.trim() || sending) return
    setSending(true)
    setError('')
    try {
      await onSend(convo.id, replyText.trim())
      setReplyText('')
    } catch (e) {
      setError(e.message || 'Failed to send')
    } finally {
      setSending(false)
    }
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Thread header */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-gray-200 bg-white">
        <div>
          <p className="font-semibold text-gray-900 text-sm">
            {convo.customer_name || formatPhone(convo.customer_phone)}
          </p>
          {convo.customer_name && (
            <p className="text-xs text-gray-400">{formatPhone(convo.customer_phone)}</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={convo.status} />
          {!isClosed && (
            <button
              onClick={() => onMarkClosed(convo.id)}
              className="text-xs text-gray-400 hover:text-gray-700 border border-gray-200 rounded px-2 py-1 transition-colors"
            >
              Mark closed
            </button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3 bg-gray-50">
        {messages.length === 0 && (
          <p className="text-center text-sm text-gray-400 mt-8">No messages yet.</p>
        )}
        {messages.map((msg, i) => {
          const isUser = msg.role === 'user'
          const isManual = msg.manual
          return (
            <div key={i} className={`flex ${isUser ? 'justify-start' : 'justify-end'}`}>
              <div className={`max-w-[75%] ${isUser ? 'items-start' : 'items-end'} flex flex-col gap-1`}>
                {/* Role label */}
                <div className={`flex items-center gap-1 ${isUser ? '' : 'flex-row-reverse'}`}>
                  {isUser
                    ? <User size={11} className="text-gray-400" />
                    : isManual
                      ? <User size={11} className="text-orange-400" />
                      : <Bot size={11} className="text-blue-400" />
                  }
                  <span className="text-[10px] text-gray-400">
                    {isUser ? 'Customer' : isManual ? 'You (manual)' : 'AI Agent'}
                    {msg.ts && ` · ${formatTime(msg.ts)}`}
                  </span>
                </div>
                {/* Bubble */}
                <div
                  className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                    isUser
                      ? 'bg-white border border-gray-200 text-gray-800 rounded-tl-sm'
                      : isManual
                        ? 'bg-orange-500 text-white rounded-tr-sm'
                        : 'bg-blue-600 text-white rounded-tr-sm'
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            </div>
          )
        })}
        <div ref={bottomRef} />
      </div>

      {/* Reply box */}
      {!isClosed && (
        <div className="border-t border-gray-200 p-4 bg-white">
          {error && <p className="text-xs text-red-500 mb-2">{error}</p>}
          <div className="flex gap-2">
            <textarea
              value={replyText}
              onChange={(e) => setReplyText(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Type a manual reply... (Enter to send)"
              rows={2}
              className="flex-1 resize-none border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <button
              onClick={handleSend}
              disabled={!replyText.trim() || sending}
              className="self-end px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center gap-1.5 text-sm font-medium"
            >
              <Send size={14} />
              {sending ? 'Sending…' : 'Send'}
            </button>
          </div>
          <p className="text-xs text-gray-400 mt-1.5">
            Manual replies are sent directly from the business Twilio number.
          </p>
        </div>
      )}
      {isClosed && (
        <div className="border-t border-gray-200 p-4 bg-gray-50 text-center text-xs text-gray-400">
          This conversation is closed.
        </div>
      )}
    </div>
  )
}

// ── Main Page ────────────────────────────────────────────────────────────────

export default function SMSConversationsPage() {
  const { activeBusiness } = useBusinessContext()
  const businessId = activeBusiness?.id ?? null

  const [convos, setConvos] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [selectedConvo, setSelectedConvo] = useState(null)
  const [statusFilter, setStatusFilter] = useState('active')
  const [loading, setLoading] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)
  const [error, setError] = useState('')

  // Load conversation list
  useEffect(() => {
    if (!businessId) return
    loadConvos()
  }, [businessId, statusFilter])

  async function loadConvos() {
    setLoading(true)
    setError('')
    try {
      const data = await getSmsConversations(statusFilter || null, businessId)
      setConvos(data)
    } catch (e) {
      setError(e.message || 'Failed to load conversations')
    } finally {
      setLoading(false)
    }
  }

  // Load selected conversation detail (with messages)
  useEffect(() => {
    if (!selectedId || !businessId) {
      setSelectedConvo(null)
      return
    }
    loadDetail(selectedId)
  }, [selectedId, businessId])

  async function loadDetail(id) {
    setDetailLoading(true)
    try {
      const data = await getSmsConversation(id, businessId)
      setSelectedConvo(data)
    } catch (e) {
      setError(e.message || 'Failed to load conversation')
    } finally {
      setDetailLoading(false)
    }
  }

  async function handleSend(id, message) {
    const updated = await sendManualSms(id, message, businessId)
    setSelectedConvo(updated)
    // Refresh list to update last message time
    setConvos(prev => prev.map(c => c.id === id
      ? { ...c, last_message_at: updated.last_message_at, message_count: (updated.messages || []).length }
      : c
    ))
  }

  async function handleClose(id) {
    await closeSmsConversation(id, businessId)
    await loadConvos()
    if (selectedId === id) setSelectedId(null)
  }

  if (!businessId) {
    return (
      <div className="text-center py-20 text-gray-500 text-sm">
        Select a business to view SMS conversations.
      </div>
    )
  }

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] -m-8">
      {/* Page header */}
      <div className="flex items-center justify-between px-8 py-5 bg-white border-b border-gray-200 shrink-0">
        <div>
          <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <MessageSquare size={20} className="text-blue-600" />
            SMS Conversations
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Inbound texts handled by the AI booking agent
          </p>
        </div>
        <button
          onClick={loadConvos}
          className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-800 border border-gray-200 rounded-lg px-3 py-1.5 transition-colors"
        >
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>

      {/* Body */}
      <div className="flex flex-1 min-h-0">
        {/* Left: list */}
        <div className="w-80 border-r border-gray-200 flex flex-col bg-white shrink-0">
          {/* Filter tabs */}
          <div className="flex border-b border-gray-200 px-2 pt-2 gap-1">
            {['active', 'booked', 'escalated', 'closed', ''].map((s) => (
              <button
                key={s}
                onClick={() => { setStatusFilter(s); setSelectedId(null) }}
                className={`px-3 py-1.5 text-xs font-medium rounded-t transition-colors ${
                  statusFilter === s
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-500 hover:text-gray-800 hover:bg-gray-100'
                }`}
              >
                {s === '' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)}
              </button>
            ))}
          </div>

          {/* List */}
          <div className="flex-1 overflow-y-auto">
            {error && (
              <p className="text-xs text-red-500 text-center py-4 px-3">{error}</p>
            )}
            {loading && (
              <p className="text-xs text-gray-400 text-center py-6">Loading…</p>
            )}
            {!loading && convos.length === 0 && (
              <div className="text-center py-12 px-4">
                <MessageSquare size={32} className="text-gray-200 mx-auto mb-3" />
                <p className="text-sm text-gray-400">No conversations yet</p>
                <p className="text-xs text-gray-300 mt-1">
                  They'll appear here when customers text your Twilio number.
                </p>
              </div>
            )}
            {convos.map((c) => {
              const isSelected = c.id === selectedId
              return (
                <button
                  key={c.id}
                  onClick={() => setSelectedId(c.id)}
                  className={`w-full text-left px-4 py-3 border-b border-gray-100 transition-colors flex items-start gap-3 ${
                    isSelected ? 'bg-blue-50 border-l-2 border-l-blue-500' : 'hover:bg-gray-50'
                  }`}
                >
                  {/* Avatar */}
                  <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center shrink-0 mt-0.5">
                    <User size={14} className="text-gray-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-1">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {c.customer_name || formatPhone(c.customer_phone)}
                      </p>
                      <span className="text-[10px] text-gray-400 shrink-0">
                        {formatRelativeTime(c.last_message_at)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between mt-0.5">
                      <span className="text-xs text-gray-400">{c.message_count} messages</span>
                      <StatusBadge status={c.status} />
                    </div>
                  </div>
                  <ChevronRight size={14} className="text-gray-300 shrink-0 mt-1" />
                </button>
              )
            })}
          </div>
        </div>

        {/* Right: thread */}
        <div className="flex-1 flex flex-col min-w-0 bg-white">
          {detailLoading ? (
            <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
              Loading conversation…
            </div>
          ) : (
            <ConversationThread
              convo={selectedConvo}
              businessId={businessId}
              onClose={() => setSelectedId(null)}
              onSend={handleSend}
              onMarkClosed={handleClose}
            />
          )}
        </div>
      </div>

      {/* Info banner when no Twilio number configured */}
      {!activeBusiness?.twilio_phone_number && (
        <div className="shrink-0 bg-amber-50 border-t border-amber-200 px-8 py-3 flex items-center gap-2 text-sm text-amber-700">
          <AlertCircle size={15} className="shrink-0" />
          No Twilio number configured for <strong>{activeBusiness?.name}</strong>.
          Add one in Settings → Business Info to enable inbound SMS.
        </div>
      )}
    </div>
  )
}
