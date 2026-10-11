"""PlantCare AI - Flask REST API.

Run locally:   python app.py
Production:    gunicorn "app:create_app()" --workers 1 --threads 4 --timeout 120
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

from database import Database
from disease_info import get_disease_info, list_known_classes, split_class_name
from predict import ModelNotAvailable, Predictor
from preprocessing import (InvalidImageError, extension_allowed, load_image, safe_filename,
                           stored_name)

BASE_DIR = Path(__file__).resolve().parent


def _path(value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else (BASE_DIR / p).resolve()


def create_app(config: dict | None = None, predictor: Predictor | None = None) -> Flask:
    load_dotenv(BASE_DIR / ".env")
    cfg = {
        "MODEL_PATH": os.getenv("MODEL_PATH", "../models/plant_disease_model.keras"),
        "CLASS_NAMES_PATH": os.getenv("CLASS_NAMES_PATH", "../models/class_names.json"),
        "DATABASE_PATH": os.getenv("DATABASE_PATH", "plantcare.db"),
        "UPLOAD_DIR": os.getenv("UPLOAD_DIR", "uploads"),
        "MAX_UPLOAD_MB": float(os.getenv("MAX_UPLOAD_MB", "5")),
        "LOW_CONFIDENCE_THRESHOLD": float(os.getenv("LOW_CONFIDENCE_THRESHOLD", "0.60")),
        "CORS_ORIGINS": os.getenv("CORS_ORIGINS", "http://localhost:5173"),
        "SAVE_UPLOADS": os.getenv("SAVE_UPLOADS", "true").lower() == "true",
    }
    cfg.update(config or {})

    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = int(cfg["MAX_UPLOAD_MB"] * 1024 * 1024)
    origins = [o.strip() for o in str(cfg["CORS_ORIGINS"]).split(",") if o.strip()]
    CORS(app, resources={r"/api/*": {"origins": origins}})

    upload_dir = _path(cfg["UPLOAD_DIR"])
    upload_dir.mkdir(parents=True, exist_ok=True)
    db = Database(str(_path(cfg["DATABASE_PATH"])))

    if predictor is None:
        predictor = Predictor(_path(cfg["MODEL_PATH"]), _path(cfg["CLASS_NAMES_PATH"]),
                              cfg["LOW_CONFIDENCE_THRESHOLD"])
        predictor.load()  # once, at startup - never per request

    def error(message: str, status: int, **extra):
        return jsonify({"error": message, **extra}), status

    # ---------------------------------------------------------------- routes
    @app.get("/api/health")
    def health():
        return jsonify({
            "status": "ok" if predictor.ready else "degraded",
            "model_loaded": predictor.ready,
            "num_classes": len(predictor.class_names),
            "detail": None if predictor.ready else predictor.error,
        })

    @app.get("/api/diseases")
    def diseases():
        names = predictor.class_names or list_known_classes()
        items = []
        for name in names:
            info = get_disease_info(name)
            items.append({"class_name": name, **info})
        plants = sorted({i["plant"] for i in items})
        return jsonify({"plants": plants, "count": len(items), "diseases": items,
                        "model_loaded": predictor.ready})

    @app.post("/api/predict")
    def predict_route():
        if not predictor.ready:
            return error("Prediction model is not available on the server.", 503,
                         detail=predictor.error)
        file = request.files.get("image")
        if file is None or not file.filename:
            return error("No image provided. Send multipart form field 'image'.", 400)
        if not extension_allowed(file.filename):
            return error("Unsupported file type. Use JPG, JPEG or PNG.", 415)
        data = file.read()
        if not data:
            return error("Uploaded file is empty.", 400)
        try:
            img = load_image(data)
            result = predictor.predict(img)
        except InvalidImageError as exc:
            return error(str(exc), 422)
        except ModelNotAvailable as exc:
            return error("Prediction model is not available on the server.", 503, detail=str(exc))
        except Exception:
            app.logger.exception("Prediction failed")
            return error("Prediction failed due to an internal error.", 500)

        original = safe_filename(file.filename)
        ref = None
        if cfg["SAVE_UPLOADS"]:
            ref = stored_name(file.filename)
            (upload_dir / ref).write_bytes(data)
        pid = db.add_prediction(
            image_ref=ref, original_filename=original, class_name=result["class_name"],
            plant=result["plant"], disease=result["disease"],
            confidence=result["confidence"], is_healthy=result["is_healthy"])
        result["history_id"] = pid
        return jsonify(result), 200

    @app.get("/api/history")
    def history():
        try:
            limit = min(max(int(request.args.get("limit", 100)), 1), 500)
            offset = max(int(request.args.get("offset", 0)), 0)
        except ValueError:
            return error("limit and offset must be integers.", 400)
        return jsonify({"items": db.list_predictions(limit, offset)})

    @app.delete("/api/history/<int:pid>")
    def delete_history(pid: int):
        with db._conn() as c:  # fetch image ref before deleting the row
            row = c.execute("SELECT image_ref FROM predictions WHERE id = ?", (pid,)).fetchone()
        if row is None:
            return error("History record not found.", 404)
        db.delete_prediction(pid)
        if row["image_ref"]:
            (upload_dir / row["image_ref"]).unlink(missing_ok=True)
        return jsonify({"deleted": pid})

    @app.delete("/api/history")
    def clear_history():
        for ref in db.clear():
            (upload_dir / ref).unlink(missing_ok=True)
        return jsonify({"cleared": True})

    @app.get("/api/analytics")
    def analytics():
        return jsonify(db.analytics())

    # ---------------------------------------------------------------- errors
    @app.errorhandler(413)
    def too_large(_):
        return error(f"File too large. Maximum size is {cfg['MAX_UPLOAD_MB']:g} MB.", 413)

    @app.errorhandler(404)
    def not_found(_):
        return error("Endpoint not found.", 404)

    @app.errorhandler(405)
    def bad_method(_):
        return error("Method not allowed.", 405)

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
