import { useState } from 'react'

interface Props {
  title: string
  defaultOpen?: boolean
  children: React.ReactNode
}

export default function CollapsiblePanel({ title, defaultOpen = false, children }: Props) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <section className="card">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between text-left"
        aria-expanded={open}
      >
        <h3 className="text-lg font-semibold text-gray-800">{title}</h3>
        <span className="text-gray-400 text-xl">{open ? '−' : '+'}</span>
      </button>
      {open && <div className="mt-4 border-t border-gray-100 pt-4">{children}</div>}
    </section>
  )
}
