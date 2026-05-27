/**
 * RowMenu — a 3-dot (⋮) dropdown menu for table rows and cards.
 *
 * Usage:
 *   <RowMenu items={[
 *     { label: 'Edit',   icon: <Pencil size={14} />, onClick: () => openEdit(row) },
 *     { label: 'Delete', icon: <Trash2 size={14} />, onClick: () => del(row), danger: true },
 *     { label: 'Divider' },   ← renders a <hr> separator
 *   ]} />
 */

import { useState, useEffect, useRef } from 'react'
import { MoreVertical } from 'lucide-react'

export default function RowMenu({ items = [], align = 'right' }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  // Close on outside click
  useEffect(() => {
    if (!open) return
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  const handleItem = (item) => {
    setOpen(false)
    item.onClick?.()
  }

  return (
    <div ref={ref} className="relative inline-block">
      <button
        onClick={(e) => { e.stopPropagation(); setOpen(o => !o) }}
        className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
        title="More actions"
      >
        <MoreVertical size={16} />
      </button>

      {open && (
        <div
          className={`absolute z-50 mt-1 w-52 bg-white rounded-xl shadow-lg border border-gray-200 py-1 ${
            align === 'left' ? 'left-0' : 'right-0'
          }`}
        >
          {items.map((item, i) => {
            if (item.label === 'Divider') {
              return <hr key={i} className="my-1 border-gray-100" />
            }
            if (item.disabled) {
              return (
                <div key={i} className="flex items-center gap-2.5 px-3 py-2 text-sm text-gray-300 cursor-not-allowed">
                  {item.icon && <span className="shrink-0">{item.icon}</span>}
                  {item.label}
                </div>
              )
            }
            return (
              <button
                key={i}
                onClick={() => handleItem(item)}
                className={`w-full flex items-center gap-2.5 px-3 py-2 text-sm text-left transition-colors ${
                  item.danger
                    ? 'text-red-600 hover:bg-red-50'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                {item.icon && <span className="shrink-0 text-current">{item.icon}</span>}
                {item.label}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
