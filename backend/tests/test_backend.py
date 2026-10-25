import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from fastapi.testclient import TestClient
import router
from main import app, DB

client = TestClient(app)
AUTH = {"Authorization": "Bearer change-me"}
WAV = b"RIFF" + b"\x00" * 64000


def test_tags_always_use_fast_model():
    assert router.pick_tier("tag", "word " * 5000) == "fast"


def test_summary_tier_depends_on_length():
    assert router.pick_tier("summary", "word " * 100) == "fast"
    assert router.pick_tier("summary", "word " * 2000) == "strong"


def test_router_falls_back_when_provider_fails():
    calls = []
    def flaky(tier, prompt):
        calls.append(tier)
        if tier == "fast":
            raise RuntimeError("down")
        return "ok"
    answer, model = router.run("summary", "short text", "p", caller=flaky)
    assert answer == "ok" and calls == ["fast", "strong"] and model == router.MODELS["strong"]


def test_router_raises_when_everything_fails():
    def dead(tier, prompt): raise RuntimeError("down")
    try:
        router.run("summary", "x", "p", caller=dead)
        assert False
    except RuntimeError:
        pass


def test_upload_requires_token():
    assert client.post("/api/upload", content=WAV).status_code == 401


def test_upload_and_bookmarks_and_search():
    DB.clear()
    r = client.post("/api/upload", content=WAV, headers={**AUTH, "X-Device-Id": "pendant-01", "X-Bookmarks": "3.5,12.0"})
    assert r.status_code == 200
    rec = client.get("/api/recordings", headers=AUTH).json()[0]
    assert rec["bookmarks"] == [3.5, 12.0] and rec["device_id"] == "pendant-01" and rec["duration_s"] > 1
    assert len(client.get("/api/search", params={"q": "budget"}, headers=AUTH).json()) == 1
    assert client.get("/api/search", params={"q": "zebra"}, headers=AUTH).json() == []


def test_tiny_upload_rejected_and_delete_everything():
    assert client.post("/api/upload", content=b"x", headers=AUTH).status_code == 400
    client.post("/api/upload", content=WAV, headers=AUTH)
    assert client.delete("/api/recordings", headers=AUTH).json() == {"ok": True}
    assert client.get("/api/recordings", headers=AUTH).json() == []
