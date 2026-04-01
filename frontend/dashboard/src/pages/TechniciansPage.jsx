import { useState, useEffect } from 'react'
import { Plus, X, Pencil } from 'lucide-react'
import { getTechnicians, createTechnician, updateTechnician } from '../services/api'
import { useBusinessContext } from '../hooks/useBusinessContext'

const SKILL_OPTIONS = ['plumbing', 'electrical', 'hvac', 'cleaning', 'landscaping', 'general']

export default function TechniciansPage() {
  const { activeBusinessId } = useBusinessContext()
  const [technicians, setTechnicians] = useState([])
  const [showModal, setShowModal] = useState(false)
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState({ name: '', phone: '', email: '', skills: [] })
  const [error, setError] = useState('')

  const load = async () => {
    if (activeBusinessId == null) return
    try { setTechnicians(await getTechnicians(activeBusinessId)) } catch (err) { console.error(err) }
  }
  useEffect(() => { load() }, [activeBusinessId])

  const openCreate = () => { setEditing(null); setForm({ name: '', phone: '', email: '', skills: [] }); setShowModal(true) }
  const openEdit = (t) => { setEditing(t); setForm({ name: t.name, phone: t.phone || '', email: t.email || '', skills: t.skills || [] }); setShowModal(true) }

  const toggleSkill = (skill) => {
    setForm(f => ({
      ...f,
      skills: f.skills.includes(skill) ? f.skills.filter(s => s !== skill) : [...f.skills, skill]
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      if (editing) { await updateTechnician(editing.id, form, activeBusinessId) }
      else { await createTechnician(form, activeBusinessId) }
      setShowModal(false)
      load()
    } catch (err) { setError(err.message) }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Technicians</h1>
        <button onClick={openCreate} className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700">
          <Plus size={16} /> Add Technician
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {technicians.map((t) => (
          <div key={t.id} className={`bg-white rounded-xl shadow-sm border p-5 ${!t.is_active ? 'opacity-50' : ''}`}>
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-semibold text-gray-900">{t.name}</h3>
                {t.phone && <p className="text-sm text-gray-500 mt-0.5">{t.phone}</p>}
                {t.email && <p className="text-sm text-gray-500">{t.email}</p>}
              </div>
              <button onClick={() => openEdit(t)} className="text-gray-400 hover:text-gray-600"><Pencil size={16} /></button>
            </div>
            <div className="flex flex-wrap gap-1.5 mt-3">
              {(t.skills || []).map(s => (
                <span key={s} className="px-2 py-0.5 text-xs font-medium rounded-full bg-emerald-100 text-emerald-700">{s}</span>
              ))}
            </div>
          </div>
        ))}
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">{editing ? 'Edit Technician' : 'Add Technician'}</h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
            </div>
            {error && <div className="bg-red-50 text-red-700 px-3 py-2 rounded-lg text-sm mb-3">{error}</div>}
            <form onSubmit={handleSubmit} className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" required />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                <input type="tel" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Skills</label>
                <div className="flex flex-wrap gap-2">
                  {SKILL_OPTIONS.map(skill => (
                    <button key={skill} type="button" onClick={() => toggleSkill(skill)}
                      className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                        form.skills.includes(skill) ? 'bg-emerald-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}>{skill}</button>
                  ))}
                </div>
              </div>
              <button type="submit" className="w-full bg-blue-600 text-white py-2.5 rounded-lg font-medium hover:bg-blue-700">{editing ? 'Save Changes' : 'Add Technician'}</button>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
