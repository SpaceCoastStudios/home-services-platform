import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import { BusinessProvider } from './hooks/useBusinessContext'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import AppointmentsPage from './pages/AppointmentsPage'
import CustomersPage from './pages/CustomersPage'
import ServicesPage from './pages/ServicesPage'
import TechniciansPage from './pages/TechniciansPage'
import ContactsPage from './pages/ContactsPage'
import SettingsPage from './pages/SettingsPage'
import BusinessesPage from './pages/BusinessesPage'
import OnCallPage from './pages/OnCallPage'
import OnboardingPage from './pages/OnboardingPage'

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="flex items-center justify-center h-screen text-gray-500">Loading...</div>
  if (!user) return <Navigate to="/login" replace />
  return children
}

function PlatformAdminRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return null
  if (!user?.isPlatformAdmin) return <Navigate to="/" replace />
  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <ProtectedRoute>
            <BusinessProvider>
              <Layout />
            </BusinessProvider>
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="appointments" element={<AppointmentsPage />} />
        <Route path="customers" element={<CustomersPage />} />
        <Route path="services" element={<ServicesPage />} />
        <Route path="technicians" element={<TechniciansPage />} />
        <Route path="contacts" element={<ContactsPage />} />
        <Route path="oncall" element={<OnCallPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route
          path="businesses"
          element={
            <PlatformAdminRoute>
              <BusinessesPage />
            </PlatformAdminRoute>
          }
        />
        <Route
          path="onboard"
          element={
            <PlatformAdminRoute>
              <OnboardingPage />
            </PlatformAdminRoute>
          }
        />
      </Route>
    </Routes>
  )
}
