import { AlertTriangle, CheckCircle2, Bug } from 'lucide-react'
import DiseaseInfo from './DiseaseInfo.jsx'

const pct = (v) => `${(v * 100).toFixed(1)}%`
const pretty = (s) => s.replaceAll('_', ' ')

export default function ResultCard({ result }) {
  const healthy = result.is_healthy
  return (
    <section className="card space-y-5" aria-live="polite">
      <div className="flex items-start gap-3">
        {healthy
          ? <CheckCircle2 className="h-8 w-8 text-leaf-600" aria-hidden="true" />
          : <Bug className="h-8 w-8 text-amber-600" aria-hidden="true" />}
        <div>
          <p className="text-sm text-slate-500">Most likely result</p>
          <h2 className="text-2xl font-bold text-leaf-900">{pretty(result.plant)}: {pretty(result.disease)}</h2>
          <p className="text-sm text-slate-600">Model confidence {pct(result.confidence)}</p>
        </div>
      </div>

      <div className="h-2 overflow-hidden rounded-full bg-leaf-100" role="img"
        aria-label={`Confidence ${pct(result.confidence)}`}>
        <div className="h-full bg-leaf-600" style={{ width: pct(result.confidence) }} />
      </div>

      {result.low_confidence && (
        <div role="alert" className="flex gap-2 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
          <AlertTriangle className="h-5 w-5 shrink-0" aria-hidden="true" />
          Low confidence. Try a clearer, well-lit photo of a single leaf, and consult an expert before acting.
        </div>
      )}
      {result.possibly_blurry && (
        <p className="rounded-lg bg-slate-50 p-3 text-sm text-slate-700">
          The photo looks blurry, which can reduce accuracy.
        </p>
      )}

      <div>
        <h3 className="font-display text-sm font-semibold text-leaf-900">Top predictions</h3>
        <ul className="mt-2 space-y-2">
          {result.top_predictions.map((p) => (
            <li key={p.class_name} className="text-sm">
              <div className="flex justify-between">
                <span>{pretty(p.plant)}: {pretty(p.disease)}</span>
                <span className="font-medium">{pct(p.confidence)}</span>
              </div>
              <div className="mt-1 h-1.5 rounded-full bg-slate-100">
                <div className="h-full rounded-full bg-leaf-400" style={{ width: pct(p.confidence) }} />
              </div>
            </li>
          ))}
        </ul>
      </div>

      <DiseaseInfo info={result.disease_info} />
      <p className="border-t border-leaf-100 pt-3 text-xs text-slate-500">{result.disclaimer}</p>
    </section>
  )
}
