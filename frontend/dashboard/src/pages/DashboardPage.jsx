import { useState, useEffect } from 'react'
import { Calendar, Users, MessageSquare, CheckCircle, Clock } from 'lucide-react'
import { getAppointments, getCustomers, getContactSubmissions } from '../services/api'
import { useBusinessContext } from '../hooks/useBusinessContext'

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-center gap-4">
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon size={22} className="text-white" />
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
        <StatCard icon={Calendar} label="Today's Appointments" value={stats.todayAppointments} color="bg-blue-600" />
        <StatCard icon={Users} label="Total Customers" value={stats.totalCustomers} color="bg-emerald-600" />
        <StatCard icon={MessageSquare} label="Pending Contacts" value={stats.pendingContacts} color="bg-amber-500" />
        <StatCard icon={CheckCircle} label="Completed Today" value={stats.completedToday} color="bg-purple-600" />
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
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
                  <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${
                    appt.status === 'confirmed' ? 'bg-green-100 text-green-700'
                    : appt.status === 'pending' ? 'bg-yellow-100 text-yellow-700'
                    : appt.status === 'in_progress' ? 'bg-blue-100 text-blue-700'
                    : appt.status === 'completed' ? 'bg-gray-100 text-gray-700'
                    : 'bg-red-100 text-red-700'
                  }`}>
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
