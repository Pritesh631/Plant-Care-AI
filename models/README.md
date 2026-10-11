# Model artifacts

Running `python ml/train.py` and `python ml/evaluate.py` produces:

| File | Purpose |
|------|---------|
| `plant_disease_model.keras` | Final trained MobileNetV2 model (not committed) |
| `class_names.json` | Ordered class list; index = model output index |
| `training_history.json` | Per-epoch loss/accuracy for each phase |
| `evaluation_report.json` | Test-set metrics (accuracy, precision, recall, F1, confusion matrix) |

`class_names.json` must be the exact file written during training. Never edit it by hand.

The backend refuses to serve predictions (HTTP 503) if the model or class file is missing. It never returns fake predictions.

For hosting, upload the `.keras` file to object storage (S3, Google Drive release asset, Hugging Face Hub) and download it at deploy time, or use Git LFS.
