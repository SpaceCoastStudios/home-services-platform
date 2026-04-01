import { createContext, useContext, useState, useEffect } from 'react'
import { login as apiLogin } from '../services/api'

const AuthContext = createContext(null)

function decodeToken(token) {
  try {
    return JSON.parse(atob(token.split('.')[1]))
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      const payload = decodeToken(token)
      if (payload) {
        setUser({
          id: payload.sub,
          username: payload.username,
          role: payload.role,
          businessId: payload.business_id,         // null for platform admins
          isPlatformAdmin: payload.is_platform_admin ?? false,
        })
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
    setUser({
      id: payload.sub,
      username: payload.username,
      role: payload.role,
      businessId: payload.business_id,
      isPlatformAdmin: payload.is_platform_admin ?? false,
    })
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be inside AuthProvider')
  return ctx
}
