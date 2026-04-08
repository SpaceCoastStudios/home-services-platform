import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useBusinessContext } from '../hooks/useBusinessContext'
import {
  LayoutDashboard,
  Calendar,
  Users,
  Wrench,
  HardHat,
  Settings,
  MessageSquare,
  MessageCircle,
  LogOut,
  Building2,
  ChevronDown,
  PhoneCall,
} from 'lucide-react'
import { useState, useRef, useEffect } from 'react'

const businessNav = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/appointments', icon: Calendar, label: 'Appointments' },
  { to: '/customers', icon: Users, label: 'Customers' },
  { to: '/services', icon: Wrench, label: 'Services' },
  { to: '/technicians', icon: HardHat, label: 'Technicians' },
  { to: '/contacts', icon: MessageSquare, label: 'Contact Queue' },
  { to: '/sms', icon: MessageCircle, label: 'SMS Conversations' },
  { to: '/oncall', icon: PhoneCall, label: 'On-Call' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

function BusinessSelector() {
  const { activeBusiness, businesses, selectBusiness } = useBusinessContext()
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  // Close dropdown on outside click
  useEffect(() => {
    function handle(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handle)
    return () => document.removeEventListener('mousedown', handle)
  }, [])

  return (
    <div ref={ref} className="relative px-3 pb-3">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between gap-2 px-3 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 transition-colors text-sm text-left"
      >
        <div className="flex items-center gap-2 min-w-0">
          <Building2 size={15} className="text-blue-400 shrink-0" />
          <span className="truncate text-white font-medium">
            {activeBusiness?.name ?? 'Select business…'}
          </span>
        </div>
        <ChevronDown size={14} className={`text-gray-400 shrink-0 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="absolute left-3 right-3 top-full mt-1 z-50 bg-gray-800 border border-gray-700 rounded-lg shadow-lg overflow-hidden">
          {businesses.length === 0 && (
            <p className="px-3 py-2 text-xs text-gray-400">No businesses yet</p>
          )}
          {businesses.map((b) => (
            <button
              key={b.id}
              onClick={() => { selectBusiness(b); setOpen(false) }}
              className={`w-full text-left px-3 py-2 text-sm hover:bg-gray-700 transition-colors flex items-center justify-between gap-2 ${
                activeBusiness?.id === b.id ? 'text-blue-400 font-medium' : 'text-gray-200'
              }`}
            >
              <span className="truncate">{b.name}</span>
              <span className={`text-xs px-1.5 py-0.5 rounded shrink-0 ${
                b.plan === 'full' ? 'bg-blue-900 text-blue-300' : 'bg-gray-700 text-gray-400'
              }`}>
                {b.plan}
              </span>
            </button>
          ))}
          <div className="border-t border-gray-700">
            <NavLink
              to="/businesses"
              onClick={() => setOpen(false)}
              className="block px-3 py-2 text-xs text-gray-400 hover:text-white hover:bg-gray-700 transition-colors"
            >
              Manage all businesses →
            </NavLink>
          </div>
        </div>
      )}
    </div>
  )
}

export default function Layout() {
  const { user, logout } = useAuth()
  const { activeBusiness } = useBusinessContext()

  // Platform admins get a Businesses link at the top of nav
  const platformNav = user?.isPlatformAdmin
    ? [{ to: '/businesses', icon: Building2, label: 'All Businesses' }]
    : []

  const nav = [...platformNav, ...businessNav]

  // For business admins, show their business branding in the header
  const headerBusiness = !user?.isPlatformAdmin ? activeBusiness : null
  const brandColor = headerBusiness?.brand_color || null

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-900 text-gray-100 flex flex-col">
        {/* Header */}
        {headerBusiness ? (
          // Business admin view — show the business name with its brand color accent
          <div
            className="p-5 border-b border-gray-700"
            style={{ borderTop: `3px solid ${brandColor || '#2563eb'}` }}
          >
            {headerBusiness.logo_url ? (
              <img
                src={headerBusiness.logo_url}
                alt={headerBusiness.name}
                className="h-8 object-contain mb-2"
              />
            ) : (
              <div className="flex items-center gap-2 mb-1">
                <div
                  className="w-7 h-7 rounded-md flex items-center justify-center text-white text-xs font-bold shrink-0"
                  style={{ backgroundColor: brandColor || '#2563eb' }}
                >
                  {headerBusiness.name?.charAt(0) ?? '?'}
                </div>
                <h1 className="text-base font-bold leading-tight truncate">
                  {headerBusiness.name}
                </h1>
              </div>
            )}
            <p className="text-xs text-gray-400">Admin Dashboard</p>
          </div>
        ) : (
          // Platform admin view — always show Space Coast Studios
          <div className="p-5 border-b border-gray-700">
            <h1 className="text-lg font-bold">Space Coast Studios</h1>
            <p className="text-xs text-gray-400 mt-1">Platform Admin</p>
          </div>
        )}

        {/* Business selector — platform admins only */}
        {user?.isPlatformAdmin && (
          <div className="pt-3 border-b border-gray-700">
            <p className="px-4 pb-1 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Active Business
            </p>
            <BusinessSelector />
          </div>
        )}

        {/* Nav */}
        <nav className="flex-1 py-4 space-y-1 px-3 overflow-y-auto">
          {nav.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-gray-700 space-y-1">
          {activeBusiness?.name && (
            <p className="text-xs text-gray-500 truncate">
              Viewing: {activeBusiness.name}
            </p>
          )}
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">{user?.username}</span>
            <button
              onClick={logout}
              className="text-gray-400 hover:text-white transition-colors"
              title="Logout"
            >
              <LogOut size={18} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto bg-gray-50">
        <div className="p-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
