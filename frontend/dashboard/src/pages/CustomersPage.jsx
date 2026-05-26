import { useState, useEffect } from 'react'
import { Plus, Search, X, Pencil } from 'lucide-react'
import { getCustomers, createCustomer, updateCustomer } from '../services/api'
import { useBusinessContext } from '../hooks/useBusinessContext'

const EMPTY_FORM = { first_name: '', last_name: '', phone: '', email: '', address: '', city: '', state: '', zip_code: '' }

function CustomerForm({ title, form, setForm, onSubmit, onClose, error, submitLabel }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 max-h-[90vh] overflow-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">{title}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>
        {error && <div className="bg-red-50 text-red-700 px-3 py-2 rounded-lg text-sm mb-3">{error}</div>}
        <form onSubmit={onSubmit} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
              <input value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
              <input value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" required />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
            <input type="tel" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Street Address</label>
            <input value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" placeholder="123 Main St" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">City</label>
              <input value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
              <input value={form.state} onChange={(e) => setForm({ ...form, state: e.target.value })} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" placeholder="FL" maxLength={2} />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Zip Code</label>
            <input value={form.zip_code} onChange={(e) => setForm({ ...form, zip_code: e.target.value })} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>
          <button type="submit" className="w-full bg-blue-600 text-white py-2.5 rounded-lg font-medium hover:bg-blue-700">{submitLabel}</button>
        </form>
      </div>
    </div>
  )
}

export default function CustomersPage() {
  const { activeBusinessId } = useBusinessContext()
  const [customers, setCustomers] = useState([])
  const [search, setSearch] = useState('')

  const [showCreate, setShowCreate] = useState(false)
  const [createForm, setCreateForm] = useState({ ...EMPTY_FORM })
  const [createError, setCreateError] = useState('')

  const [editCustomer, setEditCustomer] = useState(null) // customer object being edited
  const [editForm, setEditForm] = useState({ ...EMPTY_FORM })
  const [editError, setEditError] = useState('')

  const load = async () => {
    if (activeBusinessId == null) return
    try { setCustomers(await getCustomers(search, activeBusinessId)) } catch (err) { console.error(err) }
  }

  useEffect(() => { load() }, [search, activeBusinessId])

  const handleCreate = async (e) => {
    e.preventDefault()
    setCreateError('')
    try {
      await createCustomer(createForm, activeBusinessId)
      setShowCreate(false)
      setCreateForm({ ...EMPTY_FORM })
      load()
    } catch (err) { setCreateError(err.message) }
  }

  const openEdit = (customer) => {
    setEditCustomer(customer)
    setEditForm({
      first_name: customer.first_name || '',
      last_name:  customer.last_name  || '',
      phone:      customer.phone      || '',
      email:      customer.email      || '',
      address:    customer.address    || '',
      city:       customer.city       || '',
      state:      customer.state      || '',
      zip_code:   customer.zip_code   || '',
    })
    setEditError('')
  }

  const handleEdit = async (e) => {
    e.preventDefault()
    setEditError('')
    try {
      await updateCustomer(editCustomer.id, editForm, activeBusinessId)
      setEditCustomer(null)
      load()
    } catch (err) { setEditError(err.message) }
  }

  if (activeBusinessId == null) {
    return <div className="flex items-center justify-center h-64 text-gray-400">Select a business to view customers.</div>
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Customers</h1>
        <button onClick={() => { setShowCreate(true); setCreateError('') }} className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700">
          <Plus size={16} /> Add Customer
        </button>
      </div>

      <div className="relative mb-4">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          placeholder="Search by name, phone, or email..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
        />
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {customers.length === 0 ? (
          <div className="p-6 text-center text-gray-400">No customers found</div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <th className="px-6 py-3">Name</th>
                <th className="px-6 py-3">Phone</th>
                <th className="px-6 py-3">Email</th>
                <th className="px-6 py-3">Address</th>
                <th className="px-6 py-3">Created</th>
                <th className="px-6 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {customers.map((c) => (
                <tr key={c.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium">{c.first_name} {c.last_name}</td>
                  <td className="px-6 py-4 text-sm">{c.phone}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{c.email || '—'}</td>
                  <td className="px-6 py-4 text-sm text-gray-500 truncate max-w-xs">
                    {[c.address, c.city, c.state, c.zip_code].filter(Boolean).join(', ') || '—'}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">{new Date(c.created_at).toLocaleDateString()}</td>
                  <td className="px-6 py-4">
                    <button onClick={() => openEdit(c)} className="text-gray-400 hover:text-blue-600 transition-colors" title="Edit customer">
                      <Pencil size={15} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showCreate && (
        <CustomerForm
          title="Add Customer"
          form={createForm}
          setForm={setCreateForm}
          onSubmit={handleCreate}
          onClose={() => setShowCreate(false)}
          error={createError}
          submitLabel="Add Customer"
        />
      )}

      {editCustomer && (
        <CustomerForm
          title={`Edit — ${editCustomer.first_name} ${editCustomer.last_name}`}
          form={editForm}
          setForm={setEditForm}
          onSubmit={handleEdit}
          onClose={() => setEditCustomer(null)}
          error={editError}
          submitLabel="Save Changes"
        />
      )}
    </div>
  )
}
