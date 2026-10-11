import io

from conftest import make_png


def post_image(client, data, name="leaf.png", ctype="image/png"):
    return client.post("/api/predict", data={"image": (io.BytesIO(data), name, ctype)},
                       content_type="multipart/form-data")


def test_health_ok(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json["model_loaded"] is True


def test_health_degraded_without_model(client_no_model):
    r = client_no_model.get("/api/health")
    assert r.json["status"] == "degraded" and r.json["model_loaded"] is False


def test_predict_without_model_returns_503_not_fake_result(client_no_model):
    r = post_image(client_no_model, make_png())
    assert r.status_code == 503 and "disease" not in r.json


def test_predict_valid_image(client):
    r = post_image(client, make_png())
    assert r.status_code == 200
    body = r.json
    for key in ("plant", "disease", "confidence", "top_predictions", "disease_info", "history_id"):
        assert key in body
    assert body["disease_info"]["verification"] == "ai_generated"


def test_predict_missing_file(client):
    assert client.post("/api/predict").status_code == 400


def test_predict_wrong_extension(client):
    assert post_image(client, b"hello", name="notes.txt").status_code == 415


def test_predict_corrupt_image(client):
    assert post_image(client, b"not really a png", name="leaf.png").status_code == 422


def test_predict_png_disguised_gif_rejected(client):
    import io as _io
    from PIL import Image
    buf = _io.BytesIO()
    Image.new("RGB", (64, 64)).save(buf, format="GIF")
    assert post_image(client, buf.getvalue(), name="leaf.png").status_code == 422


def test_predict_too_small_image(client):
    assert post_image(client, make_png((8, 8))).status_code == 422


def test_predict_too_large(client):
    r = post_image(client, b"0" * (2 * 1024 * 1024))
    assert r.status_code == 413


def test_unsafe_filename_is_sanitised(client):
    post_image(client, make_png(), name="../../etc/pass wd.png")
    item = client.get("/api/history").json["items"][0]
    assert "/" not in item["original_filename"] and ".." not in item["original_filename"]


def test_history_and_delete(client):
    pid = post_image(client, make_png()).json["history_id"]
    items = client.get("/api/history").json["items"]
    assert len(items) == 1 and "image_ref" not in items[0]
    assert client.delete(f"/api/history/{pid}").status_code == 200
    assert client.get("/api/history").json["items"] == []
    assert client.delete(f"/api/history/{pid}").status_code == 404


def test_history_bad_params(client):
    assert client.get("/api/history?limit=abc").status_code == 400


def test_analytics_computed_from_records(client):
    assert client.get("/api/analytics").json["total_predictions"] == 0
    post_image(client, make_png())
    post_image(client, make_png())
    a = client.get("/api/analytics").json
    assert a["total_predictions"] == 2 and a["diseased_count"] == 2 and a["healthy_count"] == 0
    assert a["top_diseases"][0]["count"] == 2


def test_diseases_listing(client):
    r = client.get("/api/diseases")
    assert r.status_code == 200 and r.json["count"] == 3


def test_unknown_route_json_404(client):
    r = client.get("/api/nope")
    assert r.status_code == 404 and "error" in r.json
