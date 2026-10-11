"""SQLite persistence for prediction history and analytics."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_ref TEXT,
    original_filename TEXT NOT NULL,
    class_name TEXT NOT NULL,
    plant TEXT NOT NULL,
    disease TEXT NOT NULL,
    confidence REAL NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    is_healthy INTEGER NOT NULL CHECK (is_healthy IN (0, 1)),
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_predictions_created ON predictions(created_at);
"""

COLUMNS = ("id, image_ref, original_filename, class_name, plant, disease, "
           "confidence, is_healthy, created_at")


class Database:
    def __init__(self, path: str):
        self.path = path
        self.init()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init(self) -> None:
        with self._conn() as c:
            c.executescript(SCHEMA)

    def add_prediction(self, *, image_ref: str | None, original_filename: str, class_name: str,
                       plant: str, disease: str, confidence: float, is_healthy: bool) -> int:
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO predictions (image_ref, original_filename, class_name, plant, disease,"
                " confidence, is_healthy, created_at) VALUES (?,?,?,?,?,?,?,?)",
                (image_ref, original_filename, class_name, plant, disease, float(confidence),
                 int(is_healthy), datetime.now(timezone.utc).isoformat(timespec="seconds")))
            return cur.lastrowid

    def list_predictions(self, limit: int = 100, offset: int = 0) -> list[dict]:
        with self._conn() as c:
            rows = c.execute(
                f"SELECT {COLUMNS} FROM predictions ORDER BY id DESC LIMIT ? OFFSET ?",
                (limit, offset)).fetchall()
        return [self._row(r) for r in rows]

    def get_prediction(self, pid: int) -> dict | None:
        with self._conn() as c:
            r = c.execute(f"SELECT {COLUMNS} FROM predictions WHERE id = ?", (pid,)).fetchone()
        return self._row(r) if r else None

    def delete_prediction(self, pid: int) -> bool:
        with self._conn() as c:
            return c.execute("DELETE FROM predictions WHERE id = ?", (pid,)).rowcount > 0

    def clear(self) -> list[str]:
        """Delete all rows; returns image refs so callers can remove the files."""
        with self._conn() as c:
            refs = [r["image_ref"] for r in c.execute(
                "SELECT image_ref FROM predictions WHERE image_ref IS NOT NULL")]
            c.execute("DELETE FROM predictions")
        return refs

    def analytics(self) -> dict:
        """Every number is computed from stored rows; nothing is hardcoded."""
        with self._conn() as c:
            total, healthy, avg = c.execute(
                "SELECT COUNT(*), COALESCE(SUM(is_healthy),0), AVG(confidence) FROM predictions"
            ).fetchone()
            top = c.execute(
                "SELECT class_name, plant, disease, COUNT(*) AS count FROM predictions "
                "WHERE is_healthy = 0 GROUP BY class_name ORDER BY count DESC, class_name LIMIT 5"
            ).fetchall()
            by_plant = c.execute(
                "SELECT plant, COUNT(*) AS count FROM predictions GROUP BY plant "
                "ORDER BY count DESC, plant").fetchall()
            by_day = c.execute(
                "SELECT substr(created_at,1,10) AS day, COUNT(*) AS count FROM predictions "
                "GROUP BY day ORDER BY day DESC LIMIT 14").fetchall()
            recent = c.execute(
                f"SELECT {COLUMNS} FROM predictions ORDER BY id DESC LIMIT 5").fetchall()
        return {
            "total_predictions": total,
            "healthy_count": int(healthy),
            "diseased_count": total - int(healthy),
            "average_confidence": float(avg) if avg is not None else None,
            "top_diseases": [dict(r) for r in top],
            "by_plant": [dict(r) for r in by_plant],
            "by_day": [dict(r) for r in reversed(by_day)],
            "recent": [self._row(r) for r in recent],
        }

    @staticmethod
    def _row(r: sqlite3.Row) -> dict:
        d = dict(r)
        d["is_healthy"] = bool(d["is_healthy"])
        d.pop("image_ref", None)  # internal storage name is never sent to clients
        return d
