import { useCallback, useState } from 'react'
import { Activity, Bug, Leaf, Trash2 } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import StatCard from '../components/StatCard.jsx'
import { EmptyState, ErrorAlert, Spinner } from '../components/Feedback.jsx'
import useAsync from '../hooks/useAsync.js'
import { clearHistory, deleteHistoryItem, errorMessage, getAnalytics, getHistory } from '../services/api.js'

const pretty = (s) => s.replaceAll('_', ' ')

export default function History() {
  const loader = useCallback(async () => {
    const [analytics, items] = await Promise.all([getAnalytics(), getHistory()])
    return { analytics, items }
  }, [])
  const { data, loading, error, reload } = useAsync(loader)
  const [actionError, setActionError] = useState(null)

  const remove = async (id) => {
    setActionError(null)
    try { await deleteHistoryItem(id); reload() } catch (e) { setActionError(errorMessage(e)) }
  }
  const clearAll = async () => {
    if (!window.confirm('Delete all prediction history? This cannot be undone.')) return
    setActionError(null)
    try { await clearHistory(); reload() } catch (e) { setActionError(errorMessage(e)) }
  }

  const a = data?.analytics
  const pieData = a ? [
    { name: 'Healthy', value: a.healthy_count, fill: '#389340' },
    { name: 'Diseased', value: a.diseased_count, fill: '#d97706' },
  ] : []

  return (
    <div className="space-y-8">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold text-leaf-900">History &amp; dashboard</h1>
          <p className="mt-1 text-slate-600">Statistics are calculated from your stored predictions.</p>
        </div>
        {data?.items.length > 0 && (
          <button className="btn-danger" onClick={clearAll}><Trash2 className="h-4 w-4" aria-hidden="true" /> Clear all</button>
        )}
      </header>

      {loading && <Spinner />}
      <ErrorAlert message={error || actionError} onRetry={error ? reload : undefined} />

      {a && a.total_predictions === 0 && (
        <EmptyState title="No predictions yet">Analyse a leaf on the Detect page and it will appear here.</EmptyState>
      )}

      {a && a.total_predictions > 0 && (
        <>
          <div className="grid gap-4 sm:grid-cols-3">
            <StatCard icon={Activity} label="Total predictions" value={a.total_predictions} />
            <StatCard icon={Leaf} label="Healthy leaves" value={a.healthy_count} />
            <StatCard icon={Bug} label="Diseased leaves" value={a.diseased_count} />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <section className="card" aria-label="Healthy versus diseased">
              <h2 className="mb-2 font-display font-semibold text-leaf-900">Healthy vs diseased</h2>
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie data={pieData} dataKey="value" nameKey="name" innerRadius={55} outerRadius={90}>
                    {pieData.map((d) => <Cell key={d.name} fill={d.fill} />)}
                  </Pie>
                  <Tooltip /><Legend />
                </PieChart>
              </ResponsiveContainer>
            </section>

            <section className="card" aria-label="Most frequently detected diseases">
              <h2 className="mb-2 font-display font-semibold text-leaf-900">Most detected diseases</h2>
              {a.top_diseases.length === 0 ? (
                <p className="py-10 text-center text-sm text-slate-600">No diseased predictions yet.</p>
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={a.top_diseases.map((d) => ({ ...d, label: `${pretty(d.plant)}: ${pretty(d.disease)}` }))}
                    layout="vertical" margin={{ left: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" allowDecimals={false} />
                    <YAxis type="category" dataKey="label" width={150} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#2a7632" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </section>
          </div>
        </>
      )}

      {data && data.items.length > 0 && (
        <section aria-label="Prediction history">
          <h2 className="mb-3 font-display text-xl font-semibold text-leaf-900">Recent predictions</h2>
          <div className="overflow-x-auto rounded-2xl border border-leaf-100">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="bg-leaf-50 text-leaf-900">
                <tr>
                  <th scope="col" className="p-3">Date</th><th scope="col" className="p-3">File</th>
                  <th scope="col" className="p-3">Result</th><th scope="col" className="p-3">Confidence</th>
                  <th scope="col" className="p-3"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((r) => (
                  <tr key={r.id} className="border-t border-leaf-100">
                    <td className="p-3 whitespace-nowrap">{new Date(r.created_at).toLocaleString()}</td>
                    <td className="max-w-[160px] truncate p-3">{r.original_filename}</td>
                    <td className="p-3">{pretty(r.plant)}: {pretty(r.disease)}</td>
                    <td className="p-3">{(r.confidence * 100).toFixed(1)}%</td>
                    <td className="p-3 text-right">
                      <button className="btn-danger !px-2 !py-1" onClick={() => remove(r.id)}
                        aria-label={`Delete prediction ${r.id}`}><Trash2 className="h-4 w-4" aria-hidden="true" /></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  )
}
