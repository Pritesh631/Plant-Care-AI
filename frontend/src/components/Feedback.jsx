import { AlertTriangle, Loader2 } from 'lucide-react'

export function Spinner({ label = 'Loading...' }) {
  return (
    <div role="status" className="flex items-center justify-center gap-2 py-10 text-leaf-700">
      <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
      <span>{label}</span>
    </div>
  )
}

export function ErrorAlert({ message, onRetry }) {
  if (!message) return null
  return (
    <div role="alert" className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
      <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
      <div className="flex-1">
        <p>{message}</p>
        {onRetry && (
          <button onClick={onRetry} className="mt-2 font-semibold underline">Try again</button>
        )}
      </div>
    </div>
  )
}

export function EmptyState({ title, children }) {
  return (
    <div className="rounded-2xl border border-dashed border-leaf-200 p-10 text-center">
      <p className="font-display text-lg font-semibold text-leaf-900">{title}</p>
      <div className="mt-1 text-sm text-slate-600">{children}</div>
    </div>
  )
}
