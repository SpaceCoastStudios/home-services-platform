/**
 * RowMenu — a 3-dot (⋮) dropdown menu for table rows and cards.
 * Uses a fixed-position portal so it's never clipped by overflow:hidden containers.
 *
 * Usage:
 *   <RowMenu items={[
 *     { label: 'Edit',   icon: <Pencil size={14} />, onClick: () => openEdit(row) },
 *     { label: 'Delete', icon: <Trash2 size={14} />, onClick: () => del(row), danger: true },
 *     { label: 'Divider' },   ← renders a <hr> separator
 *   ]} />
 */

import { useState, useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { MoreVertical } from 'lucide-react'

export default function RowMenu({ items = [], align = 'right' }) {
  const [open, setOpen] = useState(false)
  const [pos, setPos] = useState({ top: 0, left: 0 })
  const btnRef = useRef(null)

  // Position the dropdown relative to the button using fixed coords
  const openMenu = (e) => {
    e.stopPropagation()
    if (!open && btnRef.current) {
      const rect = btnRef.current.getBoundingClientRect()
      setPos({
        top: rect.bottom + 4,
        left: align === 'left' ? rect.left : rect.right - 208, // 208 = w-52
      })
    }
    setOpen(o => !o)
  }

  // Close on outside click or scroll
  useEffect(() => {
    if (!open) return
    const close = () => setOpen(false)
    document.addEventListener('mousedown', close)
    document.addEventListener('scroll', close, true)
    return () => {
      document.removeEventListener('mousedown', close)
      document.removeEventListener('scroll', close, true)
    }
  }, [open])

  const handleItem = (e, item) => {
    e.stopPropagation()
    setOpen(false)
    item.onClick?.()
  }

  const dropdown = open && (
    <div
      onMouseDown={(e) => e.stopPropagation()}
      style={{ position: 'fixed', top: pos.top, left: pos.left, zIndex: 9999 }}
      className="w-52 bg-surface rounded-xl shadow-lg border border-gray-200 py-1"
    >
      {items.map((item, i) => {
        if (item.label === 'Divider') {
          return <hr key={i} className="my-1 border-gray-100" />
        }
        if (item.disabled) {
          return (
            <div key={i} className="flex items-center gap-2.5 px-3 py-2 text-sm text-gray-300 cursor-not-allowed select-none">
              {item.icon && <span className="shrink-0">{item.icon}</span>}
              {item.label}
            </div>
          )
        }
        return (
          <button
            key={i}
            onMouseDown={(e) => handleItem(e, item)}
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
  )

  return (
    <>
      <button
        ref={btnRef}
        onClick={openMenu}
        className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
        title="More actions"
      >
        <MoreVertical size={16} />
      </button>

      {createPortal(dropdown, document.body)}
    </>
  )
}
