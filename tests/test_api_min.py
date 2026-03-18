import io
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import api_min


@pytest.fixture
def client(tmp_path, monkeypatch):
    result_dir = tmp_path / "api_result"
    upload_dir = tmp_path / "uploads"
    db_path = tmp_path / "jobs.db"

    monkeypatch.setattr(api_min, "RESULT_DIR", str(result_dir))
    monkeypatch.setattr(api_min, "UPLOAD_DIR", str(upload_dir))
    monkeypatch.setattr(api_min, "DB_PATH", str(db_path))

    def fake_run_predict(ct_path: str, output_name=None) -> str:
        out_name = output_name if output_name else f"result-{Path(ct_path).name}"
        out_path = result_dir / out_name
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(b"dummy-result")
        return str(out_path)

    monkeypatch.setattr(api_min, "run_predict", fake_run_predict)

    def fake_startup():
        result_dir.mkdir(parents=True, exist_ok=True)
        upload_dir.mkdir(parents=True, exist_ok=True)
        api_min.db.init_db(api_min.DB_PATH)
        api_min.model = object()

    monkeypatch.setattr(api_min, "_startup_init", fake_startup)

    with TestClient(api_min.app) as test_client:
        yield test_client


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_predict_upload(client):
    resp = client.post(
        "/predict",
        files={"file": ("volume-40.nii", io.BytesIO(b"dummy-ct"), "application/octet-stream")},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "volume-40.nii"
    assert isinstance(data["elapsed_ms"], int)
    assert data["elapsed_ms"] >= 0

    result_path = Path(data["result_path"])
    assert result_path.exists()


def test_jobs_submit_and_poll(client):
    submit_resp = client.post(
        "/jobs",
        files={"file": ("volume-40.nii", io.BytesIO(b"dummy-ct"), "application/octet-stream")},
    )

    assert submit_resp.status_code == 200
    submit_data = submit_resp.json()
    assert "job_id" in submit_data
    job_id = submit_data["job_id"]

    final = None
    deadline = time.time() + 5
    while time.time() < deadline:
        poll_resp = client.get(f"/jobs/{job_id}")
        assert poll_resp.status_code == 200
        job = poll_resp.json()
        if job["status"] in {"succeeded", "failed"}:
            final = job
            break
        time.sleep(0.05)

    assert final is not None, "job polling timed out"
    assert final["status"] == "succeeded"
    assert final["error"] is None
    assert isinstance(final["elapsed_ms"], int)
    assert final["elapsed_ms"] >= 0
    assert Path(final["result_path"]).exists()


def test_job_not_found(client):
    resp = client.get("/jobs/not_exists")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "job not found"
