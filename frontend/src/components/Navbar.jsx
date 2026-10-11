import { useState } from 'react'
import { NavLink, Link } from 'react-router-dom'
import { Leaf, Menu, X } from 'lucide-react'

const links = [
  { to: '/', label: 'Home' },
  { to: '/detect', label: 'Detect' },
  { to: '/library', label: 'Disease Library' },
  { to: '/history', label: 'History & Dashboard' },
  { to: '/about', label: 'About' },
  { to: '/contact', label: 'Contact' },
]

export default function Navbar() {
  const [open, setOpen] = useState(false)
  const cls = ({ isActive }) =>
    `rounded-md px-3 py-2 text-sm font-medium ${isActive ? 'bg-leaf-100 text-leaf-800' : 'text-slate-600 hover:bg-leaf-50'}`

  return (
    <header className="sticky top-0 z-20 border-b border-leaf-100 bg-white/95 backdrop-blur">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6" aria-label="Main">
        <Link to="/" className="flex items-center gap-2 font-display text-lg font-bold text-leaf-800">
          <Leaf className="h-6 w-6 text-leaf-600" aria-hidden="true" /> PlantCare AI
        </Link>
        <div className="hidden gap-1 md:flex">
          {links.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.to === '/'} className={cls}>{l.label}</NavLink>
          ))}
        </div>
        <button className="rounded-md p-2 md:hidden" onClick={() => setOpen(!open)}
          aria-expanded={open} aria-label="Toggle menu">
          {open ? <X /> : <Menu />}
        </button>
      </nav>
      {open && (
        <div className="flex flex-col gap-1 border-t border-leaf-100 px-4 pb-3 md:hidden">
          {links.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.to === '/'} className={cls} onClick={() => setOpen(false)}>
              {l.label}
            </NavLink>
          ))}
        </div>
      )}
    </header>
  )
}
