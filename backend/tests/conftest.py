import io
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app  # noqa: E402


class StubPredictor:
    """Test double with a deterministic result. Used ONLY in tests, never in the app."""
    ready = True
    error = None
    class_names = ["Tomato___Late_blight", "Tomato___healthy", "Apple___Apple_scab"]

    def __init__(self, healthy=False, confidence=0.93):
        self.healthy, self.confidence = healthy, confidence

    def predict(self, img, top_k=3):
        from disease_info import get_disease_info
        name = "Tomato___healthy" if self.healthy else "Tomato___Late_blight"
        info = get_disease_info(name)
        return {
            "class_name": name, "plant": "Tomato",
            "disease": "healthy" if self.healthy else "Late_blight",
            "confidence": self.confidence, "is_healthy": info["is_healthy"],
            "low_confidence": self.confidence < 0.6, "possibly_blurry": False,
            "top_predictions": [{"class_name": name, "plant": "Tomato", "disease": "x",
                                 "confidence": self.confidence}],
            "disease_info": info, "disclaimer": "test",
        }


class UnavailablePredictor:
    ready = False
    error = "Model file not found"
    class_names = []


def make_png(size=(64, 64), color=(30, 160, 60)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def client(tmp_path):
    app = create_app({"DATABASE_PATH": str(tmp_path / "t.db"), "UPLOAD_DIR": str(tmp_path / "up"),
                      "MAX_UPLOAD_MB": 1}, predictor=StubPredictor())
    return app.test_client()


@pytest.fixture
def client_no_model(tmp_path):
    app = create_app({"DATABASE_PATH": str(tmp_path / "t.db"), "UPLOAD_DIR": str(tmp_path / "up")},
                     predictor=UnavailablePredictor())
    return app.test_client()
