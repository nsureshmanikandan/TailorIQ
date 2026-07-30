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
        <h3 className="text-base font-semibold text-white">{title}</h3>
        <span className="text-slate-500 text-xl">{open ? '−' : '+'}</span>
      </button>
      {open && <div className="mt-4 border-t pt-4" style={{ borderColor: 'rgba(255,255,255,0.07)' }}>{children}</div>}
    </section>
  )
}
