"""Model loading and prediction. The model is loaded once and reused."""
from __future__ import annotations

import json
import threading
from pathlib import Path

import numpy as np
from PIL import Image

from disease_info import get_disease_info, split_class_name
from preprocessing import blur_score, preprocess

BLUR_THRESHOLD = 50.0  # heuristic; very low Laplacian variance suggests a blurry photo


class ModelNotAvailable(RuntimeError):
    """Model or class file missing/unloadable. The API maps this to HTTP 503."""


class Predictor:
    def __init__(self, model_path: str | Path, class_names_path: str | Path,
                 low_confidence_threshold: float = 0.60):
        self.model_path = Path(model_path)
        self.class_names_path = Path(class_names_path)
        self.threshold = low_confidence_threshold
        self.model = None
        self.class_names: list[str] = []
        self.error: str | None = None
        self._lock = threading.Lock()

    def load(self) -> bool:
        try:
            if not self.class_names_path.exists():
                raise FileNotFoundError(f"Class names file not found: {self.class_names_path}")
            if not self.model_path.exists():
                raise FileNotFoundError(
                    f"Model file not found: {self.model_path}. Train it with `python ml/train.py` "
                    "(see README) or place plant_disease_model.keras in models/.")
            self.class_names = json.loads(self.class_names_path.read_text())
            from tensorflow import keras
            self.model = keras.models.load_model(self.model_path)
            out = self.model.output_shape[-1]
            if out != len(self.class_names):
                raise ValueError(f"Model outputs {out} classes but class_names.json lists "
                                 f"{len(self.class_names)}. Files are from different training runs.")
            self.error = None
            return True
        except Exception as exc:  # report status instead of crashing the server
            self.model, self.error = None, str(exc)
            return False

    @property
    def ready(self) -> bool:
        return self.model is not None

    def predict(self, img: Image.Image, top_k: int = 3) -> dict:
        if not self.ready:
            raise ModelNotAvailable(self.error or "Model is not loaded.")
        batch = preprocess(img)
        with self._lock:  # Keras predict is not guaranteed thread-safe
            probs = self.model.predict(batch, verbose=0)[0]
        order = np.argsort(probs)[::-1][:top_k]
        top = []
        for i in order:
            plant, condition = split_class_name(self.class_names[i])
            top.append({"class_name": self.class_names[i], "plant": plant,
                        "disease": condition, "confidence": float(probs[i])})
        best = top[0]
        info = get_disease_info(best["class_name"])
        sharp = blur_score(img)
        return {
            "class_name": best["class_name"],
            "plant": best["plant"],
            "disease": best["disease"],
            "confidence": best["confidence"],
            "is_healthy": info["is_healthy"],
            "low_confidence": best["confidence"] < self.threshold,
            "possibly_blurry": sharp is not None and sharp < BLUR_THRESHOLD,
            "top_predictions": top,
            "disease_info": info,
            "disclaimer": ("This is an automated estimate from a leaf image, not a confirmed "
                           "diagnosis. Verify with an agricultural expert."),
        }
