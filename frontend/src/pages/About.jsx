import useAsync from '../hooks/useAsync.js'
import { getHealth } from '../services/api.js'

const steps = [
  ['Dataset', 'PlantVillage leaf images (folder per class), split 70/15/15 into train, validation and test sets by file, stratified by class, so no image appears in two sets.'],
  ['Preprocessing', 'Images are resized to 224x224 RGB. Normalisation is built into the model, so training and inference share the exact same pipeline.'],
  ['Augmentation', 'Flips, rotation, zoom and contrast changes are applied to training images only.'],
  ['Baseline', 'A small three-block CNN provides a reference point.'],
  ['Transfer learning', 'MobileNetV2 (ImageNet weights) with a new classification head. The base is frozen first, then the top layers are fine-tuned at a low learning rate.'],
  ['Training controls', 'Early stopping, learning-rate reduction and model checkpoints on validation loss.'],
  ['Evaluation', 'Accuracy, macro precision, recall, F1 and a confusion matrix are measured on the held-out test set only.'],
]

export default function About() {
  const { data } = useAsync(getHealth)
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-3xl font-bold text-leaf-900">About the project</h1>
      <p className="text-slate-700">
        PlantCare AI is a plant disease detection system built with React, Flask and TensorFlow/Keras.
        This page describes the machine-learning methodology.
      </p>
      <ol className="space-y-3">
        {steps.map(([t, d], i) => (
          <li key={t} className="card !p-4">
            <p className="font-display font-semibold text-leaf-900">{i + 1}. {t}</p>
            <p className="mt-1 text-sm text-slate-700">{d}</p>
          </li>
        ))}
      </ol>
      <div className="card text-sm text-slate-700">
        <h2 className="font-display text-lg font-semibold text-leaf-900">Model status</h2>
        <p className="mt-1">
          {data ? (data.model_loaded ? `Model loaded (${data.num_classes} classes).` : 'Model not loaded on the server.') : 'Checking...'}
        </p>
        <p className="mt-2">
          Accuracy figures are not shown here. Run <code>python ml/evaluate.py</code> and read
          <code> models/evaluation_report.json</code> for numbers measured on your own test set.
        </p>
      </div>
      <p className="text-xs text-slate-500">
        Limitations: PlantVillage images are lab-style photos on plain backgrounds, so accuracy on field photos
        can be much lower. Predictions are not a substitute for expert diagnosis.
      </p>
    </div>
  )
}
