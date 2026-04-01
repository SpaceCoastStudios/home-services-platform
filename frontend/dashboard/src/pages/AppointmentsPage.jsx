import { useState, useEffect } from 'react'
import { Plus, X, ChevronLeft, ChevronRight, Clock, User, Calendar, Search } from 'lucide-react'
import {
  getAppointments, createAppointment, cancelAppointment, updateAppointment,
  getCustomers, getServices, getTechnicians, getAvailability,
} from '../services/api'
import { useBusinessContext } from '../hooks/useBusinessContext'

const STATUS_COLORS = {
  pending: 'bg-yellow-100 text-yellow-700',
  confirmed: 'bg-green-100 text-green-700',
  in_progress: 'bg-blue-100 text-blue-700',
  completed: 'bg-gray-100 text-gray-600',
  cancelled: 'bg-red-100 text-red-700',
  no_show: 'bg-red-100 text-red-700',
}

function formatDate(dateStr) {
  return new Date(dateStr + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
}

function formatTime(isoStr) {
  return new Date(isoStr).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
}

export default function AppointmentsPage() {
  const { activeBusinessId } = useBusinessContext()
  const [appointments, setAppointments] = useState([])
  const [showCreate, setShowCreate] = useState(false)
  const [filter, setFilter] = useState('')
  const [loading, setLoading] = useState(true)

  // Create flow — stepped wizard
  const [step, setStep] = useState(1) // 1=customer, 2=service, 3=pick slot, 4=confirm
  const [customers, setCustomers] = useState([])
  const [services, setServices] = useState([])
  const [technicians, setTechnicians] = useState([])
  const [selectedCustomer, setSelectedCustomer] = useState(null)
  const [selectedService, setSelectedService] = useState(null)
  const [availableDays, setAvailableDays] = useState([])
  const [selectedSlot, setSelectedSlot] = useState(null)
  const [slotsLoading, setSlotsLoading] = useState(false)
  const [weekOffset, setWeekOffset] = useState(0)
  const [customerSearch, setCustomerSearch] = useState('')
  const [error, setError] = useState('')

  const load = async () => {
    if (activeBusinessId == null) return
    setLoading(true)
    try {
      const params = {}
      if (filter) params.status = filter
      setAppointments(await getAppointments(params, activeBusinessId))
    } catch (err) { console.error(err) }
    setLoading(false)
  }

  useEffect(() => { load() }, [filter, activeBusinessId])

  const openCreate = async () => {
    const [c, s, t] = await Promise.all([
      getCustomers('', activeBusinessId),
      getServices(activeBusinessId),
      getTechnicians(activeBusinessId),
    ])
    setCustomers(c)
    setServices(s.filter(sv => sv.is_active))
    setTechnicians(t)
    setStep(1)
    setSelectedCustomer(null)
    setSelectedService(null)
    setSelectedSlot(null)
    setAvailableDays([])
    setWeekOffset(0)
    setCustomerSearch('')
    setError('')
    setShowCreate(true)
  }

  const pickService = async (service) => {
    setSelectedService(service)
    setSelectedSlot(null)
    setWeekOffset(0)
    setStep(3)
    await loadSlots(service.id, 0)
  }

  const loadSlots = async (serviceId, offset) => {
    setSlotsLoading(true)
    try {
      const today = new Date()
      const start = new Date(today)
      start.setDate(start.getDate() + (offset * 7))
      if (offset === 0) start.setDate(start.getDate()) // start from today
      const end = new Date(start)
      end.setDate(end.getDate() + 6)
      const startStr = start.toISOString().split('T')[0]
      const endStr = end.toISOString().split('T')[0]
      const res = await getAvailability(serviceId, startStr, endStr, null, activeBusinessId)
      setAvailableDays(res.availability || [])
    } catch (err) {
      console.error(err)
      setAvailableDays([])
    }
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
      load()
    } catch (err) { setError(err.message) }
  }

  const handleCancel = async (id) => {
    if (!confirm('Cancel this appointment?')) return
    await cancelAppointment(id, activeBusinessId)
    load()
  }

  const handleStatusChange = async (id, newStatus) => {
    await updateAppointment(id, { status: newStatus }, activeBusinessId)
    load()
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Appointments</h1>
        <button onClick={openCreate} className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700">
          <Plus size={16} /> New Appointment
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-4">
        {['', 'pending', 'confirmed', 'in_progress', 'completed', 'cancelled'].map((s) => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              filter === s ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 border border-gray-300 hover:bg-gray-50'
            }`}
          >
            {s || 'All'}
          </button>
        ))}
      </div>

      {/* Table */}
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
                  <td className="px-6 py-4 text-sm">{appt.service_name || '—'}</td>
                  <td className="px-6 py-4 text-sm">{appt.technician_name || 'Unassigned'}</td>
                  <td className="px-6 py-4">
                    <select
                      value={appt.status}
                      onChange={(e) => handleStatusChange(appt.id, e.target.value)}
                      className={`text-xs font-medium rounded-full px-2.5 py-1 border-0 cursor-pointer ${STATUS_COLORS[appt.status] || 'bg-gray-100'}`}
                    >
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

      {/* Create Modal — Stepped Wizard */}
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

            {/* Progress indicator */}
            <div className="flex gap-1 mb-5">
              {[1,2,3,4].map(s => (
                <div key={s} className={`h-1 flex-1 rounded-full ${s <= step ? 'bg-blue-600' : 'bg-gray-200'}`} />
              ))}
            </div>

            {error && <div className="bg-red-50 text-red-700 px-3 py-2 rounded-lg text-sm mb-3">{error}</div>}

            {/* Step 1: Customer */}
            {step === 1 && (() => {
              const q = customerSearch.toLowerCase()
              const filtered = q
                ? customers.filter(c =>
                    `${c.first_name} ${c.last_name}`.toLowerCase().includes(q) ||
                    c.phone.includes(q) ||
                    (c.email && c.email.toLowerCase().includes(q))
                  )
                : customers
              return (
                <div>
                  <div className="relative mb-3">
                    <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Search by name, phone, or email..."
                      value={customerSearch}
                      onChange={(e) => setCustomerSearch(e.target.value)}
                      autoFocus
                      className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                    />
                  </div>
                  <div className="space-y-2 max-h-80 overflow-auto">
                    {filtered.length === 0 ? (
                      <div className="text-center text-gray-400 py-6 text-sm">
                        {q ? 'No customers match your search' : 'No customers found'}
                      </div>
                    ) : (
                      filtered.map(c => (
                        <button key={c.id} onClick={() => { setSelectedCustomer(c); setStep(2) }}
                          className={`w-full text-left px-4 py-3 rounded-lg border transition-colors hover:border-blue-400 hover:bg-blue-50 ${
                            selectedCustomer?.id === c.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                          }`}>
                          <div className="flex items-center gap-3">
                            <div className="w-9 h-9 rounded-full bg-gray-200 flex items-center justify-center text-sm font-medium text-gray-600">
                              {c.first_name[0]}{c.last_name[0]}
                            </div>
                            <div>
                              <p className="font-medium text-sm text-gray-900">{c.first_name} {c.last_name}</p>
                              <p className="text-xs text-gray-500">{c.phone}{c.email ? ` · ${c.email}` : ''}</p>
                            </div>
                          </div>
                        </button>
                      ))
                    )}
                  </div>
                </div>
              )
            })()}

            {/* Step 2: Service */}
            {step === 2 && (
              <div className="space-y-2">
                {services.map(s => (
                  <button key={s.id} onClick={() => pickService(s)}
                    className="w-full text-left px-4 py-3 rounded-lg border border-gray-200 transition-colors hover:border-blue-400 hover:bg-blue-50">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-sm text-gray-900">{s.name}</p>
                        <p className="text-xs text-gray-500">{s.category} · {s.duration_minutes} min</p>
                      </div>
                      {s.base_price && <span className="text-sm font-semibold text-gray-700">${Number(s.base_price).toFixed(0)}</span>}
                    </div>
                  </button>
                ))}
              </div>
            )}

            {/* Step 3: Available Slots */}
            {step === 3 && (
              <div>
                {/* Week navigation */}
                <div className="flex items-center justify-between mb-4">
                  <button onClick={() => changeWeek(-1)} disabled={weekOffset === 0}
                    className="p-1.5 rounded-lg hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed">
                    <ChevronLeft size={18} />
                  </button>
                  <span className="text-sm font-medium text-gray-600">
                    {weekOffset === 0 ? 'This Week' : weekOffset === 1 ? 'Next Week' : `${weekOffset} Weeks Out`}
                  </span>
                  <button onClick={() => changeWeek(1)}
                    className="p-1.5 rounded-lg hover:bg-gray-100">
                    <ChevronRight size={18} />
                  </button>
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
                          {day.slots.map((slot, i) => {
                            const isSelected = selectedSlot?.start === slot.start
                            return (
                              <button key={i} onClick={() => { setSelectedSlot(slot); setStep(4) }}
                                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                                  isSelected
                                    ? 'bg-blue-600 text-white'
                                    : 'bg-gray-100 text-gray-700 hover:bg-blue-100 hover:text-blue-700'
                                }`}>
                                {formatTime(slot.start)}
                              </button>
                            )
                          })}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Step 4: Confirm */}
            {step === 4 && selectedCustomer && selectedService && selectedSlot && (
              <div>
                <div className="bg-gray-50 rounded-xl p-5 space-y-4">
                  <div className="flex items-center gap-3">
                    <User size={18} className="text-gray-400" />
                    <div>
                      <p className="text-xs text-gray-500">Customer</p>
                      <p className="font-medium text-gray-900">{selectedCustomer.first_name} {selectedCustomer.last_name}</p>
                      <p className="text-xs text-gray-500">{selectedCustomer.phone}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Clock size={18} className="text-gray-400" />
                    <div>
                      <p className="text-xs text-gray-500">Service</p>
                      <p className="font-medium text-gray-900">{selectedService.name}</p>
                      <p className="text-xs text-gray-500">{selectedService.duration_minutes} min · {selectedService.base_price ? `$${Number(selectedService.base_price).toFixed(0)}` : 'Quote on arrival'}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Calendar size={18} className="text-gray-400" />
                    <div>
                      <p className="text-xs text-gray-500">Date & Time</p>
                      <p className="font-medium text-gray-900">
                        {new Date(selectedSlot.start).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
                      </p>
                      <p className="text-sm text-gray-600">{formatTime(selectedSlot.start)} – {formatTime(selectedSlot.end)}</p>
                    </div>
                  </div>
                  {selectedCustomer.address && (
                    <div className="text-sm">
                      <p className="text-xs text-gray-500">Address</p>
                      <p className="text-gray-700">{selectedCustomer.address}</p>
                    </div>
                  )}
                </div>

                <div className="flex gap-3 mt-5">
                  <button onClick={() => setStep(3)}
                    className="flex-1 bg-gray-100 text-gray-700 py-2.5 rounded-lg font-medium hover:bg-gray-200">
                    Change Time
                  </button>
                  <button onClick={handleCreate}
                    className="flex-1 bg-blue-600 text-white py-2.5 rounded-lg font-medium hover:bg-blue-700">
                    Confirm Booking
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
