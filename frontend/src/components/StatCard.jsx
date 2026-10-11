export default function StatCard({ icon: Icon, label, value }) {
  return (
    <div className="card flex items-center gap-4 !p-5">
      <div className="rounded-xl bg-leaf-100 p-3 text-leaf-700"><Icon className="h-6 w-6" aria-hidden="true" /></div>
      <div>
        <p className="text-sm text-slate-500">{label}</p>
        <p className="font-display text-2xl font-bold text-leaf-900">{value}</p>
      </div>
    </div>
  )
}
