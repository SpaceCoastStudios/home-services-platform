import { useState, useEffect } from 'react'
import { getBusinesses, createBusiness, updateBusiness } from '../services/api'
import { useBusinessContext } from '../hooks/useBusinessContext'
import { Building2, Plus, X, Check, Users, Calendar, Globe, Wrench } from 'lucide-react'

const INDUSTRIES = ['hvac', 'plumbing', 'electrical', 'landscaping', 'cleaning', 'roofing', 'general']
const PLANS = ['full', 'mini']

function StatBadge({ label, value, color = 'gray' }) {
  const colors = {
    blue: 'bg-blue-50 text-blue-700',
    green: 'bg-green-50 text-green-700',
    gray: 'bg-gray-100 text-gray-600',
    purple: 'bg-purple-50 text-purple-700',
  }
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${colors[color]}`}>
      {value} {label}
    </span>
  )
}

function BusinessModal({ business, onClose, onSaved }) {
  const isEdit = !!business?.id
  const [form, setForm] = useState({
    name: business?.name ?? '',
    slug: business?.slug ?? '',
    industry: business?.industry ?? 'hvac',
    plan: business?.plan ?? 'full',
    phone: business?.phone ?? '',
    email: business?.email ?? '',
    address: business?.address ?? '',
    website: business?.website ?? '',
    brand_color: business?.brand_color ?? '#2563eb',
    ai_agent_name: business?.ai_agent_name ?? '',
    ai_system_prompt: business?.ai_system_prompt ?? '',
    from_email: business?.from_email ?? '',
    is_demo: business?.is_demo ?? false,
    is_active: business?.is_active ?? true,
    // New business only
    admin_username: '',
    admin_password: '',
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const set = (field) => (e) => {
    const val = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    setForm((f) => ({ ...f, [field]: val }))
    // Auto-generate slug from name on create
    if (field === 'name' && !isEdit) {
      setForm((f) => ({
        ...f,
        name: e.target.value,
        slug: e.target.value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''),
      }))
    }
  }

  const save = async () => {
    if (!form.name || !form.slug) { setError('Name and slug are required'); return }
    setSaving(true)
    setError('')
    try {
      if (isEdit) {
        await updateBusiness(business.id, form)
      } else {
        await createBusiness(form)
      }
      onSaved()
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-lg font-semibold">
            {isEdit ? `Edit: ${business.name}` : 'Add New Business'}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X size={20} />
          </button>
        </div>

        <div className="p-6 space-y-5">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-2 text-sm">
              {error}
            </div>
          )}

          {/* Basic Info */}
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Business Name *</label>
              <input value={form.name} onChange={set('name')} className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="Peak HVAC Services" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Slug * <span className="text-gray-400 font-normal">(URL identifier)</span></label>
              <input value={form.slug} onChange={set('slug')} disabled={isEdit} className="w-full border rounded-lg px-3 py-2 text-sm disabled:bg-gray-50 disabled:text-gray-400" placeholder="peak-hvac" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Industry</label>
              <select value={form.industry} onChange={set('industry')} className="w-full border rounded-lg px-3 py-2 text-sm">
                {INDUSTRIES.map((i) => <option key={i} value={i}>{i.charAt(0).toUpperCase() + i.slice(1)}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Plan</label>
              <select value={form.plan} onChange={set('plan')} className="w-full border rounded-lg px-3 py-2 text-sm">
                {PLANS.map((p) => <option key={p} value={p}>{p === 'full' ? 'Full (hosted site)' : 'Mini (API only)'}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Brand Color</label>
              <div className="flex gap-2 items-center">
                <input type="color" value={form.brand_color} onChange={set('brand_color')} className="h-9 w-12 border rounded cursor-pointer" />
                <input value={form.brand_color} onChange={set('brand_color')} className="flex-1 border rounded-lg px-3 py-2 text-sm font-mono" placeholder="#2563eb" />
              </div>
            </div>
          </div>

          {/* Contact */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
              <input value={form.phone} onChange={set('phone')} className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="(321) 555-0100" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input value={form.email} onChange={set('email')} className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="info@peakhvac.com" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Website</label>
              <input value={form.website} onChange={set('website')} className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="https://peakhvac.com" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
              <input value={form.address} onChange={set('address')} className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="123 Main St, City, FL" />
            </div>
          </div>

          {/* AI Agent */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-700">AI Agent Configuration</h3>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Agent Name</label>
              <input value={form.ai_agent_name} onChange={set('ai_agent_name')} className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="e.g. Peak Assistant" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">System Prompt <span className="text-gray-400 font-normal">(custom AI instructions)</span></label>
              <textarea
                value={form.ai_system_prompt}
                onChange={set('ai_system_prompt')}
                rows={3}
                className="w-full border rounded-lg px-3 py-2 text-sm resize-none"
                placeholder="You are a helpful assistant for Peak HVAC. You help customers book HVAC service appointments..."
              />
            </div>
          </div>

          {/* From Email */}
          <div className="space-y-3 border-t pt-4">
            <h3 className="text-sm font-semibold text-gray-700">Email Sending</h3>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                From Email <span className="text-gray-400 font-normal">(customer-facing sender address)</span>
              </label>
              <input
                value={form.from_email}
                onChange={set('from_email')}
                className="w-full border rounded-lg px-3 py-2 text-sm"
                placeholder="info@peakhvac.com"
              />
              <p className="text-xs text-gray-400 mt-1">
                Must be a verified sender on the business's domain in SendGrid. Leave blank to use the platform default.
              </p>
            </div>
          </div>

          {/* Status flags */}
          <div className="flex gap-6">
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input type="checkbox" checked={form.is_demo} onChange={set('is_demo')} className="rounded" />
              <span className="text-gray-700">Demo business</span>
            </label>
            {isEdit && (
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input type="checkbox" checked={form.is_active} onChange={set('is_active')} className="rounded" />
                <span className="text-gray-700">Active</span>
              </label>
            )}
          </div>

          {/* Admin user — new businesses only */}
          {!isEdit && (
            <div className="space-y-3 border-t pt-4">
              <h3 className="text-sm font-semibold text-gray-700">Create Admin User <span className="text-gray-400 font-normal">(optional)</span></h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
                  <input value={form.admin_username} onChange={set('admin_username')} className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="peakhvac-admin" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                  <input type="password" value={form.admin_password} onChange={set('admin_password')} className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="••••••••" />
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="flex justify-end gap-3 px-6 py-4 border-t bg-gray-50 rounded-b-2xl">
          <button onClick={onClose} className="px-4 py-2 text-sm border rounded-lg hover:bg-gray-100">Cancel</button>
          <button
            onClick={save}
            disabled={saving}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
          >
            {saving ? 'Saving…' : <><Check size={15} /> {isEdit ? 'Save Changes' : 'Create Business'}</>}
          </button>
        </div>
      </div>
    </div>
  )
}

function PlanBadge({ plan }) {
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
      plan === 'full' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'
    }`}>
      {plan === 'full' ? 'Full' : 'Mini'}
    </span>
  )
}

