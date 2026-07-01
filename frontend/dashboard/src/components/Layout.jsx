import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useBusinessContext } from '../hooks/useBusinessContext'
import { useTheme } from '../hooks/useTheme'
import { computeBrandTokens } from '../utils/color'
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
  Bell,
  CreditCard,
  Eye,
  X,
  Sun,
  Moon,
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
  { to: '/notification-templates', icon: Bell, label: 'Notifications' },
  { to: '/oncall', icon: PhoneCall, label: 'On-Call' },
  { to: '/billing', icon: CreditCard, label: 'Billing' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

function BusinessSelector() {
  const { activeBusiness, businesses, selectBusiness } = useBusinessContext()
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

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
        className="w-full flex items-center justify-between gap-2 px-3 py-2 rounded-lg bg-surface border border-line hover:bg-subtle transition-colors text-sm text-left"
      >
        <div className="flex items-center gap-2 min-w-0">
          <Building2 size={15} className="text-brand shrink-0" />
          <span className="truncate text-ink font-medium">
            {activeBusiness?.name ?? 'Select business…'}
          </span>
        </div>
        <ChevronDown size={14} className={`text-gray-400 shrink-0 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="absolute left-3 right-3 top-full mt-1 z-50 bg-surface border border-line rounded-lg shadow-lg overflow-hidden">
          {businesses.length === 0 && (
            <p className="px-3 py-2 text-xs text-gray-400">No businesses yet</p>
          )}
          {businesses.map((b) => (
            <button
              key={b.id}
              onClick={() => { selectBusiness(b); setOpen(false) }}
              className={`w-full text-left px-3 py-2 text-sm hover:bg-subtle transition-colors flex items-center justify-between gap-2 ${
                activeBusiness?.id === b.id ? 'text-brand font-medium' : 'text-ink'
              }`}
            >
              <span className="truncate">{b.name}</span>
              <span className={`text-xs px-1.5 py-0.5 rounded shrink-0 ${
                b.plan === 'full' ? 'bg-brand-tint text-brand-ink' : 'bg-subtle text-gray-400'
              }`}>
                {b.plan}
              </span>
            </button>
          ))}
          <div className="border-t border-line">
            <NavLink
              to="/businesses"
              onClick={() => setOpen(false)}
              className="block px-3 py-2 text-xs text-gray-400 hover:text-ink hover:bg-subtle transition-colors"
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
  const { user, logout, isImpersonating, impersonatedBizName, exitImpersonation } = useAuth()
  const { activeBusiness } = useBusinessContext()
  const { theme, toggleTheme } = useTheme()
  const navigate = useNavigate()

  const platformNav = user?.isPlatformAdmin
    ? [{ to: '/businesses', icon: Building2, label: 'All Businesses' }]
    : []

  const nav = [...platformNav, ...businessNav]

  const headerBusiness = !user?.isPlatformAdmin ? activeBusiness : null
  const brandColor = headerBusiness?.brand_color || null

  useEffect(() => {
    const tokens = computeBrandTokens(brandColor, theme)
    const root = document.documentElement.style
    root.setProperty('--brand', tokens.brand)
    root.setProperty('--brand-hover', tokens.brandHover)
    root.setProperty('--brand-tint', tokens.brandTint)
    root.setProperty('--brand-ink', tokens.brandInk)
  }, [brandColor, theme])

  return (
    <div className="flex h-screen bg-page">
      <aside className="w-64 bg-page text-ink border-r border-line flex flex-col">
        {headerBusiness ? (
          <div
            className="p-5 border-b border-line"
            style={{ borderTop: '3px solid var(--brand)' }}
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
                  style={{ backgroundColor: 'var(--brand)' }}
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
          <div className="p-5 border-b border-line">
            <h1 className="text-lg font-bold">Launchpad</h1>
            <p className="text-xs text-gray-400 mt-1">Platform Admin</p>
          </div>
        )}

        {user?.isPlatformAdmin && (
          <div className="pt-3 border-b border-line">
            <p className="px-4 pb-1 text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Active Business
            </p>
            <BusinessSelector />
          </div>
        )}

        <nav className="flex-1 py-4 space-y-1 px-3 overflow-y-auto">
          {nav.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-brand text-white'
                    : 'text-gray-500 hover:bg-subtle hover:text-ink'
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-line space-y-2">
          {activeBusiness?.name && (
            <p className="text-xs text-gray-400 truncate">
              Viewing: {activeBusiness.name}
            </p>
          )}
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-500">{user?.username}</span>
            <div className="flex items-center gap-1">
              <button
                onClick={toggleTheme}
                className="text-gray-400 hover:text-ink transition-colors p-1 rounded-md hover:bg-subtle"
                title={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
              >
                {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
              </button>
              <button
                onClick={logout}
                className="text-gray-400 hover:text-ink transition-colors p-1 rounded-md hover:bg-subtle"
                title="Logout"
              >
                <LogOut size={16} />
              </button>
            </div>
          </div>
        </div>
      </aside>

      <main className="flex-1 overflow-auto bg-page flex flex-col">
        {isImpersonating && (
          <div className="bg-amber-400 text-amber-900 px-6 py-2.5 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Eye size={16} />
              <span>Viewing as <strong>{impersonatedBizName}</strong> — changes you make affect this client's real data</span>
            </div>
            <button
              onClick={() => { exitImpersonation(); navigate('/businesses') }}
              className="flex items-center gap-1.5 text-sm font-semibold bg-amber-900/15 hover:bg-amber-900/25 px-3 py-1 rounded-lg transition-colors"
            >
              <X size={14} />
              Exit impersonation
            </button>
          </div>
        )}
        <div className="p-8 flex-1">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
