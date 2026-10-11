import json
from pathlib import Path

import numpy as np
import pytest

from conftest import make_png
from database import Database
from disease_info import get_disease_info, is_healthy_class, list_known_classes, split_class_name
from preprocessing import InvalidImageError, load_image, safe_filename


def test_split_class_name():
    assert split_class_name("Tomato___Late_blight") == ("Tomato", "Late blight")
    assert split_class_name("Pepper,_bell___Bacterial_spot")[0] == "Pepper bell"


def test_healthy_detection_and_unknown_class_not_fabricated():
    assert is_healthy_class("Apple___healthy")
    info = get_disease_info("Mystery___Blight")
    assert info["info_available"] is False and info["symptoms"] == []


def test_all_known_diseases_have_required_fields_and_no_dosages():
    for name in list_known_classes():
        info = get_disease_info(name)
        for field in ("symptoms", "causes", "prevention", "treatment", "crop_care"):
            assert info[field], f"{name} missing {field}"
        text = json.dumps(info).lower()
        assert " ml/" not in text and " g/l" not in text and "per litre" not in text


def test_safe_filename():
    assert safe_filename("../../a b.png") == "a_b.png"


def test_load_image_rejects_garbage():
    with pytest.raises(InvalidImageError):
        load_image(b"junk")


def test_database_roundtrip(tmp_path):
    db = Database(str(tmp_path / "x.db"))
    pid = db.add_prediction(image_ref="a.png", original_filename="a.png", class_name="Apple___healthy",
                            plant="Apple", disease="healthy", confidence=0.9, is_healthy=True)
    assert db.get_prediction(pid)["is_healthy"] is True
    assert db.analytics()["healthy_count"] == 1
    assert db.clear() == ["a.png"] and db.list_predictions() == []


def test_database_rejects_invalid_confidence(tmp_path):
    import sqlite3
    db = Database(str(tmp_path / "x.db"))
    with pytest.raises(sqlite3.IntegrityError):
        db.add_prediction(image_ref=None, original_filename="a", class_name="c", plant="p",
                          disease="d", confidence=1.5, is_healthy=False)


def test_preprocess_matches_training_pipeline(tmp_path):
    """Backend preprocessing must equal ml/common.py::decode_image on the same file."""
    tf = pytest.importorskip("tensorflow")
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ml"))
    from common import decode_image
    from preprocessing import preprocess

    rng = np.random.default_rng(0)
    from PIL import Image
    p = tmp_path / "leaf.png"
    Image.fromarray(rng.integers(0, 255, (300, 400, 3), dtype=np.uint8)).save(p)
    train_side = decode_image(tf.constant(str(p))).numpy()
    infer_side = preprocess(load_image(p.read_bytes()))[0]
    assert infer_side.shape == (224, 224, 3)
    assert np.allclose(train_side, infer_side, atol=1e-3)