export default function BusinessesPage() {
  const [businesses, setBusinesses] = useState([])
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState(null) // null | 'new' | business object
  const { selectBusiness } = useBusinessContext()

  const load = () => {
    setLoading(true)
    getBusinesses()
      .then(setBusinesses)
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleSaved = () => {
    setModal(null)
    load()
  }

  const activeCount = businesses.filter((b) => b.is_active).length

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Businesses</h1>
          <p className="text-gray-500 mt-1">
            {activeCount} active tenant{activeCount !== 1 ? 's' : ''} on the platform
          </p>
        </div>
        <button
          onClick={() => setModal('new')}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
        >
          <Plus size={16} /> Add Business
        </button>
      </div>

      {/* Business grid */}
      {loading ? (
        <div className="text-center py-20 text-gray-400">Loading businesses…</div>
      ) : businesses.length === 0 ? (
        <div className="text-center py-20">
          <Building2 size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500 font-medium">No businesses yet</p>
          <p className="text-gray-400 text-sm mt-1">Add your first client to get started.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {businesses.map((b) => (
            <div
              key={b.id}
              className={`bg-white rounded-2xl border shadow-sm hover:shadow-md transition-shadow flex flex-col ${
                !b.is_active ? 'opacity-60' : ''
              }`}
            >
              {/* Color strip */}
              <div
                className="h-1.5 rounded-t-2xl"
                style={{ backgroundColor: b.brand_color || '#2563eb' }}
              />

              <div className="p-5 flex-1 flex flex-col">
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="min-w-0">
                    <h2 className="font-semibold text-gray-900 truncate">{b.name}</h2>
                    <p className="text-xs text-gray-400 mt-0.5">/{b.slug}</p>
                  </div>
                  <div className="flex gap-1.5 shrink-0">
                    <PlanBadge plan={b.plan} />
                    {b.is_demo && (
                      <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">Demo</span>
                    )}
                    {!b.is_active && (
                      <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-red-100 text-red-600">Inactive</span>
                    )}
                  </div>
                </div>

                {/* Details */}
                <div className="space-y-1 text-sm text-gray-500 mb-4">
                  {b.industry && (
                    <div className="flex items-center gap-1.5">
                      <Wrench size={13} />
                      <span className="capitalize">{b.industry}</span>
                    </div>
                  )}
                  {b.website && (
                    <div className="flex items-center gap-1.5">
                      <Globe size={13} />
                      <a href={b.website} target="_blank" rel="noreferrer" className="hover:text-blue-600 truncate">
                        {b.website.replace(/^https?:\/\//, '')}
                      </a>
                    </div>
                  )}
                  {b.ai_agent_name && (
                    <div className="text-xs text-purple-600 bg-purple-50 rounded px-2 py-0.5 inline-block mt-1">
                      AI Agent: {b.ai_agent_name}
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex gap-2 mt-auto pt-3 border-t">
                  <button
                    onClick={() => { selectBusiness(b) }}
                    className="flex-1 text-center text-sm py-1.5 rounded-lg border border-blue-200 text-blue-600 hover:bg-blue-50 transition-colors font-medium"
                  >
                    View Dashboard
                  </button>
                  <button
                    onClick={() => setModal(b)}
                    className="flex-1 text-center text-sm py-1.5 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
                  >
                    Edit
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {modal && (
        <BusinessModal
          business={modal === 'new' ? null : modal}
          onClose={() => setModal(null)}
          onSaved={handleSaved}
        />
      )}
    </div>
  )
}
