"""Image validation and preprocessing for inference.

Must stay consistent with ml/common.py::decode_image:
    RGB -> tf.image.resize to 224x224 (bilinear) -> float32 in [0, 255].
Normalisation to [-1, 1] happens inside the saved model (Rescaling layer).
"""
from __future__ import annotations

import io
import re
import uuid
from pathlib import Path

import numpy as np
from PIL import Image, UnidentifiedImageError

IMG_SIZE = (224, 224)
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
ALLOWED_FORMATS = {"JPEG", "PNG"}
MIN_SIDE = 32


class InvalidImageError(ValueError):
    """Raised when an upload is not a usable JPG/PNG image."""


def safe_filename(original: str | None) -> str:
    name = Path(original or "upload").name
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)[:80]
    return name or "upload"


def extension_allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def stored_name(original: str | None) -> str:
    """Unguessable on-disk name, so uploads can never collide or be enumerated."""
    ext = safe_filename(original).rsplit(".", 1)[-1].lower()
    ext = ext if ext in ALLOWED_EXTENSIONS else "jpg"
    return f"{uuid.uuid4().hex}.{ext}"


def load_image(data: bytes) -> Image.Image:
    """Decode bytes into an RGB PIL image, validating real content (not just extension)."""
    try:
        probe = Image.open(io.BytesIO(data))
        probe.verify()  # detects truncated/corrupt files
        img = Image.open(io.BytesIO(data))
        fmt = img.format
        img.load()
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
        raise InvalidImageError("File is not a valid image.") from exc
    if fmt not in ALLOWED_FORMATS:
        raise InvalidImageError("Only JPG and PNG images are supported.")
    if min(img.size) < MIN_SIDE:
        raise InvalidImageError(f"Image is too small (minimum {MIN_SIDE}px per side).")
    return img.convert("RGB")


def preprocess(img: Image.Image) -> np.ndarray:
    """Return float32 array of shape (1, 224, 224, 3) with values in [0, 255]."""
    import tensorflow as tf  # imported lazily so DB/validation tests run without TF

    arr = np.asarray(img, dtype=np.float32)
    resized = tf.image.resize(arr, IMG_SIZE).numpy()  # same op as training
    return resized[np.newaxis, ...].astype(np.float32)


def blur_score(img: Image.Image) -> float | None:
    """Laplacian variance (higher = sharper). None if OpenCV is unavailable."""
    try:
        import cv2
    except ImportError:
        return None
    gray = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())
