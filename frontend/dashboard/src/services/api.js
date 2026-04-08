/**
 * API client — handles all backend communication with JWT auth.
 * All scoped endpoints accept an optional businessId parameter.
 * Platform admins pass it explicitly; business admins omit it
 * (the backend resolves it from their token automatically).
 */

// In development (localhost), Vite proxies /api → localhost:8000.
// In production, route directly to the API subdomain.
const isLocalhost = typeof window !== 'undefined' &&
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
const API_ROOT = isLocalhost ? '' : 'https://api.spacecoaststudios.com'
const BASE = `${API_ROOT}/api`

function getToken() {
  return localStorage.getItem('access_token')
}

async function request(path, options = {}) {
  const token = getToken()
  const headers = { 'Content-Type': 'application/json', ...options.headers }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(path.startsWith('/') ? `${API_ROOT}${path}` : `${BASE}/${path}`, {
    ...options,
    headers,
  })

  if (res.status === 401) {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }

  if (res.status === 204) return null
  return res.json()
}

/** Build a query string, omitting null/undefined values. */
function qs(params) {
  const filtered = Object.entries(params).filter(([, v]) => v != null && v !== '')
  if (!filtered.length) return ''
  return '?' + new URLSearchParams(filtered).toString()
}

const api = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: 'POST', body: JSON.stringify(body) }),
  put: (path, body) => request(path, { method: 'PUT', body: JSON.stringify(body) }),
  delete: (path) => request(path, { method: 'DELETE' }),
}

