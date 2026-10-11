import { useMemo, useState } from 'react'
import { ChevronDown, Search } from 'lucide-react'
import DiseaseInfo from '../components/DiseaseInfo.jsx'
import { EmptyState, ErrorAlert, Spinner } from '../components/Feedback.jsx'
import useAsync from '../hooks/useAsync.js'
import { getDiseases } from '../services/api.js'

export default function Library() {
  const { data, loading, error, reload } = useAsync(getDiseases)
  const [plant, setPlant] = useState('All')
  const [query, setQuery] = useState('')
  const [openId, setOpenId] = useState(null)

  const items = useMemo(() => {
    if (!data) return []
    const q = query.trim().toLowerCase()
    return data.diseases.filter((d) =>
      (plant === 'All' || d.plant === plant) &&
      (!q || `${d.plant} ${d.disease}`.toLowerCase().includes(q)))
  }, [data, plant, query])

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-leaf-900">Disease library</h1>
        <p className="mt-1 text-slate-600">Plants and conditions the model can recognise.</p>
      </header>

      {loading && <Spinner />}
      <ErrorAlert message={error} onRetry={reload} />

      {data && (
        <>
          <div className="flex flex-col gap-3 sm:flex-row">
            <div className="relative flex-1">
              <label htmlFor="lib-search" className="sr-only">Search diseases</label>
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" aria-hidden="true" />
              <input id="lib-search" className="input pl-9" placeholder="Search plant or disease"
                value={query} onChange={(e) => setQuery(e.target.value)} />
            </div>
            <div>
              <label htmlFor="lib-plant" className="sr-only">Filter by plant</label>
              <select id="lib-plant" className="input" value={plant} onChange={(e) => setPlant(e.target.value)}>
                <option>All</option>
                {data.plants.map((p) => <option key={p}>{p}</option>)}
              </select>
            </div>
          </div>

          {!data.model_loaded && (
            <p className="rounded-lg bg-amber-50 p-3 text-sm text-amber-900">
              The model is not loaded on the server, so this list shows classes with stored information only.
            </p>
          )}

          {items.length === 0 ? (
            <EmptyState title="No matches">Try a different search or plant filter.</EmptyState>
          ) : (
            <ul className="grid gap-4 md:grid-cols-2">
              {items.map((d) => {
                const open = openId === d.class_name
                return (
                  <li key={d.class_name} className="card !p-4">
                    <button className="flex w-full items-center justify-between text-left"
                      aria-expanded={open} onClick={() => setOpenId(open ? null : d.class_name)}>
                      <span>
                        <span className="block text-xs uppercase tracking-wide text-leaf-600">{d.plant}</span>
                        <span className="font-display font-semibold text-leaf-900">{d.disease}</span>
                      </span>
                      <ChevronDown className={`h-5 w-5 transition ${open ? 'rotate-180' : ''}`} aria-hidden="true" />
                    </button>
                    {open && <div className="mt-4 border-t border-leaf-100 pt-4"><DiseaseInfo info={d} /></div>}
                  </li>
                )
              })}
            </ul>
          )}
        </>
      )}
    </div>
  )
}
