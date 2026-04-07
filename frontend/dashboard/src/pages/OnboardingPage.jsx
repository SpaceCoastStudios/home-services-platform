import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  createBusiness, createService, createTechnician,
  updateBusinessHours,
} from '../services/api'
import { useBusinessContext } from '../hooks/useBusinessContext'
import {
  Building2, Bot, Wrench, Users, Clock, CheckCircle2,
  Plus, Trash2, ChevronRight, ChevronLeft, ArrowRight,
} from 'lucide-react'

// ─── Constants ───────────────────────────────────────────────────────────────

const INDUSTRIES = [
  { value: 'hvac',        label: 'HVAC & Air Conditioning' },
  { value: 'plumbing',    label: 'Plumbing' },
  { value: 'electrical',  label: 'Electrical' },
  { value: 'landscaping', label: 'Lawn & Landscaping' },
  { value: 'roofing',     label: 'Roofing' },
  { value: 'cleaning',    label: 'Cleaning Services' },
  { value: 'general',     label: 'General Home Services' },
]

const PLANS = [
  { value: 'full', label: 'Professional', price: '$2,497 setup + $349/mo',
    desc: 'Full-featured platform with unlimited technicians, SMS reminders, AI persona, and monthly check-in.' },
  { value: 'mini', label: 'Starter', price: '$1,497 setup + $199/mo',
    desc: 'Core platform — up to 5 technicians, 3 service types, email confirmations, admin dashboard.' },
]

const SKILL_OPTIONS = ['plumbing', 'electrical', 'hvac', 'cleaning', 'landscaping', 'general']

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

const SERVICE_CATEGORIES = [
  'hvac', 'plumbing', 'electrical', 'landscaping', 'cleaning', 'roofing', 'general',
]

const STEPS = [
  { num: 1, label: 'Business', icon: Building2 },
  { num: 2, label: 'AI & Brand', icon: Bot },
  { num: 3, label: 'Services', icon: Wrench },
  { num: 4, label: 'Team', icon: Users },
  { num: 5, label: 'Hours & Login', icon: Clock },
]

// ─── Helpers ─────────────────────────────────────────────────────────────────

function slugify(str) {
  return str.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
}

function defaultPrompt(name, industry, agentName) {
  const ind = INDUSTRIES.find((i) => i.value === industry)?.label ?? industry
  return `You are ${agentName || 'our virtual assistant'} for ${name || 'our business'}, a ${ind} service company based in Florida. Your role is to help customers schedule appointments, answer questions about our services, and provide friendly, professional support at any hour.\n\nWhen a customer wants to book a service, ask for their preferred date and time and let them know a team member will confirm the appointment. If you cannot answer a specific question, reassure them that a technician will follow up shortly.`
}

function defaultHours() {
  // 0 = Monday … 4 = Friday open, 5 = Saturday, 6 = Sunday closed
  return DAYS.map((_, i) => ({
    day_of_week: i,
    open_time: '08:00',
    close_time: '17:00',
    is_active: i < 5,
  }))
}

// ─── Shared UI ───────────────────────────────────────────────────────────────

function Label({ children, optional }) {
  return (
    <label className="block text-sm font-medium text-gray-700 mb-1">
      {children}
      {optional && <span className="ml-1 font-normal text-gray-400">(optional)</span>}
    </label>
  )
}

function Input({ ...props }) {
  return (
    <input
      className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      {...props}
    />
  )
}

function Select({ children, ...props }) {
  return (
    <select
      className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
      {...props}
    >
      {children}
    </select>
  )
}

function FieldError({ msg }) {
  if (!msg) return null
  return <p className="text-xs text-red-600 mt-1">{msg}</p>
}

// ─── Progress Bar ────────────────────────────────────────────────────────────

