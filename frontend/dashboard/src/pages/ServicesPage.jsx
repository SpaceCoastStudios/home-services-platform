import { useState, useEffect } from 'react'
import { Plus, X, Pencil } from 'lucide-react'
import { getServices, createService, updateService, deleteService } from '../services/api'
import { useBusinessContext } from '../hooks/useBusinessContext'

const CATEGORIES = ['plumbing', 'electrical', 'hvac', 'cleaning', 'landscaping', 'general']

export default function ServicesPage() {
  const { activeBusinessId } = useBusinessContext()
  const [services, setServices] = useState([])
  const [showModal, setShowModal] = useState(false)
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState({ name: '', category: '', description: '', duration_minutes: 60, base_price: '' })
  const [error, setError] = useState('')

  const load = async () => {
    if (activeBusinessId == null) return
    try { setServices(await getServices(activeBusinessId)) } catch (err) { console.error(err) }
  }
  useEffect(() => { load() }, [activeBusinessId])

  const openCreate = () => {
    setEditing(null)
    setForm({ name: '', category: '', description: '', duration_minutes: 60, base_price: '' })
    setShowModal(true)
  }
  const openEdit = (s) => {
    setEditing(s)
    setForm({ name: s.name, category: s.category, description: s.description || '', duration_minutes: s.duration_minutes, base_price: s.base_price || '' })
    setShowModal(true)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      const data = { ...form, duration_minutes: Number(form.duration_minutes), base_price: form.base_price ? Number(form.base_price) : null }
      if (editing) { await updateService(editing.id, data, activeBusinessId) }
      else { await createService(data, activeBusinessId) }
      setShowModal(false)
      load()
    } catch (err) { setError(err.message) }
  }

  const handleDelete = async (id) => {
    if (!confirm('Deactivate this service?')) return
    await deleteService(id, activeBusinessId)
    load()
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Services</h1>
        <button onClick={openCreate} className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700">
          <Plus size={16} /> Add Service
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {services.map((s) => (
          <div key={s.id} className={`bg-white rounded-xl shadow-sm border p-5 ${!s.is_active ? 'opacity-50' : ''}`}>
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-semibold text-gray-900">{s.name}</h3>
                <span className="inline-block mt-1 px-2 py-0.5 text-xs font-medium rounded-full bg-blue-100 text-blue-700">{s.category}</span>
              </div>
              <button onClick={() => openEdit(s)} className="text-gray-400 hover:text-gray-600"><Pencil size={16} /></button>
            </div>
            {s.description && <p className="text-sm text-gray-500 mt-2">{s.description}</p>}
            <div className="flex items-center gap-4 mt-3 text-sm text-gray-600">
              <span>{s.duration_minutes} min</span>
              {s.base_price && <span>${Number(s.base_price).toFixed(2)}</span>}
            </div>
            {!s.is_active && <p className="text-xs text-red-500 mt-2">Inactive</p>}
          </div>
        ))}
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">{editing ? 'Edit Service' : 'Add Service'}</h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
            </div>
            {error && <div className="bg-red-50 text-red-700 px-3 py-2 rounded-lg text-sm mb-3">{error}</div>}
            <form onSubmit={handleSubmit} className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" required />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" required>
                  <option value="">Select...</option>
                  {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" rows={2} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Duration (min)</label>
                  <input type="number" value={form.duration_minutes} onChange={(e) => setForm({ ...form, duration_minutes: e.target.value })} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" required />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Base Price ($)</label>
                  <input type="number" step="0.01" value={form.base_price} onChange={(e) => setForm({ ...form, base_price: e.target.value })} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
                </div>
              </div>
              <button type="submit" className="w-full bg-blue-600 text-white py-2.5 rounded-lg font-medium hover:bg-blue-700">{editing ? 'Save Changes' : 'Add Service'}</button>
              {editing && editing.is_active && (
                <button type="button" onClick={() => { handleDelete(editing.id); setShowModal(false) }} className="w-full text-red-600 text-sm py-2 hover:underline">Deactivate Service</button>
              )}
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
