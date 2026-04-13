import { useState, useEffect } from 'react'
import { Plus, X, ChevronLeft, ChevronRight, Clock, User, Calendar, Search, Repeat, RefreshCw } from 'lucide-react'
import {
  getAppointments, createAppointment, cancelAppointment, updateAppointment,
  getCustomers, getServices, getTechnicians, getAvailability,
  getRecurringSchedules, createRecurringSchedule, updateRecurringSchedule, deactivateRecurringSchedule,
} from '../services/api'
import { useBusinessContext } from '../hooks/useBusinessContext'

const STATUS_COLORS = {
  pending: 'bg-yellow-100 text-yellow-700',
  confirmed: 'bg-green-100 text-green-700',
  in_progress: 'bg-blue-100 text-blue-700',
  en_route: 'bg-purple-100 text-purple-700',
  completed: 'bg-gray-100 text-gray-600',
  cancelled: 'bg-red-100 text-red-700',
  no_show: 'bg-red-100 text-red-700',
}

const FREQ_LABELS = { weekly: 'Weekly', biweekly: 'Every 2 Weeks', monthly: 'Monthly' }
const DOW_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

function formatDate(dateStr) {
  return new Date(dateStr + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
}
function formatTime(isoStr) {
  return new Date(isoStr).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
}

export default function AppointmentsPage() {
  const { activeBusinessId } = useBusinessContext()
  const [tab, setTab] = useState('appointments') // 'appointments' | 'recurring'
  const [appointments, setAppointments] = useState([])
  const [recurringSchedules, setRecurringSchedules] = useState([])
  const [showCreate, setShowCreate] = useState(false)
  const [showRecurringCreate, setShowRecurringCreate] = useState(false)
  const [filter, setFilter] = useState('')
  const [loading, setLoading] = useState(true)

  // Shared lookup data
  const [customers, setCustomers] = useState([])
  const [services, setServices] = useState([])
  const [technicians, setTechnicians] = useState([])

  // One-off create wizard
  const [step, setStep] = useState(1)
  const [selectedCustomer, setSelectedCustomer] = useState(null)
  const [selectedService, setSelectedService] = useState(null)
  const [availableDays, setAvailableDays] = useState([])
  const [selectedSlot, setSelectedSlot] = useState(null)
  const [slotsLoading, setSlotsLoading] = useState(false)
  const [weekOffset, setWeekOffset] = useState(0)
  const [customerSearch, setCustomerSearch] = useState('')
  const [error, setError] = useState('')

  // Recurring create form
  const [recForm, setRecForm] = useState({
    customer_id: '',
    service_type_id: '',
    technician_id: '',
    frequency: 'weekly',
    preferred_day_of_week: '0',
    preferred_day_of_month: '1',
    preferred_time: '09:00',
    start_date: new Date().toISOString().split('T')[0],
    end_date: '',
    notes: '',
    address: '',
  })
  const [recError, setRecError] = useState('')
  const [recLoading, setRecLoading] = useState(false)

  const loadAppointments = async () => {
    if (activeBusinessId == null) return
    setLoading(true)
    try {
      const params = {}
      if (filter) params.status = filter
      setAppointments(await getAppointments(params, activeBusinessId))
    } catch (err) { console.error(err) }
    setLoading(false)
  }

  const loadRecurring = async () => {
    if (activeBusinessId == null) return
    try {
      setRecurringSchedules(await getRecurringSchedules({}, activeBusinessId))
    } catch (err) { console.error(err) }
  }

  useEffect(() => { loadAppointments() }, [filter, activeBusinessId])
  useEffect(() => { if (tab === 'recurring') loadRecurring() }, [tab, activeBusinessId])

  const loadLookups = async () => {
    const [c, s, t] = await Promise.all([
      getCustomers('', activeBusinessId),
      getServices(activeBusinessId),
      getTechnicians(activeBusinessId),
    ])
    setCustomers(c)
    setServices(s.filter(sv => sv.is_active))
    setTechnicians(t)
  }

  const openCreate = async () => {
    await loadLookups()
    setStep(1); setSelectedCustomer(null); setSelectedService(null)
    setSelectedSlot(null); setAvailableDays([]); setWeekOffset(0)
    setCustomerSearch(''); setError('')
    setShowCreate(true)
  }

  const openRecurringCreate = async () => {
    await loadLookups()
    setRecForm({
      customer_id: '', service_type_id: '', technician_id: '',
      frequency: 'weekly', preferred_day_of_week: '0', preferred_day_of_month: '1',
      preferred_time: '09:00', start_date: new Date().toISOString().split('T')[0],
      end_date: '', notes: '', address: '',
    })
    setRecError('')
    setShowRecurringCreate(true)
  }

  // ── One-off booking helpers ───────────────────────────────────────────────
  const pickService = async (service) => {
    setSelectedService(service); setSelectedSlot(null); setWeekOffset(0); setStep(3)
    await loadSlots(service.id, 0)
  }

  const loadSlots = async (serviceId, offset) => {
    setSlotsLoading(true)
    try {
      const today = new Date()
      const start = new Date(today); start.setDate(start.getDate() + (offset * 7))
      const end = new Date(start); end.setDate(end.getDate() + 6)
      const res = await getAvailability(serviceId, start.toISOString().split('T')[0], end.toISOString().split('T')[0], null, activeBusinessId)
      setAvailableDays(res.availability || [])
    } catch (err) { console.error(err); setAvailableDays([]) }
    setSlotsLoading(false)
  }

  const changeWeek = async (delta) => {
    const newOffset = weekOffset + delta
    if (newOffset < 0) return
    setWeekOffset(newOffset)
    await loadSlots(selectedService.id, newOffset)
  }

  const handleCreate = async () => {
    setError('')
    try {
      await createAppointment({
        customer_id: selectedCustomer.id,
        service_type_id: selectedService.id,
        scheduled_start: selectedSlot.start,
        source: 'dashboard',
        address: selectedCustomer.address,
      }, activeBusinessId)
      setShowCreate(false)
      loadAppointments()
    } catch (err) { setError(err.message) }
  }

  const handleCancel = async (id) => {
    if (!confirm('Cancel this appointment?')) return
    await cancelAppointment(id, activeBusinessId)
    loadAppointments()
  }

  const handleStatusChange = async (id, newStatus) => {
    await updateAppointment(id, { status: newStatus }, activeBusinessId)
    loadAppointments()
  }

  // ── Recurring create submit ──────────────────────────────────────────────
  const handleRecurringCreate = async () => {
    setRecError(''); setRecLoading(true)
    try {
      const payload = {
        customer_id: parseInt(recForm.customer_id),
        service_type_id: parseInt(recForm.service_type_id),
        technician_id: recForm.technician_id ? parseInt(recForm.technician_id) : null,
        frequency: recForm.frequency,
        preferred_time: recForm.preferred_time + ':00',
        start_date: recForm.start_date,
        end_date: recForm.end_date || null,
        notes: recForm.notes || null,
        address: recForm.address || null,
      }
      if (recForm.frequency === 'monthly') {
        payload.preferred_day_of_month = parseInt(recForm.preferred_day_of_month)
      } else {
        payload.preferred_day_of_week = parseInt(recForm.preferred_day_of_week)
      }
      await createRecurringSchedule(payload, activeBusinessId)
      setShowRecurringCreate(false)
      loadRecurring()
      loadAppointments()
    } catch (err) { setRecError(err.message) }
    setRecLoading(false)
  }

  const handlePauseResume = async (schedule) => {
    await updateRecurringSchedule(schedule.id, { is_active: !schedule.is_active }, activeBusinessId)
    loadRecurring()
  }

  const handleDeactivate = async (id) => {
    if (!confirm('Stop this recurring series? Future appointments will not be cancelled.')) return
    await deactivateRecurringSchedule(id, activeBusinessId)
    loadRecurring()
  }

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Appointments</h1>
        <div className="flex gap-2">
          <button onClick={openRecurringCreate}
            className="flex items-center gap-2 bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-50">
            <Repeat size={16} /> New Recurring
          </button>
          <button onClick={openCreate}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700">
            <Plus size={16} /> New Appointment
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-5 border-b border-gray-200">
        {[['appointments', 'Appointments'], ['recurring', 'Recurring Series']].map(([key, label]) => (
          <button key={key} onClick={() => setTab(key)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              tab === key ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}>
            {label}
          </button>
        ))}
      </div>

      {/* ── Appointments Tab ─────────────────────────────────────────────── */}
      {tab === 'appointments' && (
        <>
          <div className="flex gap-2 mb-4">
            {['', 'pending', 'confirmed', 'in_progress', 'en_route', 'completed', 'cancelled'].map((s) => (
              <button key={s} onClick={() => setFilter(s)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  filter === s ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 border border-gray-300 hover:bg-gray-50'
                }`}>
                {s || 'All'}
              </button>
            ))}
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            {loading ? (
              <div className="p-6 text-center text-gray-400">Loading...</div>
            ) : appointments.length === 0 ? (
              <div className="p-6 text-center text-gray-400">No appointments found</div>
            ) : (
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    <th className="px-6 py-3">Date/Time</th>
                    <th className="px-6 py-3">Customer</th>
                    <th className="px-6 py-3">Service</th>
                    <th className="px-6 py-3">Technician</th>
                    <th className="px-6 py-3">Status</th>
                    <th className="px-6 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {appointments.map((appt) => (
                    <tr key={appt.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm">
                        <div className="font-medium">{new Date(appt.scheduled_start).toLocaleDateString()}</div>
                        <div className="text-gray-500">{new Date(appt.scheduled_start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} - {new Date(appt.scheduled_end).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                      </td>
                      <td className="px-6 py-4 text-sm font-medium">{appt.customer_name || '—'}</td>
                      <td className="px-6 py-4 text-sm">
                        <div className="flex items-center gap-1.5">
                          {appt.service_name || '—'}
                          {appt.recurring_schedule_id && (
                            <span title="Recurring appointment" className="inline-flex items-center gap-0.5 bg-purple-100 text-purple-700 text-xs px-1.5 py-0.5 rounded-full">
                              <Repeat size={10} /> Recurring
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm">{appt.technician_name || 'Unassigned'}</td>
                      <td className="px-6 py-4">
                        <select value={appt.status} onChange={(e) => handleStatusChange(appt.id, e.target.value)}
                          className={`text-xs font-medium rounded-full px-2.5 py-1 border-0 cursor-pointer ${STATUS_COLORS[appt.status] || 'bg-gray-100'}`}>
                          {Object.keys(STATUS_COLORS).map(s => <option key={s} value={s}>{s}</option>)}
                        </select>
                      </td>
                      <td className="px-6 py-4">
                        {appt.status !== 'cancelled' && appt.status !== 'completed' && (
                          <button onClick={() => handleCancel(appt.id)} className="text-red-600 hover:text-red-800 text-sm">Cancel</button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}

      {/* ── Recurring Tab ────────────────────────────────────────────────── */}
      {tab === 'recurring' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          {recurringSchedules.length === 0 ? (
            <div className="p-12 text-center">
              <Repeat size={40} className="mx-auto text-gray-300 mb-3" />
              <p className="text-gray-500 font-medium">No recurring series yet</p>
              <p className="text-sm text-gray-400 mt-1">Set up a recurring schedule to automatically generate weekly, biweekly, or monthly appointments.</p>
              <button onClick={openRecurringCreate} className="mt-4 inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700">
                <Plus size={15} /> Create Recurring Series
              </button>
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <th className="px-6 py-3">Customer</th>
                  <th className="px-6 py-3">Service</th>
                  <th className="px-6 py-3">Schedule</th>
                  <th className="px-6 py-3">Technician</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {recurringSchedules.map((s) => {
                  const scheduleDesc = s.frequency === 'monthly'
                    ? `Monthly on the ${s.preferred_day_of_month}${['st','nd','rd'][((s.preferred_day_of_month-1)%10)] || 'th'} at ${s.preferred_time}`
                    : `${FREQ_LABELS[s.frequency]} on ${DOW_LABELS[s.preferred_day_of_week] || '?'} at ${s.preferred_time}`
                  return (
                    <tr key={s.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm font-medium">{s.customer_name || '—'}</td>
                      <td className="px-6 py-4 text-sm">{s.service_name || '—'}</td>
                      <td className="px-6 py-4 text-sm">
                        <div className="flex items-center gap-1.5">
                          <Repeat size={13} className="text-purple-500 shrink-0" />
                          <span>{scheduleDesc}</span>
                        </div>
                        {s.end_date && <div className="text-xs text-gray-400 mt-0.5">Until {s.end_date}</div>}
                      </td>
                      <td className="px-6 py-4 text-sm">{s.technician_name || 'Auto-assign'}</td>
                      <td className="px-6 py-4">
                        <span className={`inline-block text-xs font-medium rounded-full px-2.5 py-1 ${s.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                          {s.is_active ? 'Active' : 'Paused'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex gap-3 text-sm">
                          <button onClick={() => handlePauseResume(s)}
                            className="text-blue-600 hover:text-blue-800">
                            {s.is_active ? 'Pause' : 'Resume'}
                          </button>
                          {s.is_active && (
                            <button onClick={() => handleDeactivate(s.id)} className="text-red-600 hover:text-red-800">
                              Stop
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* ── One-off Appointment Modal ──────────────────────────────────────── */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg p-6 max-h-[85vh] overflow-auto">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                {step > 1 && step < 4 && (
                  <button onClick={() => setStep(step - 1)} className="text-gray-400 hover:text-gray-600"><ChevronLeft size={20} /></button>
                )}
                <h2 className="text-lg font-semibold">
                  {step === 1 && 'Select Customer'}
                  {step === 2 && 'Select Service'}
                  {step === 3 && 'Pick a Time Slot'}
                  {step === 4 && 'Confirm Appointment'}
                </h2>
              </div>
              <button onClick={() => setShowCreate(false)} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
            </div>
            <div className="flex gap-1 mb-5">
              {[1,2,3,4].map(s => (
                <div key={s} className={`h-1 flex-1 rounded-full ${s <= step ? 'bg-blue-600' : 'bg-gray-200'}`} />
              ))}
            </div>
            {error && <div className="bg-red-50 text-red-700 px-3 py-2 rounded-lg text-sm mb-3">{error}</div>}

            {step === 1 && (() => {
              const q = customerSearch.toLowerCase()
              const filtered = q ? customers.filter(c =>
                `${c.first_name} ${c.last_name}`.toLowerCase().includes(q) ||
                c.phone.includes(q) || (c.email && c.email.toLowerCase().includes(q))
              ) : customers
              return (
                <div>
                  <div className="relative mb-3">
                    <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input type="text" placeholder="Search by name, phone, or email..."
                      value={customerSearch} onChange={(e) => setCustomerSearch(e.target.value)} autoFocus
                      className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none" />
                  </div>
                  <div className="space-y-2 max-h-80 overflow-auto">
                    {filtered.length === 0 ? (
                      <div className="text-center text-gray-400 py-6 text-sm">{q ? 'No customers match' : 'No customers found'}</div>
                    ) : filtered.map(c => (
                      <button key={c.id} onClick={() => { setSelectedCustomer(c); setStep(2) }}
                        className={`w-full text-left px-4 py-3 rounded-lg border transition-colors hover:border-blue-400 hover:bg-blue-50 ${selectedCustomer?.id === c.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}`}>
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 rounded-full bg-gray-200 flex items-center justify-center text-sm font-medium text-gray-600">
                            {c.first_name[0]}{c.last_name[0]}
                          </div>
                          <div>
                            <p className="font-medium text-sm">{c.first_name} {c.last_name}</p>
                            <p className="text-xs text-gray-500">{c.phone}{c.email ? ` · ${c.email}` : ''}</p>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )
            })()}

            {step === 2 && (
              <div className="space-y-2">
                {services.map(s => (
                  <button key={s.id} onClick={() => pickService(s)}
                    className="w-full text-left px-4 py-3 rounded-lg border border-gray-200 hover:border-blue-400 hover:bg-blue-50">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-sm">{s.name}</p>
                        <p className="text-xs text-gray-500">{s.category} · {s.duration_minutes} min</p>
                      </div>
                      {s.base_price && <span className="text-sm font-semibold text-gray-700">${Number(s.base_price).toFixed(0)}</span>}
                    </div>
                  </button>
                ))}
              </div>
            )}

            {step === 3 && (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <button onClick={() => changeWeek(-1)} disabled={weekOffset === 0}
                    className="p-1.5 rounded-lg hover:bg-gray-100 disabled:opacity-30"><ChevronLeft size={18} /></button>
                  <span className="text-sm font-medium text-gray-600">
                    {weekOffset === 0 ? 'This Week' : weekOffset === 1 ? 'Next Week' : `${weekOffset} Weeks Out`}
                  </span>
                  <button onClick={() => changeWeek(1)} className="p-1.5 rounded-lg hover:bg-gray-100"><ChevronRight size={18} /></button>
                </div>
                {slotsLoading ? (
                  <div className="text-center text-gray-400 py-8">Loading available slots...</div>
                ) : availableDays.length === 0 ? (
                  <div className="text-center text-gray-400 py-8">
                    <Calendar size={32} className="mx-auto mb-2 opacity-50" />
                    <p>No available slots this week</p>
                    <button onClick={() => changeWeek(1)} className="text-blue-600 text-sm mt-2 hover:underline">Check next week</button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {availableDays.map(day => (
                      <div key={day.date}>
                        <p className="text-sm font-semibold text-gray-700 mb-2">{formatDate(day.date)}</p>
                        <div className="flex flex-wrap gap-2">
                          {day.slots.map((slot, i) => (
                            <button key={i} onClick={() => { setSelectedSlot(slot); setStep(4) }}
                              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                                selectedSlot?.start === slot.start ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-blue-100 hover:text-blue-700'
                              }`}>
                              {formatTime(slot.start)}
                            </button>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {step === 4 && selectedCustomer && selectedService && selectedSlot && (
              <div>
                <div className="bg-gray-50 rounded-xl p-5 space-y-4">
                  <div className="flex items-center gap-3">
                    <User size={18} className="text-gray-400" />
                    <div>
                      <p className="text-xs text-gray-500">Customer</p>
                      <p className="font-medium">{selectedCustomer.first_name} {selectedCustomer.last_name}</p>
                      <p className="text-xs text-gray-500">{selectedCustomer.phone}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Clock size={18} className="text-gray-400" />
                    <div>
                      <p className="text-xs text-gray-500">Service</p>
                      <p className="font-medium">{selectedService.name}</p>
                      <p className="text-xs text-gray-500">{selectedService.duration_minutes} min · {selectedService.base_price ? `$${Number(selectedService.base_price).toFixed(0)}` : 'Quote on arrival'}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Calendar size={18} className="text-gray-400" />
                    <div>
                      <p className="text-xs text-gray-500">Date & Time</p>
                      <p className="font-medium">{new Date(selectedSlot.start).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}</p>
                      <p className="text-sm text-gray-600">{formatTime(selectedSlot.start)} – {formatTime(selectedSlot.end)}</p>
                    </div>
                  </div>
                </div>
                <div className="flex gap-3 mt-5">
                  <button onClick={() => setStep(3)} className="flex-1 bg-gray-100 text-gray-700 py-2.5 rounded-lg font-medium hover:bg-gray-200">Change Time</button>
                  <button onClick={handleCreate} className="flex-1 bg-blue-600 text-white py-2.5 rounded-lg font-medium hover:bg-blue-700">Confirm Booking</button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Recurring Create Modal ─────────────────────────────────────────── */}
      {showRecurringCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg p-6 max-h-[90vh] overflow-auto">
            <div className="flex items-center justify-between mb-5">
              <div className="flex items-center gap-2">
                <Repeat size={20} className="text-purple-600" />
                <h2 className="text-lg font-semibold">New Recurring Series</h2>
              </div>
              <button onClick={() => setShowRecurringCreate(false)} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
            </div>

            {recError && <div className="bg-red-50 text-red-700 px-3 py-2 rounded-lg text-sm mb-4">{recError}</div>}

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Customer *</label>
                <select value={recForm.customer_id} onChange={e => setRecForm(f => ({ ...f, customer_id: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none">
                  <option value="">Select a customer…</option>
                  {customers.map(c => <option key={c.id} value={c.id}>{c.first_name} {c.last_name} — {c.phone}</option>)}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Service *</label>
                <select value={recForm.service_type_id} onChange={e => setRecForm(f => ({ ...f, service_type_id: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none">
                  <option value="">Select a service…</option>
                  {services.map(s => <option key={s.id} value={s.id}>{s.name} ({s.duration_minutes} min)</option>)}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Preferred Technician</label>
                <select value={recForm.technician_id} onChange={e => setRecForm(f => ({ ...f, technician_id: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none">
                  <option value="">Auto-assign</option>
                  {technicians.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Frequency *</label>
                  <select value={recForm.frequency} onChange={e => setRecForm(f => ({ ...f, frequency: e.target.value }))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none">
                    <option value="weekly">Weekly</option>
                    <option value="biweekly">Every 2 Weeks</option>
                    <option value="monthly">Monthly</option>
                  </select>
                </div>

                {recForm.frequency !== 'monthly' ? (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Day of Week *</label>
                    <select value={recForm.preferred_day_of_week} onChange={e => setRecForm(f => ({ ...f, preferred_day_of_week: e.target.value }))}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none">
                      {DOW_LABELS.map((d, i) => <option key={i} value={i}>{d}</option>)}
                    </select>
                  </div>
                ) : (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Day of Month *</label>
                    <input type="number" min="1" max="28" value={recForm.preferred_day_of_month}
                      onChange={e => setRecForm(f => ({ ...f, preferred_day_of_month: e.target.value }))}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none" />
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Preferred Time *</label>
                  <input type="time" value={recForm.preferred_time} onChange={e => setRecForm(f => ({ ...f, preferred_time: e.target.value }))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Start Date *</label>
                  <input type="date" value={recForm.start_date} onChange={e => setRecForm(f => ({ ...f, start_date: e.target.value }))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none" />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">End Date <span className="text-gray-400">(optional — leave blank for ongoing)</span></label>
                <input type="date" value={recForm.end_date} onChange={e => setRecForm(f => ({ ...f, end_date: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none" />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Service Address</label>
                <input type="text" placeholder="123 Main St, City, FL" value={recForm.address}
                  onChange={e => setRecForm(f => ({ ...f, address: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none" />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <textarea rows={2} placeholder="Gate code, special instructions…" value={recForm.notes}
                  onChange={e => setRecForm(f => ({ ...f, notes: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none resize-none" />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button onClick={() => setShowRecurringCreate(false)}
                className="flex-1 bg-gray-100 text-gray-700 py-2.5 rounded-lg font-medium hover:bg-gray-200">
                Cancel
              </button>
              <button onClick={handleRecurringCreate} disabled={recLoading || !recForm.customer_id || !recForm.service_type_id}
                className="flex-1 bg-purple-600 text-white py-2.5 rounded-lg font-medium hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                {recLoading ? <><RefreshCw size={15} className="animate-spin" /> Creating…</> : <><Repeat size={15} /> Create Series</>}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
