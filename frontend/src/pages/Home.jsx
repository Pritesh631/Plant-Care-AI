import { Link } from 'react-router-dom'
import { BookOpen, Camera, ShieldCheck, Sprout } from 'lucide-react'

const features = [
  { icon: Camera, title: 'Upload or capture', text: 'Drop in a leaf photo from your device or camera.' },
  { icon: Sprout, title: 'Deep-learning analysis', text: 'A MobileNetV2 transfer-learning model predicts the likely condition.' },
  { icon: BookOpen, title: 'Care guidance', text: 'Symptoms, causes, prevention and general treatment notes.' },
  { icon: ShieldCheck, title: 'Honest results', text: 'Confidence scores and low-confidence warnings, never a guaranteed diagnosis.' },
]

export default function Home() {
  return (
    <div className="space-y-12">
      <section className="rounded-3xl bg-gradient-to-br from-leaf-100 via-leaf-50 to-white px-6 py-16 text-center sm:px-12">
        <h1 className="text-4xl font-bold text-leaf-900 sm:text-5xl">Spot plant disease early</h1>
        <p className="mx-auto mt-4 max-w-2xl text-lg text-slate-700">
          PlantCare AI analyses a photo of a leaf and suggests the most likely disease with a confidence score
          and practical care guidance.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Link to="/detect" className="btn-primary">Analyse a leaf</Link>
          <Link to="/library" className="btn-secondary">Browse disease library</Link>
        </div>
      </section>

      <section aria-label="Features" className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {features.map(({ icon: Icon, title, text }) => (
          <div key={title} className="card">
            <Icon className="h-8 w-8 text-leaf-600" aria-hidden="true" />
            <h2 className="mt-3 text-lg font-semibold text-leaf-900">{title}</h2>
            <p className="mt-1 text-sm text-slate-600">{text}</p>
          </div>
        ))}
      </section>
    </div>
  )
}
