import { useState } from 'react'

// No backend endpoint stores feedback, so the form opens the visitor's email client.
// Set VITE_CONTACT_EMAIL in frontend/.env to your address.
const CONTACT_EMAIL = import.meta.env.VITE_CONTACT_EMAIL || ''

export default function Contact() {
  const [form, setForm] = useState({ name: '', email: '', message: '' })
  const [errors, setErrors] = useState({})
  const [sent, setSent] = useState(false)

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const submit = (e) => {
    e.preventDefault()
    const errs = {}
    if (!form.name.trim()) errs.name = 'Please enter your name.'
    if (!/^\S+@\S+\.\S+$/.test(form.email)) errs.email = 'Please enter a valid email address.'
    if (form.message.trim().length < 10) errs.message = 'Please write at least 10 characters.'
    setErrors(errs)
    if (Object.keys(errs).length) return
    const subject = encodeURIComponent('PlantCare AI feedback')
    const body = encodeURIComponent(`${form.message}\n\nFrom: ${form.name} <${form.email}>`)
    window.location.href = `mailto:${CONTACT_EMAIL}?subject=${subject}&body=${body}`
    setSent(true)
  }

  const field = (id, label, props = {}) => (
    <div>
      <label htmlFor={id} className="mb-1 block text-sm font-medium">{label}</label>
      {props.rows ? (
        <textarea id={id} className="input" value={form[id]} onChange={set(id)}
          aria-invalid={!!errors[id]} aria-describedby={errors[id] ? `${id}-err` : undefined} {...props} />
      ) : (
        <input id={id} className="input" value={form[id]} onChange={set(id)}
          aria-invalid={!!errors[id]} aria-describedby={errors[id] ? `${id}-err` : undefined} {...props} />
      )}
      {errors[id] && <p id={`${id}-err`} role="alert" className="mt-1 text-sm text-red-700">{errors[id]}</p>}
    </div>
  )

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-leaf-900">Contact &amp; feedback</h1>
        <p className="mt-1 text-slate-600">Found a wrong prediction or have an idea? Let us know.</p>
      </header>
      {!CONTACT_EMAIL && (
        <p className="rounded-lg bg-amber-50 p-3 text-sm text-amber-900">
          No contact address is configured. Set <code>VITE_CONTACT_EMAIL</code> in <code>frontend/.env</code>.
        </p>
      )}
      <form onSubmit={submit} className="card space-y-4" noValidate>
        {field('name', 'Name', { type: 'text', autoComplete: 'name' })}
        {field('email', 'Email', { type: 'email', autoComplete: 'email' })}
        {field('message', 'Message', { rows: 5 })}
        <button type="submit" className="btn-primary" disabled={!CONTACT_EMAIL}>Send feedback</button>
        {sent && <p role="status" className="text-sm text-leaf-700">Your email app should open with the message ready to send.</p>}
      </form>
    </div>
  )
}
