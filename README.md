# PlantCare AI - Plant Disease Detection and Prediction System

Upload a leaf photo and get the most likely plant disease, a confidence score, top-3 predictions and care guidance.
React + Flask + TensorFlow (MobileNetV2 transfer learning).

> **Status:** code is complete, but no model is trained yet and no accuracy is claimed. Train it (section 5) and read
> `models/evaluation_report.json` for measured results. Until then the API returns `503` for predictions, never fake output.

## 1. Features
- Drag-and-drop / camera upload (JPG, JPEG, PNG, 5 MB max), preview, reset, validation
- Prediction with confidence, top-3, low-confidence and blur warnings
- Disease library (symptoms, causes, prevention, treatment, crop care), each entry labelled **AI-generated** or **expert verified**
- SQLite history with delete, and dashboard analytics computed from stored rows
- Six pages: Home, Detect, Disease Library, History & Dashboard, About, Contact

## 2. Tech stack
Frontend: React 18, Vite, Tailwind CSS, Axios, React Router, Recharts, Lucide.
Backend: Flask, TensorFlow/Keras, NumPy, Pillow, OpenCV (blur check), SQLite.
ML: baseline CNN and MobileNetV2, scikit-learn metrics.

## 3. Project structure
```
plantcare-ai/
├── backend/   app.py predict.py preprocessing.py database.py disease_info.py download_model.py tests/
├── frontend/  src/{components,pages,services,hooks}
├── ml/        common.py train.py evaluate.py dataset/
├── models/    class_names.json README.md  (+ generated artifacts)
├── render.yaml  .env.example  .gitignore
```

## 4. Dataset
PlantVillage (Hughes & Salathé, 2015; Mohanty et al., 2016). Common mirror: Kaggle "PlantVillage dataset" / "New Plant Diseases Dataset".
**Check the licence on the exact copy you download** (the original is distributed under CC0/open terms on several mirrors, but mirrors differ) and cite the paper.
Place images as `ml/dataset/<ClassName>/*.jpg`, e.g. `ml/dataset/Tomato___Late_blight/`. Use the colour images, not the segmented/grayscale variants.
`models/class_names.json` ships with the standard 38 PlantVillage class names; training overwrites it with the classes found in your folder.

## 5. Model architecture and training
- Input 224x224 RGB, raw 0-255 pixels; `Rescaling` to [-1, 1] is inside the model so training and inference match
- Baseline: 3 conv blocks + GAP + dropout + softmax
- Main: MobileNetV2 (ImageNet) -> GAP -> Dropout(0.3) -> Dense softmax. Phase 1 frozen base (lr 1e-3), phase 2 fine-tune top 30 layers with BatchNorm frozen (lr 1e-5)
- Stratified 70/15/15 split by file; augmentation on training data only; early stopping, LR reduction, checkpoints

```bash
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
python ml/train.py --epochs 10 --fine-tune-epochs 5      # add --skip-baseline to save time
python ml/evaluate.py
```
Outputs in `models/`: `plant_disease_model.keras`, `class_names.json`, `training_history.json`, `evaluation_report.json`, `confusion_matrix.png`, `baseline_cnn.keras`, `dataset_split.json`.

## 6. Evaluation results
Not yet measured. After `evaluate.py`, copy the numbers from `models/evaluation_report.json` here. Do not quote validation accuracy as test accuracy.

## 7. Run locally
```bash
# backend (from repo root)
cp .env.example backend/.env
cd backend && python app.py            # http://localhost:5000

# frontend (new terminal)
cd frontend
echo "VITE_API_BASE_URL=http://localhost:5000/api" > .env
echo "VITE_CONTACT_EMAIL=you@example.com" >> .env
npm install && npm run dev             # http://localhost:5173
```
Tests: `cd backend && python -m pytest -q`

## 8. API
| Method | Path | Notes |
|---|---|---|
| GET | `/api/health` | `{"status":"ok","model_loaded":true,"num_classes":38}`; `degraded` if model missing |
| GET | `/api/diseases` | supported classes with info |
| POST | `/api/predict` | multipart field `image` |
| GET | `/api/history?limit=&offset=` | stored predictions |
| DELETE | `/api/history/<id>` | 200, or 404 |
| DELETE | `/api/history` | clear all |
| GET | `/api/analytics` | totals, top diseases, by plant, by day, recent |

