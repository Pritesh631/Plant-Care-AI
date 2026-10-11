import { Info } from 'lucide-react'

function Section({ title, items }) {
  if (!items || items.length === 0) return null
  return (
    <div>
      <h4 className="font-display text-sm font-semibold text-leaf-900">{title}</h4>
      <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-slate-700">
        {items.map((t) => <li key={t}>{t}</li>)}
      </ul>
    </div>
  )
}

export function VerificationBadge({ info }) {
  const verified = info.verification === 'verified'
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${
      verified ? 'bg-leaf-100 text-leaf-800' : 'bg-amber-100 text-amber-800'
    }`}>
      <Info className="h-3 w-3" aria-hidden="true" />
      {verified ? 'Expert verified' : 'AI-generated, not expert-reviewed'}
    </span>
  )
}

export default function DiseaseInfo({ info }) {
  if (!info) return null
  if (!info.info_available) {
    return <p className="text-sm text-slate-600">No stored information for this class yet.</p>
  }
  return (
    <div className="space-y-4">
      <VerificationBadge info={info} />
      <Section title="Common symptoms" items={info.symptoms} />
      <Section title="Possible causes" items={info.causes} />
      <Section title="Prevention" items={info.prevention} />
      <Section title="General treatment guidance" items={info.treatment} />
      <Section title="Crop care" items={info.crop_care} />
      {info.note && <p className="text-xs text-slate-500">{info.note}</p>}
    </div>
  )
}
