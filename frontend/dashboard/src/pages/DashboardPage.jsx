import { useState, useEffect } from 'react'
import { Calendar, Users, MessageSquare, CheckCircle, Clock } from 'lucide-react'
import { getAppointments, getCustomers, getContactSubmissions } from '../services/api'
import { useBusinessContext } from '../hooks/useBusinessContext'

const STATUS_PILL = {
  confirmed: 'bg-[var(--status-confirmed-bg)] text-[var(--status-confirmed-fg)]',
  pending: 'bg-[var(--status-pending-bg)] text-[var(--status-pending-fg)]',
  in_progress: 'bg-[var(--status-inprogress-bg)] text-[var(--status-inprogress-fg)]',
  en_route: 'bg-[var(--status-enroute-bg)] text-[var(--status-enroute-fg)]',
  completed: 'bg-[var(--status-completed-bg)] text-[var(--status-completed-fg)]',
  cancelled: 'bg-[var(--status-cancelled-bg)] text-[var(--status-cancelled-fg)]',
  no_show: 'bg-[var(--status-noshow-bg)] text-[var(--status-noshow-fg)]',
  emergency: 'bg-[var(--status-emergency-bg)] text-[var(--status-emergency-fg)]',
}

function StatCard({ icon: Icon, label, value }) {
  return (
    <div className="bg-surface rounded-xl border border-line p-6">
      <div className="flex items-center gap-4">
        <div className="p-3 rounded-lg bg-brand-tint">
          <Icon size={22} className="text-brand-ink" />
        </div>
        <div>
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const { activeBusinessId, activeBusiness } = useBusinessContext()
  const [stats, setStats] = useState({ todayAppointments: 0, totalCustomers: 0, pendingContacts: 0, completedToday: 0 })
  const [recentAppointments, setRecentAppointments] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (activeBusinessId == null) return
    setLoading(true)
    async function load() {
      try {
        const today = new Date().toISOString().split('T')[0]
        const [appts, customers, contacts] = await Promise.all([
          getAppointments({ start_date: today, end_date: today }, activeBusinessId),
          getCustomers('', activeBusinessId),
          getContactSubmissions('new', activeBusinessId),
        ])
        setStats({
          todayAppointments: appts.length,
          totalCustomers: customers.length,
          pendingContacts: contacts.length,
          completedToday: appts.filter((a) => a.status === 'completed').length,
        })
        setRecentAppointments(appts.slice(0, 5))
      } catch (err) {
        console.error('Failed to load dashboard data:', err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [activeBusinessId])

  if (activeBusinessId == null) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400">
        Select a business from the sidebar to view its dashboard.
      </div>
    )
  }

  if (loading) return <p className="text-gray-500">Loading dashboard...</p>

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-1">Dashboard</h1>
      {activeBusiness?.name && (
        <p className="text-gray-500 mb-6">{activeBusiness.name}</p>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard icon={Calendar} label="Today's Appointments" value={stats.todayAppointments} />
        <StatCard icon={Users} label="Total Customers" value={stats.totalCustomers} />
        <StatCard icon={MessageSquare} label="Pending Contacts" value={stats.pendingContacts} />
        <StatCard icon={CheckCircle} label="Completed Today" value={stats.completedToday} />
      </div>

      <div className="bg-surface rounded-xl border border-line">
        <div className="px-6 py-4 border-b border-line">
          <h2 className="font-semibold text-gray-900">Today's Schedule</h2>
        </div>
        {recentAppointments.length === 0 ? (
          <div className="p-6 text-center text-gray-400">No appointments scheduled for today</div>
        ) : (
          <div className="divide-y divide-gray-100">
            {recentAppointments.map((appt) => (
              <div key={appt.id} className="px-6 py-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Clock size={14} />
                    {new Date(appt.scheduled_start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{appt.customer_name || 'Customer'}</p>
                    <p className="text-sm text-gray-500">{appt.service_name || 'Service'}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm text-gray-500">{appt.technician_name || 'Unassigned'}</span>
                  <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${STATUS_PILL[appt.status] || STATUS_PILL.cancelled}`}>
                    {appt.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
