"""Evaluate saved model(s) on the held-out test split created by train.py.

Usage:
    python ml/evaluate.py
Writes models/evaluation_report.json and models/confusion_matrix.png.
Reported numbers are measured on the test set only.
"""
from __future__ import annotations

import json

import numpy as np
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             precision_recall_fscore_support)
from tensorflow import keras

from common import (BASELINE_PATH, CLASS_NAMES_PATH, CONFUSION_PNG, MODEL_PATH, REPORT_PATH,
                    load_split, make_dataset)


def evaluate_model(model, paths, labels, num_classes):
    ds = make_dataset(paths, labels, num_classes, training=False)
    probs = model.predict(ds, verbose=1)
    pred = probs.argmax(axis=1)
    p, r, f1, _ = precision_recall_fscore_support(labels, pred, average="macro", zero_division=0)
    return pred, {
        "accuracy": float(accuracy_score(labels, pred)),
        "macro_precision": float(p),
        "macro_recall": float(r),
        "macro_f1": float(f1),
    }


def save_confusion_plot(cm: np.ndarray, class_names: list[str]) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    size = max(8, len(class_names) * 0.35)
    fig, ax = plt.subplots(figsize=(size, size))
    ax.imshow(cm, cmap="Greens")
    ax.set_xticks(range(len(class_names)), class_names, rotation=90, fontsize=6)
    ax.set_yticks(range(len(class_names)), class_names, fontsize=6)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title("Confusion matrix (test set)")
    fig.tight_layout()
    fig.savefig(CONFUSION_PNG, dpi=150)
    plt.close(fig)


def main() -> None:
    class_names = json.loads(CLASS_NAMES_PATH.read_text())
    split = load_split()["test"]
    paths, labels = split["paths"], split["labels"]
    n = len(class_names)
    print(f"Test images: {len(paths)}")

    report: dict = {"test_samples": len(paths), "num_classes": n}

    model = keras.models.load_model(MODEL_PATH)
    pred, metrics = evaluate_model(model, paths, labels, n)
    report["transfer_model"] = metrics
    report["per_class"] = classification_report(
        labels, pred, labels=list(range(n)), target_names=class_names,
        output_dict=True, zero_division=0)
    cm = confusion_matrix(labels, pred, labels=list(range(n)))
    report["confusion_matrix"] = cm.tolist()
    save_confusion_plot(cm, class_names)

    if BASELINE_PATH.exists():
        _, base_metrics = evaluate_model(keras.models.load_model(BASELINE_PATH), paths, labels, n)
        report["baseline_cnn"] = base_metrics

    REPORT_PATH.write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items()
                      if k in ("transfer_model", "baseline_cnn")}, indent=2))
    print(f"Saved {REPORT_PATH} and {CONFUSION_PNG}")


if __name__ == "__main__":
    main()