// ── Auth ────────────────────────────────────────────────────
export const login = (username, password) =>
  request('/api/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) })

// ── Businesses (platform admin only) ────────────────────────
export const getBusinesses = () => api.get('businesses')
export const getBusiness = (id) => api.get(`businesses/${id}`)
export const createBusiness = (data) => api.post('businesses', data)
export const updateBusiness = (id, data) => api.put(`businesses/${id}`, data)

// ── Customers ────────────────────────────────────────────────
export const getCustomers = (search = '', businessId = null) =>
  api.get(`customers${qs({ search: search || null, business_id: businessId })}`)
export const getCustomer = (id, businessId = null) =>
  api.get(`customers/${id}${qs({ business_id: businessId })}`)
export const createCustomer = (data, businessId = null) =>
  api.post(`customers${qs({ business_id: businessId })}`, data)
export const updateCustomer = (id, data, businessId = null) =>
  api.put(`customers/${id}${qs({ business_id: businessId })}`, data)

// ── Services ─────────────────────────────────────────────────
export const getServices = (businessId, activeOnly = false) =>
  api.get(`services${qs({ business_id: businessId, active_only: activeOnly })}`)
export const createService = (data, businessId = null) =>
  api.post(`services${qs({ business_id: businessId })}`, data)
export const updateService = (id, data, businessId = null) =>
  api.put(`services/${id}${qs({ business_id: businessId })}`, data)
export const deleteService = (id, businessId = null) =>
  api.delete(`services/${id}${qs({ business_id: businessId })}`)

// ── Technicians ───────────────────────────────────────────────
export const getTechnicians = (businessId = null, activeOnly = false) =>
  api.get(`technicians${qs({ business_id: businessId, active_only: activeOnly })}`)
export const createTechnician = (data, businessId = null) =>
  api.post(`technicians${qs({ business_id: businessId })}`, data)
export const updateTechnician = (id, data, businessId = null) =>
  api.put(`technicians/${id}${qs({ business_id: businessId })}`, data)

// ── Appointments ─────────────────────────────────────────────
export const getAppointments = (params = {}, businessId = null) => {
  const allParams = { ...params, business_id: businessId }
  return api.get(`appointments${qs(allParams)}`)
}
export const getAppointment = (id, businessId = null) =>
  api.get(`appointments/${id}${qs({ business_id: businessId })}`)
export const createAppointment = (data, businessId = null) =>
  api.post(`appointments${qs({ business_id: businessId })}`, data)
export const updateAppointment = (id, data, businessId = null) =>
  api.put(`appointments/${id}${qs({ business_id: businessId })}`, data)
export const cancelAppointment = (id, businessId = null) =>
  api.post(`appointments/${id}/cancel${qs({ business_id: businessId })}`, {})

// ── Availability ─────────────────────────────────────────────
export const getAvailability = (serviceTypeId, startDate, endDate, techId = null, businessId = null) => {
  const url = `/api/availability${qs({
    service_type_id: serviceTypeId,
    start_date: startDate,
    end_date: endDate,
    technician_id: techId,
    business_id: businessId,
  })}`
  return request(url)
}

// ── Business Hours & Settings ─────────────────────────────────
export const getBusinessHours = (businessId = null) =>
  api.get(`business-hours${qs({ business_id: businessId })}`)
export const updateBusinessHours = (hours, businessId = null) =>
  api.put(`business-hours${qs({ business_id: businessId })}`, { hours })
export const getBlockedTimes = (businessId = null) =>
  api.get(`blocked-times${qs({ business_id: businessId })}`)
export const createBlockedTime = (data, businessId = null) =>
  api.post(`blocked-times${qs({ business_id: businessId })}`, data)
export const deleteBlockedTime = (id, businessId = null) =>
  api.delete(`blocked-times/${id}${qs({ business_id: businessId })}`)
export const getSettings = (businessId = null) =>
  api.get(`settings${qs({ business_id: businessId })}`)
export const updateSetting = (key, value, businessId = null) =>
  api.put(`settings/${key}${qs({ business_id: businessId })}`, { value })

// ── Recurring Schedules ───────────────────────────────────────
export const getRecurringSchedules = (params = {}, businessId = null) =>
  api.get(`recurring${qs({ ...params, business_id: businessId })}`)
export const getRecurringSchedule = (id, businessId = null) =>
  api.get(`recurring/${id}${qs({ business_id: businessId })}`)
export const createRecurringSchedule = (data, businessId = null) =>
  api.post(`recurring${qs({ business_id: businessId })}`, data)
export const updateRecurringSchedule = (id, data, businessId = null) =>
  api.put(`recurring/${id}${qs({ business_id: businessId })}`, data)
export const deactivateRecurringSchedule = (id, businessId = null) =>
  api.delete(`recurring/${id}${qs({ business_id: businessId })}`)
export const generateRecurringAppointments = (id, businessId = null) =>
  api.post(`recurring/${id}/generate${qs({ business_id: businessId })}`, {})

// ── On-Call Routing ───────────────────────────────────────────
export const getOnCallConfig = (businessId = null) =>
  api.get(`oncall/config${qs({ business_id: businessId })}`)
export const updateOnCallConfig = (data, businessId = null) =>
  api.put(`oncall/config${qs({ business_id: businessId })}`, data)
export const addRotationEntry = (data, businessId = null) =>
  api.post(`oncall/rotation${qs({ business_id: businessId })}`, data)
export const deleteRotationEntry = (id, businessId = null) =>
  api.delete(`oncall/rotation/${id}${qs({ business_id: businessId })}`)
export const getOnCallOverride = (businessId = null) =>
  api.get(`oncall/override${qs({ business_id: businessId })}`)
export const setOnCallOverride = (data, businessId = null) =>
  api.post(`oncall/override${qs({ business_id: businessId })}`, data)
export const clearOnCallOverride = (businessId = null) =>
  api.delete(`oncall/override${qs({ business_id: businessId })}`)
export const getCurrentOnCall = (businessId = null) =>
  api.get(`oncall/current${qs({ business_id: businessId })}`)

// ── Contact Submissions ───────────────────────────────────────
export const getContactSubmissions = (status = null, businessId = null) =>
  api.get(`contact-submissions${qs({ status, business_id: businessId })}`)
export const getContactSubmission = (id, businessId = null) =>
  api.get(`contact-submissions/${id}${qs({ business_id: businessId })}`)
export const updateContactSubmission = (id, data, businessId = null) =>
  api.put(`contact-submissions/${id}${qs({ business_id: businessId })}`, data)
export const triggerAiResponse = (id, businessId = null) =>
  api.post(`contact-submissions/${id}/respond${qs({ business_id: businessId })}`)
export const sendManualResponse = (id, data, businessId = null) =>
  api.post(`contact-submissions/${id}/manual-response${qs({ business_id: businessId })}`, data)

// ── SMS Conversations ─────────────────────────────────────────
export const getSmsConversations = (status = null, businessId = null) =>
  api.get(`sms-conversations${qs({ status, business_id: businessId })}`)
export const getSmsConversation = (id, businessId = null) =>
  api.get(`sms-conversations/${id}${qs({ business_id: businessId })}`)
export const closeSmsConversation = (id, businessId = null) =>
  api.post(`sms-conversations/${id}/close${qs({ business_id: businessId })}`, {})
export const sendManualSms = (id, message, businessId = null) =>
  api.post(`sms-conversations/${id}/send${qs({ business_id: businessId })}`, { message })

// ── Notification Templates ────────────────────────────────────
export const getNotificationTemplates = (businessId = null) =>
  api.get(`notification-templates${qs({ business_id: businessId })}`)
export const saveNotificationTemplates = (templates, businessId = null) =>
  api.put(`notification-templates${qs({ business_id: businessId })}`, { templates })
export const resetNotificationTemplates = (businessId = null) =>
  api.post(`notification-templates/reset${qs({ business_id: businessId })}`, {})

export default api
