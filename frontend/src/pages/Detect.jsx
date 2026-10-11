import { useEffect, useState } from 'react'
import { RotateCcw, ScanSearch } from 'lucide-react'
import UploadZone from '../components/UploadZone.jsx'
import ResultCard from '../components/ResultCard.jsx'
import { ErrorAlert, Spinner } from '../components/Feedback.jsx'
import { errorMessage, predictImage, validateImage } from '../services/api.js'

export default function Detect() {
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  useEffect(() => {
    if (!file) { setPreviewUrl(null); return undefined }
    const url = URL.createObjectURL(file)
    setPreviewUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  const onSelect = (f) => {
    const problem = validateImage(f)
    setResult(null)
    if (problem) { setError(problem); setFile(null); return }
    setError(null)
    setFile(f)
  }

  const reset = () => { setFile(null); setResult(null); setError(null) }

  const analyse = async () => {
    setLoading(true); setError(null); setResult(null)
    try {
      setResult(await predictImage(file))
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-leaf-900">Detect plant disease</h1>
        <p className="mt-1 text-slate-600">Upload a clear, well-lit photo of a single leaf.</p>
      </header>

      <ErrorAlert message={error} onRetry={file && !loading ? analyse : undefined} />

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          {!file ? (
            <UploadZone onSelect={onSelect} disabled={loading} />
          ) : (
            <div className="card space-y-4">
              <img src={previewUrl} alt="Selected leaf preview"
                className="max-h-96 w-full rounded-xl object-contain bg-leaf-50" />
              <p className="truncate text-sm text-slate-600">{file.name}</p>
              <div className="flex gap-3">
                <button className="btn-primary" onClick={analyse} disabled={loading}>
                  <ScanSearch className="h-4 w-4" aria-hidden="true" /> Analyse leaf
                </button>
                <button className="btn-secondary" onClick={reset} disabled={loading}>
                  <RotateCcw className="h-4 w-4" aria-hidden="true" /> Clear
                </button>
              </div>
            </div>
          )}
        </div>

        <div>
          {loading && <div className="card"><Spinner label="Analysing leaf..." /></div>}
          {result && !loading && <ResultCard result={result} />}
          {!result && !loading && (
            <div className="card text-sm text-slate-600">
              Results appear here with the predicted disease, confidence, top three predictions and care guidance.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
