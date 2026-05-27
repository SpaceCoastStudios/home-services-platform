import { createContext, useContext, useState, useEffect } from 'react'
import { login as apiLogin, impersonateBusiness as apiImpersonate } from '../services/api'

const AuthContext = createContext(null)

function decodeToken(token) {
  try {
    return JSON.parse(atob(token.split('.')[1]))
  } catch {
    return null
  }
}

function userFromPayload(payload) {
  if (!payload) return null
  return {
    id:              payload.sub,
    username:        payload.username,
    role:            payload.role,
    businessId:      payload.business_id,
    isPlatformAdmin: payload.is_platform_admin ?? false,
  }
}

export function AuthProvider({ children }) {
  const [user, setUser]                               = useState(null)
  const [loading, setLoading]                         = useState(true)
  const [isImpersonating, setIsImpersonating]         = useState(false)
  const [impersonatedBizName, setImpersonatedBizName] = useState('')

  // Restore session on page load
  useEffect(() => {
    const token        = localStorage.getItem('access_token')
    const platformTok  = localStorage.getItem('platform_token')

    if (token) {
      const payload = decodeToken(token)
      if (payload) {
        setUser(userFromPayload(payload))
        // If a platform_token is also stashed, we're mid-impersonation
        if (platformTok && payload.impersonating) {
          setIsImpersonating(true)
          setImpersonatedBizName(payload.business_name || 'Unknown Business')
        }
      } else {
        localStorage.removeItem('access_token')
      }
    }
    setLoading(false)
  }, [])

  const login = async (username, password) => {
    const res = await apiLogin(username, password)
    localStorage.setItem('access_token', res.access_token)
    localStorage.setItem('refresh_token', res.refresh_token)
    const payload = decodeToken(res.access_token)
    setUser(userFromPayload(payload))
    setIsImpersonating(false)
    setImpersonatedBizName('')
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('platform_token')
    setUser(null)
    setIsImpersonating(false)
    setImpersonatedBizName('')
  }

  /**
   * Switch into impersonation mode for a given business.
   * Stashes the current platform admin token so exitImpersonation() can restore it.
   */
  const impersonate = async (businessId) => {
    const { access_token, business_name } = await apiImpersonate(businessId)
    // Preserve the real platform admin token
    const currentToken = localStorage.getItem('access_token')
    localStorage.setItem('platform_token', currentToken)
    // Activate impersonation token
    localStorage.setItem('access_token', access_token)
    const payload = decodeToken(access_token)
    setUser(userFromPayload(payload))
    setIsImpersonating(true)
    setImpersonatedBizName(business_name)
  }

  /**
   * Restore the original platform admin session.
   */
  const exitImpersonation = () => {
    const platformToken = localStorage.getItem('platform_token')
    if (!platformToken) return
    localStorage.setItem('access_token', platformToken)
    localStorage.removeItem('platform_token')
    const payload = decodeToken(platformToken)
    setUser(userFromPayload(payload))
    setIsImpersonating(false)
    setImpersonatedBizName('')
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        logout,
        impersonate,
        exitImpersonation,
        isImpersonating,
        impersonatedBizName,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be inside AuthProvider')
  return ctx
}
