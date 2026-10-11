import { useRef, useState } from 'react'
import { ImagePlus } from 'lucide-react'

/** Drag-and-drop / click / camera upload. Validation is done by the parent via onSelect. */
export default function UploadZone({ onSelect, disabled }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)

  const pick = (files) => {
    if (files && files[0]) onSelect(files[0])
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); if (!disabled) setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => { e.preventDefault(); setDragging(false); if (!disabled) pick(e.dataTransfer.files) }}
      className={`flex flex-col items-center rounded-2xl border-2 border-dashed p-10 text-center transition ${
        dragging ? 'border-leaf-600 bg-leaf-50' : 'border-leaf-300 bg-white'
      }`}
    >
      <ImagePlus className="h-10 w-10 text-leaf-600" aria-hidden="true" />
      <p className="mt-3 font-display text-lg font-semibold text-leaf-900">Drag and drop a leaf image</p>
      <p className="text-sm text-slate-600">JPG, JPEG or PNG, up to 5 MB</p>
      <label htmlFor="leaf-file" className="sr-only">Choose a leaf image</label>
      <input
        id="leaf-file" ref={inputRef} type="file" accept="image/jpeg,image/png"
        capture="environment" className="sr-only" disabled={disabled}
        onChange={(e) => { pick(e.target.files); e.target.value = '' }}
      />
      <button type="button" className="btn-primary mt-4" disabled={disabled}
        onClick={() => inputRef.current?.click()}>
        Choose or capture image
      </button>
    </div>
  )
}