function ProgressBar({ currentStep }) {
  return (
    <div className="flex items-center gap-0 mb-10">
      {STEPS.map((s, idx) => {
        const done = currentStep > s.num
        const active = currentStep === s.num
        const Icon = s.icon
        return (
          <div key={s.num} className="flex items-center flex-1 last:flex-none">
            <div className="flex flex-col items-center gap-1.5">
              <div className={`w-9 h-9 rounded-full flex items-center justify-center transition-colors ${
                done    ? 'bg-green-500 text-white' :
                active  ? 'bg-blue-600 text-white' :
                          'bg-gray-100 text-gray-400'
              }`}>
                {done ? <CheckCircle2 size={18} /> : <Icon size={16} />}
              </div>
              <span className={`text-xs font-medium whitespace-nowrap ${
                active ? 'text-blue-600' : done ? 'text-green-600' : 'text-gray-400'
              }`}>{s.label}</span>
            </div>
            {idx < STEPS.length - 1 && (
              <div className={`flex-1 h-0.5 mx-2 mb-4 transition-colors ${
                currentStep > s.num ? 'bg-green-400' : 'bg-gray-200'
              }`} />
            )}
          </div>
        )
      })}
    </div>
  )
}

// ─── Step 1: Business Info ────────────────────────────────────────────────────

