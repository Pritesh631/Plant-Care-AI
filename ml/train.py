"""Train a baseline CNN and a MobileNetV2 transfer-learning model.

Usage (from repo root):
    python ml/train.py --epochs 10 --fine-tune-epochs 5
    python ml/train.py --skip-baseline        # faster

Expected dataset layout (PlantVillage, folder-per-class):
    ml/dataset/Tomato___Early_blight/*.jpg
    ml/dataset/Tomato___healthy/*.jpg
    ...
Class folder names follow PlantVillage's "Plant___Condition" convention.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter

import tensorflow as tf
from sklearn.model_selection import train_test_split
from tensorflow import keras
from tensorflow.keras import layers

from common import (BASELINE_PATH, BATCH_SIZE, CLASS_NAMES_PATH, DATASET_DIR, HISTORY_PATH,
                    IMG_SIZE, MODEL_PATH, MODELS_DIR, SEED, SPLIT_PATH, discover_classes,
                    list_images, make_dataset, set_seed)


def inspect_dataset(paths: list[str], labels: list[int], class_names: list[str]) -> None:
    counts = Counter(labels)
    print(f"\nDataset: {len(paths)} images, {len(class_names)} classes")
    for idx, name in enumerate(class_names):
        print(f"  {name:55s} {counts[idx]:6d}")
    # Quick image-quality check on a sample: flag unreadable files.
    bad = 0
    for p in paths[:: max(1, len(paths) // 500)]:
        try:
            tf.io.decode_image(tf.io.read_file(p), channels=3, expand_animations=False)
        except Exception:
            bad += 1
            print(f"  WARNING unreadable image: {p}")
    print(f"Sampled readability check: {bad} unreadable file(s)\n")


def stratified_split(paths, labels, val_frac=0.15, test_frac=0.15):
    """Split by file so no image appears in two sets (no leakage)."""
    p_train, p_tmp, y_train, y_tmp = train_test_split(
        paths, labels, test_size=val_frac + test_frac, stratify=labels, random_state=SEED)
    rel_test = test_frac / (val_frac + test_frac)
    p_val, p_test, y_val, y_test = train_test_split(
        p_tmp, y_tmp, test_size=rel_test, stratify=y_tmp, random_state=SEED)
    assert not (set(p_train) & set(p_val) | set(p_train) & set(p_test) | set(p_val) & set(p_test))
    return (p_train, y_train), (p_val, y_val), (p_test, y_test)


def augmentation() -> keras.Sequential:
    return keras.Sequential([
        layers.RandomFlip("horizontal_and_vertical"),
        layers.RandomRotation(0.1),
        layers.RandomZoom(0.1),
        layers.RandomContrast(0.1),
    ], name="augmentation")


def build_baseline(num_classes: int) -> keras.Model:
    inp = keras.Input(shape=IMG_SIZE + (3,))
    x = layers.Rescaling(1.0 / 127.5, offset=-1)(inp)
    for filters in (32, 64, 128):
        x = layers.Conv2D(filters, 3, activation="relu", padding="same")(x)
        x = layers.MaxPooling2D()(x)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.4)(x)
    out = layers.Dense(num_classes, activation="softmax")(x)
    return keras.Model(inp, out, name="baseline_cnn")


def build_transfer(num_classes: int) -> tuple[keras.Model, keras.Model]:
    base = keras.applications.MobileNetV2(
        input_shape=IMG_SIZE + (3,), include_top=False, weights="imagenet")
    base.trainable = False
    inp = keras.Input(shape=IMG_SIZE + (3,))
    # Normalisation lives inside the model: inference feeds raw 0-255 pixels.
    x = layers.Rescaling(1.0 / 127.5, offset=-1)(inp)
    x = base(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.3)(x)
    out = layers.Dense(num_classes, activation="softmax")(x)
    return keras.Model(inp, out, name="plantcare_mobilenetv2"), base


def callbacks(checkpoint_path: str) -> list:
    return [
        keras.callbacks.EarlyStopping(monitor="val_loss", patience=3, restore_best_weights=True),
        keras.callbacks.ModelCheckpoint(checkpoint_path, monitor="val_loss", save_best_only=True),
        keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=2),
    ]


def compile_model(model: keras.Model, lr: float) -> None:
    model.compile(optimizer=keras.optimizers.Adam(lr), loss="categorical_crossentropy",
                  metrics=["accuracy"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--fine-tune-epochs", type=int, default=5)
    ap.add_argument("--unfreeze-layers", type=int, default=30,
                    help="Number of top MobileNetV2 layers to unfreeze for fine-tuning")
    ap.add_argument("--skip-baseline", action="store_true")
    args = ap.parse_args()

    set_seed()
    MODELS_DIR.mkdir(exist_ok=True)
    class_names = discover_classes(DATASET_DIR)
    paths, labels = list_images(DATASET_DIR, class_names)
    inspect_dataset(paths, labels, class_names)

    (p_tr, y_tr), (p_va, y_va), (p_te, y_te) = stratified_split(paths, labels)
    n = len(class_names)
    # Single source of truth for label mapping, reused by evaluate.py and the API.
    CLASS_NAMES_PATH.write_text(json.dumps(class_names, indent=2))
    SPLIT_PATH.write_text(json.dumps({"test": {"paths": p_te, "labels": y_te}}))
    print(f"Split: train={len(p_tr)} val={len(p_va)} test={len(p_te)}")

    train_ds = make_dataset(p_tr, y_tr, n, training=True, augment=augmentation())
    val_ds = make_dataset(p_va, y_va, n, training=False)

    history: dict = {}

    if not args.skip_baseline:
        print("\n== Phase 0: baseline CNN ==")
        baseline = build_baseline(n)
        compile_model(baseline, 1e-3)
        h = baseline.fit(train_ds, validation_data=val_ds, epochs=args.epochs,
                         callbacks=callbacks(str(BASELINE_PATH)))
        history["baseline"] = h.history

    print("\n== Phase 1: MobileNetV2, frozen base ==")
    model, base = build_transfer(n)
    compile_model(model, 1e-3)
    h1 = model.fit(train_ds, validation_data=val_ds, epochs=args.epochs,
                   callbacks=callbacks(str(MODEL_PATH)))
    history["transfer_frozen"] = h1.history

    if args.fine_tune_epochs > 0:
        print(f"\n== Phase 2: fine-tune top {args.unfreeze_layers} base layers ==")
        base.trainable = True
        for layer in base.layers[:-args.unfreeze_layers]:
            layer.trainable = False
        for layer in base.layers:  # keep BatchNorm statistics frozen
            if isinstance(layer, layers.BatchNormalization):
                layer.trainable = False
        compile_model(model, 1e-5)
        h2 = model.fit(train_ds, validation_data=val_ds, epochs=args.fine_tune_epochs,
                       callbacks=callbacks(str(MODEL_PATH)))
        history["transfer_finetune"] = h2.history

    # Checkpoint holds the best val_loss weights across both phases' last save.
    model.save(MODEL_PATH)
    HISTORY_PATH.write_text(json.dumps(
        {k: {m: [float(x) for x in v] for m, v in d.items()} for k, d in history.items()},
        indent=2))
    print(f"\nSaved model -> {MODEL_PATH}\nNext: python ml/evaluate.py")


if __name__ == "__main__":
    main()