```bash
curl -F "image=@leaf.jpg" http://localhost:5000/api/predict
```
```json
{"plant":"Tomato","disease":"Late blight","class_name":"Tomato___Late_blight","confidence":0.97,
 "is_healthy":false,"low_confidence":false,"top_predictions":[{"class_name":"...","confidence":0.97}],
 "disease_info":{"verification":"ai_generated","symptoms":["..."]},"disclaimer":"...","history_id":1}
```
Errors: `400` missing/empty file, `413` too large, `415` bad extension, `422` corrupt/non-JPG/PNG/too small, `503` model unavailable.
Uploaded images are stored under `backend/uploads/` with random names and are never served by the API; deleting a record deletes the file. Set `SAVE_UPLOADS=false` to store nothing.

## 9. Deployment
1. **Model**: upload `plant_disease_model.keras` to storage with a direct link (Hugging Face Hub, S3, release asset). Hosts' disk is ephemeral and the model is not in Git.
2. **Backend (Render)**: connect the repo, use `render.yaml`, set `MODEL_URL` and `CORS_ORIGINS` (your frontend URL). TensorFlow needs roughly 1 GB RAM, so the free tier may be too small. SQLite and uploads are lost on redeploy unless you add a persistent disk or switch to Postgres.
3. **Frontend (Vercel/Netlify)**: root `frontend`, build `npm run build`, output `dist`, env `VITE_API_BASE_URL=https://<backend>/api`. `vercel.json` and `public/_redirects` handle SPA routing.

Production checklist: HTTPS only; `CORS_ORIGINS` set to exact origin; no `.env` committed; persistent storage for DB; rate limiting and authentication if public (history is currently shared by all users); model measured on a field-photo test set; disease info reviewed by an expert.

## 10. Known limitations
- PlantVillage is lab-style imagery; accuracy on real field photos is usually much lower
- Single leaf, one dominant disease assumed; non-leaf images still get a prediction (low confidence is the only guard)
- History is global, not per-user (no authentication)
- Disease text is AI-generated and unreviewed; no pesticide products or doses are given
- Contact form opens the user's email client; nothing is stored server-side
- Tests for the API use a stub predictor; see Test report

## 11. Test report
Backend: `backend/tests/` covers valid/invalid uploads, size limit, spoofed extensions, unsafe filenames, history, delete, analytics, 503 without a model, DB constraints and a preprocessing parity test (training vs inference, needs TensorFlow).
**Run status in the build environment:** all Python files pass `py_compile`; the pytest suite and the frontend build were **not executed** there because package installation was blocked. Run them locally and record results here.

---

# Academic project report material

**Abstract.** Plant diseases reduce crop yield and quality, and early identification is difficult for smallholders without expert access. This project presents PlantCare AI, a web application that classifies leaf images into plant-disease and healthy classes using a MobileNetV2 transfer-learning model trained on PlantVillage, served by a Flask API with a React interface. Results are reported as confidence scores with explicit uncertainty warnings. *(Insert measured test accuracy and F1 from `evaluation_report.json`.)*

**Problem statement.** Manual disease scouting is slow, subjective and requires expertise. A low-cost tool that gives a fast, transparent first estimate from a phone photo can support earlier action and expert referral.

**Objectives.** (1) Build a multi-class leaf-disease classifier with leakage-free evaluation. (2) Expose it through a REST API. (3) Provide an accessible web UI with history and analytics. (4) Present predictions honestly, with confidence and limitations.

**Methodology.** Data collection (PlantVillage) -> class inspection -> stratified train/val/test split -> resizing and in-model normalisation -> augmentation (training only) -> baseline CNN -> MobileNetV2 feature extraction -> partial fine-tuning -> test-set evaluation (accuracy, macro precision/recall/F1, confusion matrix) -> deployment.

**System architecture.** Browser (React SPA) -> HTTPS/JSON -> Flask API (validation, preprocessing, model loaded once, SQLite) -> response with prediction and disease information. Training is offline in `ml/`; artifacts are loaded by the API at startup.

**Results.** *(Fill from `models/evaluation_report.json`: baseline vs MobileNetV2 accuracy, macro F1, most confused class pairs from the confusion matrix.)*

**Conclusion.** Transfer learning gives a practical classifier with modest compute. Reliability in the field depends on training data diversity, not on the architecture alone.

**Future scope.** Field-image datasets and domain adaptation; out-of-distribution (non-leaf) rejection; Grad-CAM explanations; user accounts; multilingual guidance; on-device TFLite inference; expert-verified knowledge base.