function StepBusinessInfo({ data, onChange, onNext }) {
  const [errors, setErrors] = useState({})

  const set = (field) => (e) => {
    const val = e.target.value
    onChange((d) => {
      const next = { ...d, [field]: val }
      if (field === 'name') next.slug = slugify(val)
      return next
    })
  }

  const validate = () => {
    const e = {}
    if (!data.name.trim()) e.name = 'Business name is required'
    if (!data.slug.trim()) e.slug = 'Slug is required'
    if (data.slug && !/^[a-z0-9-]+$/.test(data.slug)) e.slug = 'Only lowercase letters, numbers, and hyphens'
    if (!data.industry) e.industry = 'Select an industry'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900">Business details</h2>
        <p className="text-gray-500 text-sm mt-1">Start with the basics — you can update everything later.</p>
      </div>

      {/* Plan selection */}
      <div>
        <Label>Plan</Label>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {PLANS.map((p) => (
            <button
              key={p.value}
              type="button"
              onClick={() => onChange((d) => ({ ...d, plan: p.value }))}
              className={`text-left p-4 border-2 rounded-xl transition-colors ${
                data.plan === p.value
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="font-semibold text-sm text-gray-900">{p.label}</div>
              <div className="text-xs text-gray-500 mt-0.5">{p.price}</div>
              <div className="text-xs text-gray-400 mt-1">{p.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Name & Slug */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="sm:col-span-2">
          <Label>Business name</Label>
          <Input
            value={data.name}
            onChange={set('name')}
            placeholder="Peak HVAC Services"
          />
          <FieldError msg={errors.name} />
        </div>
        <div>
          <Label>URL slug</Label>
          <div className="flex items-center border border-gray-200 rounded-lg overflow-hidden focus-within:ring-2 focus-within:ring-blue-500">
            <span className="px-3 py-2 text-sm text-gray-400 bg-gray-50 border-r border-gray-200 whitespace-nowrap">id/</span>
            <input
              value={data.slug}
              onChange={set('slug')}
              placeholder="peak-hvac"
              className="flex-1 px-3 py-2 text-sm focus:outline-none"
            />
          </div>
          <FieldError msg={errors.slug} />
        </div>
        <div>
          <Label>Industry</Label>
          <Select value={data.industry} onChange={set('industry')}>
            <option value="">Select industry…</option>
            {INDUSTRIES.map((i) => (
              <option key={i.value} value={i.value}>{i.label}</option>
            ))}
          </Select>
          <FieldError msg={errors.industry} />
        </div>
      </div>

      {/* Contact */}
      <div>
        <p className="text-sm font-semibold text-gray-700 mb-3">Contact information</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <Label optional>Phone</Label>
            <Input value={data.phone} onChange={set('phone')} placeholder="(321) 555-0100" />
          </div>
          <div>
            <Label optional>Email</Label>
            <Input type="email" value={data.email} onChange={set('email')} placeholder="info@peakhvac.com" />
          </div>
          <div>
            <Label optional>Website</Label>
            <Input value={data.website} onChange={set('website')} placeholder="https://peakhvac.com" />
          </div>
          <div>
            <Label optional>Address</Label>
            <Input value={data.address} onChange={set('address')} placeholder="123 Main St, Merritt Island, FL" />
          </div>
        </div>
      </div>

      <div className="flex justify-end pt-2">
        <button
          onClick={() => validate() && onNext()}
          className="flex items-center gap-2 bg-blue-600 text-white px-6 py-2.5 rounded-xl font-medium hover:bg-blue-700 transition-colors"
        >
          Next <ChevronRight size={16} />
        </button>
      </div>
    </div>
  )
}

// ─── Step 2: AI & Branding ────────────────────────────────────────────────────

function StepAI({ data, onChange, onNext, onBack }) {
  const set = (field) => (e) => {
    const val = e.target.value
    onChange((d) => ({ ...d, [field]: val }))
  }

  const fillPrompt = () => {
    onChange((d) => ({
      ...d,
      ai_system_prompt: defaultPrompt(d.name, d.industry, d.ai_agent_name),
    }))
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900">AI assistant & branding</h2>
        <p className="text-gray-500 text-sm mt-1">Customize how the AI responds to customers and how the platform looks.</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <Label optional>AI agent name</Label>
          <Input
            value={data.ai_agent_name}
            onChange={set('ai_agent_name')}
            placeholder="e.g. Max, Sam, Aria"
          />
          <p className="text-xs text-gray-400 mt-1">The name customers see when the AI responds.</p>
        </div>
        <div>
          <Label optional>Brand color</Label>
          <div className="flex gap-2 items-center">
            <input
              type="color"
              value={data.brand_color}
              onChange={set('brand_color')}
              className="h-[38px] w-12 border rounded-lg cursor-pointer p-0.5"
            />
            <Input
              value={data.brand_color}
              onChange={set('brand_color')}
              placeholder="#f97316"
              className="font-mono"
            />
          </div>
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-1">
          <Label optional>AI system prompt</Label>
          <button
            type="button"
            onClick={fillPrompt}
            className="text-xs text-blue-600 hover:underline"
          >
            Generate from business info
          </button>
        </div>
        <textarea
          value={data.ai_system_prompt}
          onChange={set('ai_system_prompt')}
          rows={5}
          placeholder="Click 'Generate from business info' to create a starting prompt, or write your own…"
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="border-t pt-4 space-y-4">
        <p className="text-sm font-semibold text-gray-700">Notifications</p>
        <div>
          <Label optional>From email address</Label>
          <Input
            value={data.from_email}
            onChange={set('from_email')}
            type="email"
            placeholder="info@peakhvac.com"
          />
          <p className="text-xs text-gray-400 mt-1">
            Customer-facing sender for confirmation emails. Must be a verified sender in SendGrid. Leave blank to use the platform default.
          </p>
        </div>
        <div>
          <Label optional>Twilio phone number</Label>
          <Input
            value={data.twilio_phone_number}
            onChange={set('twilio_phone_number')}
            placeholder="+13215550100"
          />
          <p className="text-xs text-gray-400 mt-1">
            Dedicated number for SMS reminders. Leave blank to use the platform default.
          </p>
        </div>
      </div>

      <div className="flex justify-between pt-2">
        <button onClick={onBack} className="flex items-center gap-2 text-gray-500 hover:text-gray-700 px-4 py-2 rounded-xl border border-gray-200 hover:border-gray-300 transition-colors">
          <ChevronLeft size={16} /> Back
        </button>
        <button onClick={onNext} className="flex items-center gap-2 bg-blue-600 text-white px-6 py-2.5 rounded-xl font-medium hover:bg-blue-700 transition-colors">
          Next <ChevronRight size={16} />
        </button>
      </div>
    </div>
  )
}

// ─── Step 3: Services ─────────────────────────────────────────────────────────

function StepServices({ services, onChange, onNext, onBack, plan }) {
  const [errors, setErrors] = useState([])
  const maxServices = plan === 'mini' ? 3 : Infinity
  const atLimit = services.length >= maxServices

  const addService = () => {
    onChange((s) => [...s, { name: '', category: '', duration_minutes: 60, base_price: '' }])
  }

  const removeService = (idx) => {
    onChange((s) => s.filter((_, i) => i !== idx))
  }

  const setField = (idx, field) => (e) => {
    onChange((s) => s.map((svc, i) => i === idx ? { ...svc, [field]: e.target.value } : svc))
  }

  const validate = () => {
    const errs = services.map((s) => {
      const e = {}
      if (!s.name.trim()) e.name = 'Required'
      if (!s.category) e.category = 'Required'
      if (!s.duration_minutes || isNaN(Number(s.duration_minutes))) e.duration_minutes = 'Required'
      return e
    })
    setErrors(errs)
    return errs.every((e) => Object.keys(e).length === 0)
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900">Services offered</h2>
        <p className="text-gray-500 text-sm mt-1">
          Add the service types customers can book.
          {plan === 'mini' && <span className="text-amber-600 ml-1">Starter plan: up to 3 services.</span>}
        </p>
      </div>

      <div className="space-y-4">
        {services.map((svc, idx) => (
          <div key={idx} className="border border-gray-200 rounded-xl p-4 bg-gray-50 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-gray-700">Service {idx + 1}</span>
              {services.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeService(idx)}
                  className="text-red-400 hover:text-red-600"
                >
                  <Trash2 size={14} />
                </button>
              )}
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="sm:col-span-2">
                <Label>Service name</Label>
                <Input value={svc.name} onChange={setField(idx, 'name')} placeholder="AC Tune-Up" />
                <FieldError msg={errors[idx]?.name} />
              </div>
              <div>
                <Label>Category</Label>
                <Select value={svc.category} onChange={setField(idx, 'category')}>
                  <option value="">Select…</option>
                  {SERVICE_CATEGORIES.map((c) => (
                    <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
                  ))}
                </Select>
                <FieldError msg={errors[idx]?.category} />
              </div>
              <div>
                <Label>Duration (minutes)</Label>
                <Input
                  type="number"
                  value={svc.duration_minutes}
                  onChange={setField(idx, 'duration_minutes')}
                  placeholder="60"
                  min="15"
                  step="15"
                />
                <FieldError msg={errors[idx]?.duration_minutes} />
              </div>
              <div>
                <Label optional>Base price ($)</Label>
                <Input
                  type="number"
                  value={svc.base_price}
                  onChange={setField(idx, 'base_price')}
                  placeholder="149.00"
                  min="0"
                  step="0.01"
                />
              </div>
              <div>
                <Label optional>Description</Label>
                <Input value={svc.description || ''} onChange={setField(idx, 'description')} placeholder="Brief service description" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {!atLimit && (
        <button
          type="button"
          onClick={addService}
          className="flex items-center gap-2 text-blue-600 hover:text-blue-700 text-sm font-medium border border-blue-200 hover:border-blue-400 px-4 py-2 rounded-lg transition-colors"
        >
          <Plus size={14} /> Add another service
        </button>
      )}
      {atLimit && (
        <p className="text-xs text-amber-600">Service limit reached for Starter plan. Upgrade to Professional for unlimited services.</p>
      )}

      <div className="flex justify-between pt-2">
        <button onClick={onBack} className="flex items-center gap-2 text-gray-500 hover:text-gray-700 px-4 py-2 rounded-xl border border-gray-200 hover:border-gray-300 transition-colors">
          <ChevronLeft size={16} /> Back
        </button>
        <button
          onClick={() => validate() && onNext()}
          className="flex items-center gap-2 bg-blue-600 text-white px-6 py-2.5 rounded-xl font-medium hover:bg-blue-700 transition-colors"
        >
          Next <ChevronRight size={16} />
        </button>
      </div>
    </div>
  )
}

// ─── Step 4: Team ─────────────────────────────────────────────────────────────

function StepTeam({ technicians, onChange, onNext, onBack, plan }) {
  const [errors, setErrors] = useState([])
  const maxTechs = plan === 'mini' ? 5 : Infinity
  const atLimit = technicians.length >= maxTechs

  const addTech = () => {
    onChange((t) => [...t, { name: '', phone: '', email: '', skills: [] }])
  }

  const removeTech = (idx) => {
    onChange((t) => t.filter((_, i) => i !== idx))
  }

  const setField = (idx, field) => (e) => {
    onChange((t) => t.map((tech, i) => i === idx ? { ...tech, [field]: e.target.value } : tech))
  }

  const toggleSkill = (idx, skill) => {
    onChange((t) => t.map((tech, i) => {
      if (i !== idx) return tech
      const skills = tech.skills.includes(skill)
        ? tech.skills.filter((s) => s !== skill)
        : [...tech.skills, skill]
      return { ...tech, skills }
    }))
  }

  const validate = () => {
    const errs = technicians.map((t) => {
      const e = {}
      if (!t.name.trim()) e.name = 'Required'
      return e
    })
    setErrors(errs)
    return errs.every((e) => Object.keys(e).length === 0)
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900">Technician team</h2>
        <p className="text-gray-500 text-sm mt-1">
          Add the technicians who will be assigned to jobs.
          {plan === 'mini' && <span className="text-amber-600 ml-1">Starter plan: up to 5 technicians.</span>}
        </p>
      </div>

      <div className="space-y-4">
        {technicians.map((tech, idx) => (
          <div key={idx} className="border border-gray-200 rounded-xl p-4 bg-gray-50 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-gray-700">Technician {idx + 1}</span>
              {technicians.length > 1 && (
                <button type="button" onClick={() => removeTech(idx)} className="text-red-400 hover:text-red-600">
                  <Trash2 size={14} />
                </button>
              )}
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <Label>Full name</Label>
                <Input value={tech.name} onChange={setField(idx, 'name')} placeholder="Jane Smith" />
                <FieldError msg={errors[idx]?.name} />
              </div>
              <div>
                <Label optional>Phone</Label>
                <Input value={tech.phone} onChange={setField(idx, 'phone')} placeholder="(321) 555-0200" />
              </div>
              <div>
                <Label optional>Email</Label>
                <Input type="email" value={tech.email} onChange={setField(idx, 'email')} placeholder="jane@peakhvac.com" />
              </div>
            </div>
            <div>
              <Label optional>Skills</Label>
              <div className="flex flex-wrap gap-2 mt-1">
                {SKILL_OPTIONS.map((skill) => (
                  <button
                    key={skill}
                    type="button"
                    onClick={() => toggleSkill(idx, skill)}
                    className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                      tech.skills.includes(skill)
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'bg-white text-gray-600 border-gray-300 hover:border-blue-400'
                    }`}
                  >
                    {skill.charAt(0).toUpperCase() + skill.slice(1)}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      {!atLimit && (
        <button
          type="button"
          onClick={addTech}
          className="flex items-center gap-2 text-blue-600 hover:text-blue-700 text-sm font-medium border border-blue-200 hover:border-blue-400 px-4 py-2 rounded-lg transition-colors"
        >
          <Plus size={14} /> Add another technician
        </button>
      )}

      <div className="flex justify-between pt-2">
        <button onClick={onBack} className="flex items-center gap-2 text-gray-500 hover:text-gray-700 px-4 py-2 rounded-xl border border-gray-200 hover:border-gray-300 transition-colors">
          <ChevronLeft size={16} /> Back
        </button>
        <button
          onClick={() => validate() && onNext()}
          className="flex items-center gap-2 bg-blue-600 text-white px-6 py-2.5 rounded-xl font-medium hover:bg-blue-700 transition-colors"
        >
          Next <ChevronRight size={16} />
        </button>
      </div>
    </div>
  )
}

// ─── Step 5: Hours & Admin Login ──────────────────────────────────────────────

function StepHoursLogin({ hours, onHoursChange, admin, onAdminChange, onSubmit, onBack, submitting, error }) {
  const [adminErrors, setAdminErrors] = useState({})

  const updateHour = (idx, field, value) => {
    onHoursChange((h) => h.map((row, i) => i === idx ? { ...row, [field]: value } : row))
  }

  const validate = () => {
    const e = {}
    if (admin.password && admin.password.length < 8) e.password = 'Password must be at least 8 characters'
    if (admin.password && admin.password !== admin.confirm) e.confirm = 'Passwords do not match'
    setAdminErrors(e)
    return Object.keys(e).length === 0
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900">Hours & admin login</h2>
        <p className="text-gray-500 text-sm mt-1">Set operating hours and optionally create a login for this business's admin.</p>
      </div>

      {/* Business Hours */}
      <div>
        <p className="text-sm font-semibold text-gray-700 mb-3">Business hours</p>
        <div className="border border-gray-200 rounded-xl overflow-hidden">
          {hours.map((row, idx) => (
            <div key={idx} className={`flex items-center gap-3 px-4 py-3 ${idx < hours.length - 1 ? 'border-b border-gray-100' : ''}`}>
              <span className="w-24 text-sm text-gray-700 font-medium shrink-0">{DAYS[idx]}</span>
              <label className="flex items-center gap-2 cursor-pointer shrink-0">
                <input
                  type="checkbox"
                  checked={row.is_active}
                  onChange={(e) => updateHour(idx, 'is_active', e.target.checked)}
                  className="rounded"
                />
                <span className="text-xs text-gray-500">{row.is_active ? 'Open' : 'Closed'}</span>
              </label>
              {row.is_active && (
                <>
                  <input
                    type="time"
                    value={row.open_time}
                    onChange={(e) => updateHour(idx, 'open_time', e.target.value)}
                    className="border border-gray-200 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="text-gray-400 text-sm">to</span>
                  <input
                    type="time"
                    value={row.close_time}
                    onChange={(e) => updateHour(idx, 'close_time', e.target.value)}
                    className="border border-gray-200 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Admin Login */}
      <div className="border-t pt-5">
        <p className="text-sm font-semibold text-gray-700 mb-1">Admin login <span className="font-normal text-gray-400">(optional)</span></p>
        <p className="text-xs text-gray-400 mb-4">Create a separate login for the client to access their own dashboard. Leave blank if you'll manage access centrally.</p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <Label optional>Username</Label>
            <Input
              value={admin.username}
              onChange={(e) => onAdminChange((a) => ({ ...a, username: e.target.value }))}
              placeholder="peakhvac-admin"
            />
          </div>
          <div>
            <Label optional>Password</Label>
            <Input
              type="password"
              value={admin.password}
              onChange={(e) => onAdminChange((a) => ({ ...a, password: e.target.value }))}
              placeholder="Min 8 characters"
            />
            <FieldError msg={adminErrors.password} />
          </div>
          <div>
            <Label optional>Confirm password</Label>
            <Input
              type="password"
              value={admin.confirm}
              onChange={(e) => onAdminChange((a) => ({ ...a, confirm: e.target.value }))}
              placeholder="Repeat password"
            />
            <FieldError msg={adminErrors.confirm} />
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
          {error}
        </div>
      )}

      <div className="flex justify-between pt-2">
        <button onClick={onBack} className="flex items-center gap-2 text-gray-500 hover:text-gray-700 px-4 py-2 rounded-xl border border-gray-200 hover:border-gray-300 transition-colors">
          <ChevronLeft size={16} /> Back
        </button>
        <button
          onClick={() => validate() && onSubmit()}
          disabled={submitting}
          className="flex items-center gap-2 bg-green-600 text-white px-6 py-2.5 rounded-xl font-medium hover:bg-green-700 transition-colors disabled:opacity-50"
        >
          {submitting ? 'Creating…' : <><CheckCircle2 size={16} /> Create Client</>}
        </button>
      </div>
    </div>
  )
}

// ─── Done Screen ──────────────────────────────────────────────────────────────

function StepDone({ business, techniciansCount, servicesCount, onGoToDashboard, onAddAnother }) {
  return (
    <div className="text-center py-6">
      <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-5">
        <CheckCircle2 size={32} className="text-green-600" />
      </div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">{business.name} is live!</h2>
      <p className="text-gray-500 text-sm mb-8 max-w-sm mx-auto">
        The platform is configured and ready. Here's a summary of what was set up.
      </p>

      <div className="grid grid-cols-3 gap-4 max-w-sm mx-auto mb-8">
        <div className="bg-blue-50 rounded-xl p-4">
          <div className="text-2xl font-bold text-blue-600">{servicesCount}</div>
          <div className="text-xs text-gray-500 mt-0.5">Service{servicesCount !== 1 ? 's' : ''}</div>
        </div>
        <div className="bg-purple-50 rounded-xl p-4">
          <div className="text-2xl font-bold text-purple-600">{techniciansCount}</div>
          <div className="text-xs text-gray-500 mt-0.5">Technician{techniciansCount !== 1 ? 's' : ''}</div>
        </div>
        <div className="bg-green-50 rounded-xl p-4">
          <div className="text-2xl font-bold text-green-600">{business.plan === 'full' ? 'Pro' : 'Starter'}</div>
          <div className="text-xs text-gray-500 mt-0.5">Plan</div>
        </div>
      </div>

      <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 max-w-sm mx-auto mb-8 text-left space-y-2">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Next steps</p>
        <ul className="text-sm text-gray-700 space-y-1.5">
          <li className="flex items-start gap-2">
            <span className="text-blue-500 mt-0.5">→</span>
            Add their website contact form to send submissions to the API
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-500 mt-0.5">→</span>
            Share the booking link with the client
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-500 mt-0.5">→</span>
            Configure on-call routing if they offer emergency service
          </li>
          {business.plan === 'full' && (
            <li className="flex items-start gap-2">
              <span className="text-blue-500 mt-0.5">→</span>
              Set up the monthly check-in call cadence
            </li>
          )}
        </ul>
      </div>

      <div className="flex flex-col sm:flex-row gap-3 justify-center">
        <button
          onClick={onGoToDashboard}
          className="flex items-center justify-center gap-2 bg-blue-600 text-white px-6 py-2.5 rounded-xl font-medium hover:bg-blue-700 transition-colors"
        >
          Open {business.name} Dashboard <ArrowRight size={16} />
        </button>
        <button
          onClick={onAddAnother}
          className="flex items-center justify-center gap-2 text-gray-600 border border-gray-200 px-6 py-2.5 rounded-xl font-medium hover:bg-gray-50 transition-colors"
        >
          Onboard another client
        </button>
      </div>
    </div>
  )
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function OnboardingPage() {
  const navigate = useNavigate()
  const { selectBusiness } = useBusinessContext()

  const [step, setStep] = useState(1)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const [createdBusiness, setCreatedBusiness] = useState(null)

  const [bizForm, setBizForm] = useState({
    name: '', slug: '', industry: '', plan: 'full',
    phone: '', email: '', address: '', website: '',
    brand_color: '#f97316', logo_url: '',
    ai_agent_name: '', ai_system_prompt: '', from_email: '', twilio_phone_number: '',
    is_demo: false,
  })

  const [services, setServices] = useState([
    { name: '', category: '', duration_minutes: 60, base_price: '', description: '' },
  ])

  const [technicians, setTechnicians] = useState([
    { name: '', phone: '', email: '', skills: [] },
  ])

  const [hours, setHours] = useState(defaultHours)

  const [adminForm, setAdminForm] = useState({ username: '', password: '', confirm: '' })

  const handleSubmit = async () => {
    setSubmitting(true)
    setSubmitError('')
    try {
      // 1. Create business
      const created = await createBusiness({
        name: bizForm.name,
        slug: bizForm.slug,
        industry: bizForm.industry,
        plan: bizForm.plan,
        phone: bizForm.phone || null,
        email: bizForm.email || null,
        address: bizForm.address || null,
        website: bizForm.website || null,
        brand_color: bizForm.brand_color || null,
        logo_url: bizForm.logo_url || null,
        ai_agent_name: bizForm.ai_agent_name || null,
        ai_system_prompt: bizForm.ai_system_prompt || null,
        from_email: bizForm.from_email || null,
        twilio_phone_number: bizForm.twilio_phone_number || null,
        is_demo: bizForm.is_demo,
        admin_username: adminForm.username || undefined,
        admin_password: adminForm.password || undefined,
      })

      const businessId = created.id

      // 2. Create services (sequential to preserve order)
      for (const svc of services) {
        await createService({
          name: svc.name,
          category: svc.category,
          duration_minutes: Number(svc.duration_minutes),
          base_price: svc.base_price ? Number(svc.base_price) : null,
          description: svc.description || null,
        }, businessId)
      }

      // 3. Create technicians
      for (const tech of technicians) {
        await createTechnician({
          name: tech.name,
          phone: tech.phone || null,
          email: tech.email || null,
          skills: tech.skills,
        }, businessId)
      }

      // 4. Set business hours
      await updateBusinessHours(
        hours.map((h) => ({
          day_of_week: h.day_of_week,
          open_time: h.open_time,
          close_time: h.close_time,
          is_active: h.is_active,
        })),
        businessId,
      )

      setCreatedBusiness(created)
      setStep(6) // done
    } catch (e) {
      setSubmitError(e.message || 'Something went wrong. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleGoToDashboard = () => {
    if (createdBusiness) {
      selectBusiness(createdBusiness)
      navigate('/')
    }
  }

  const handleAddAnother = () => {
    setStep(1)
    setCreatedBusiness(null)
    setSubmitError('')
    setBizForm({
      name: '', slug: '', industry: '', plan: 'full',
      phone: '', email: '', address: '', website: '',
      brand_color: '#f97316', logo_url: '',
      ai_agent_name: '', ai_system_prompt: '', from_email: '', twilio_phone_number: '',
      is_demo: false,
    })
    setServices([{ name: '', category: '', duration_minutes: 60, base_price: '', description: '' }])
    setTechnicians([{ name: '', phone: '', email: '', skills: [] }])
    setHours(defaultHours())
    setAdminForm({ username: '', password: '', confirm: '' })
  }

  return (
    <div className="max-w-2xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-1">
          <button
            onClick={() => navigate('/businesses')}
            className="text-sm text-gray-400 hover:text-gray-600"
          >
            ← Businesses
          </button>
        </div>
        <h1 className="text-2xl font-bold text-gray-900">Onboard New Client</h1>
        <p className="text-gray-500 text-sm mt-1">Takes about 5 minutes. Everything can be updated later.</p>
      </div>

      {/* Progress */}
      {step < 6 && <ProgressBar currentStep={step} />}

      {/* Steps */}
      {step === 1 && (
        <StepBusinessInfo
          data={bizForm}
          onChange={setBizForm}
          onNext={() => setStep(2)}
        />
      )}
      {step === 2 && (
        <StepAI
          data={bizForm}
          onChange={setBizForm}
          onNext={() => setStep(3)}
          onBack={() => setStep(1)}
        />
      )}
      {step === 3 && (
        <StepServices
          services={services}
          onChange={setServices}
          onNext={() => setStep(4)}
          onBack={() => setStep(2)}
          plan={bizForm.plan}
        />
      )}
      {step === 4 && (
        <StepTeam
          technicians={technicians}
          onChange={setTechnicians}
          onNext={() => setStep(5)}
          onBack={() => setStep(3)}
          plan={bizForm.plan}
        />
      )}
      {step === 5 && (
        <StepHoursLogin
          hours={hours}
          onHoursChange={setHours}
          admin={adminForm}
          onAdminChange={setAdminForm}
          onSubmit={handleSubmit}
          onBack={() => setStep(4)}
          submitting={submitting}
          error={submitError}
        />
      )}
      {step === 6 && createdBusiness && (
        <StepDone
          business={createdBusiness}
          servicesCount={services.length}
          techniciansCount={technicians.length}
          onGoToDashboard={handleGoToDashboard}
          onAddAnother={handleAddAnother}
        />
      )}
    </div>
  )
}
