/**
 * BusinessContext — tracks which tenant is currently "active" in the dashboard.
 *
 * For platform admins: they can switch between any tenant via the sidebar selector.
 *   - activeBusiness = the business object they've selected, or null if viewing platform overview
 *   - activeBusinessId = shortcut number (or null)
 *
 * For business admins: always locked to their own business_id from the token.
 *   - activeBusinessId is set automatically on login, cannot be changed
 */

import { createContext, useContext, useState, useEffect } from 'react'
import { useAuth } from './useAuth'
import { getBusinesses } from '../services/api'

const BusinessContext = createContext(null)

export function BusinessProvider({ children }) {
  const { user } = useAuth()

  // The currently selected business object { id, name, slug, plan, ... }
  const [activeBusiness, setActiveBusiness] = useState(null)
  // All businesses (only populated for platform admins)
  const [businesses, setBusinesses] = useState([])
  const [loadingBusinesses, setLoadingBusinesses] = useState(false)

  // When the user changes (login/logout), reset context
  useEffect(() => {
    if (!user) {
      setActiveBusiness(null)
      setBusinesses([])
      return
    }

    if (user.isPlatformAdmin) {
      // Load all tenant businesses for the selector
      setLoadingBusinesses(true)
      getBusinesses()
        .then((list) => {
          setBusinesses(list)
          // Auto-select the first business so pages aren't empty on first load
          if (list.length > 0 && !activeBusiness) {
            setActiveBusiness(list[0])
          }
        })
        .catch(console.error)
        .finally(() => setLoadingBusinesses(false))
    } else {
      // Business admin — we don't have the full business object from the token,
      // but we have the ID. Pages will pass it as a query param automatically.
      setActiveBusiness({ id: user.businessId })
    }
  }, [user?.id])

  // The business_id to pass in API calls — null means "not selected yet"
  const activeBusinessId = activeBusiness?.id ?? null

  const selectBusiness = (business) => {
    setActiveBusiness(business)
  }

  const refreshBusinesses = () => {
    if (!user?.isPlatformAdmin) return
    getBusinesses().then(setBusinesses).catch(console.error)
  }

  return (
    <BusinessContext.Provider
      value={{
        activeBusiness,
        activeBusinessId,
        businesses,
        loadingBusinesses,
        selectBusiness,
        refreshBusinesses,
      }}
    >
      {children}
    </BusinessContext.Provider>
  )
}

export function useBusinessContext() {
  const ctx = useContext(BusinessContext)
  if (!ctx) throw new Error('useBusinessContext must be inside BusinessProvider')
  return ctx
}
