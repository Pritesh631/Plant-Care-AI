"""Shared constants and helpers for training and evaluation.

Preprocessing contract (must match backend/preprocessing.py):
    - RGB image resized to 224x224
    - float32 pixel values in [0, 255]
    - MobileNetV2 normalisation (scale to [-1, 1]) is done INSIDE the model
      via a Rescaling layer, so inference only needs raw 0-255 pixels.
"""
from __future__ import annotations

import json
import os
import random
from pathlib import Path

import numpy as np
import tensorflow as tf

IMG_SIZE = (224, 224)
BATCH_SIZE = 32
SEED = 42
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = ROOT / "ml" / "dataset"
MODELS_DIR = ROOT / "models"
MODEL_PATH = MODELS_DIR / "plant_disease_model.keras"
BASELINE_PATH = MODELS_DIR / "baseline_cnn.keras"
CLASS_NAMES_PATH = MODELS_DIR / "class_names.json"
SPLIT_PATH = MODELS_DIR / "dataset_split.json"
HISTORY_PATH = MODELS_DIR / "training_history.json"
REPORT_PATH = MODELS_DIR / "evaluation_report.json"
CONFUSION_PNG = MODELS_DIR / "confusion_matrix.png"


def set_seed(seed: int = SEED) -> None:
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)


def discover_classes(dataset_dir: Path = DATASET_DIR) -> list[str]:
    """Sorted sub-directory names. Sorting makes the mapping deterministic."""
    classes = sorted(p.name for p in dataset_dir.iterdir() if p.is_dir())
    if not classes:
        raise SystemExit(
            f"No class folders found in {dataset_dir}. See README.md > Dataset "
            "for how to download PlantVillage into ml/dataset/<class_name>/*.jpg"
        )
    return classes


def list_images(dataset_dir: Path, class_names: list[str]) -> tuple[list[str], list[int]]:
    paths, labels = [], []
    for idx, name in enumerate(class_names):
        for f in sorted((dataset_dir / name).rglob("*")):
            if f.suffix.lower() in IMAGE_EXTENSIONS:
                paths.append(str(f))
                labels.append(idx)
    return paths, labels


def load_split() -> dict:
    if not SPLIT_PATH.exists():
        raise SystemExit("models/dataset_split.json missing. Run `python ml/train.py` first.")
    return json.loads(SPLIT_PATH.read_text())


def decode_image(path: tf.Tensor) -> tf.Tensor:
    raw = tf.io.read_file(path)
    img = tf.io.decode_image(raw, channels=3, expand_animations=False)
    img = tf.image.resize(img, IMG_SIZE)
    return tf.cast(img, tf.float32)  # 0-255, no normalisation here


def make_dataset(paths: list[str], labels: list[int], num_classes: int,
                 training: bool, augment: tf.keras.Sequential | None = None) -> tf.data.Dataset:
    ds = tf.data.Dataset.from_tensor_slices((paths, labels))
    if training:
        ds = ds.shuffle(len(paths), seed=SEED, reshuffle_each_iteration=True)
    ds = ds.map(lambda p, y: (decode_image(p), tf.one_hot(y, num_classes)),
                num_parallel_calls=tf.data.AUTOTUNE)
    ds = ds.batch(BATCH_SIZE)
    if training and augment is not None:  # augmentation: training images only
        ds = ds.map(lambda x, y: (augment(x, training=True), y),
                    num_parallel_calls=tf.data.AUTOTUNE)
    return ds.prefetch(tf.data.AUTOTUNE)
