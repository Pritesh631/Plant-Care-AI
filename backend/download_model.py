"""Download the trained model at deploy time (the .keras file is not stored in Git).

Set MODEL_URL to a direct-download link (S3, Hugging Face Hub, GitHub release asset).
If MODEL_URL is unset or the file already exists this does nothing; the API then
reports status "degraded" and /api/predict returns 503 rather than fake results.
"""
import os
import sys
import urllib.request
from pathlib import Path

url = os.getenv("MODEL_URL")
target = (Path(__file__).resolve().parent / os.getenv("MODEL_PATH", "../models/plant_disease_model.keras")).resolve()

if target.exists():
    print(f"Model already present at {target}")
elif not url:
    print("MODEL_URL not set; skipping model download.", file=sys.stderr)
else:
    target.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading model to {target} ...")
    urllib.request.urlretrieve(url, target)
    print(f"Done ({target.stat().st_size / 1e6:.1f} MB)")
