from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.api.runs as runs_module
from app.api.runs import router
from app.core.config import Settings
from app.infrastructure.repository import RunRepository


def test_create_run_accepts_text_and_returns_202(monkeypatch, tmp_path: Path):
    repo = RunRepository(f"sqlite:///{tmp_path / 'api.db'}")
    settings = Settings(environment="test", AGENTROUTER_API_KEY="test", EXECUTE_INLINE=False)
    monkeypatch.setattr(runs_module, "get_repository", lambda: repo)
    monkeypatch.setattr(runs_module, "get_settings", lambda: settings)
    monkeypatch.setattr(runs_module, "dispatch_run", lambda run_id, background_tasks, settings: "test")

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    client = TestClient(app)
    response = client.post(
        "/api/v1/runs",
        data={
            "query": "Does the intervention improve outcomes?",
            "text": "The study reports treatment and control outcomes.",
            "top_k": "5",
        },
    )
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert body["run_id"]
    repo.close()


def test_create_run_rejects_request_without_source(monkeypatch, tmp_path: Path):
    repo = RunRepository(f"sqlite:///{tmp_path / 'api2.db'}")
    settings = Settings(environment="test", AGENTROUTER_API_KEY="test")
    monkeypatch.setattr(runs_module, "get_repository", lambda: repo)
    monkeypatch.setattr(runs_module, "get_settings", lambda: settings)
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    response = TestClient(app).post("/api/v1/runs", data={"query": "A valid research question"})
    assert response.status_code == 422
    repo.close()


def test_get_run_and_not_found(monkeypatch, tmp_path: Path):
    repo = RunRepository(f"sqlite:///{tmp_path / 'api3.db'}")
    repo.create_run(
        "known",
        "query",
        {"query": "query", "sources": [{"kind": "text", "content": "abc"}], "top_k": 8},
    )
    monkeypatch.setattr(runs_module, "get_repository", lambda: repo)
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    client = TestClient(app)
    assert client.get("/api/v1/runs/known").status_code == 200
    assert client.get("/api/v1/runs/missing").status_code == 404
    repo.close()


def test_create_run_rejects_non_pdf_upload(monkeypatch, tmp_path: Path):
    repo = RunRepository(f"sqlite:///{tmp_path / 'api4.db'}")
    settings = Settings(environment="test", AGENTROUTER_API_KEY="test")
    monkeypatch.setattr(runs_module, "get_repository", lambda: repo)
    monkeypatch.setattr(runs_module, "get_settings", lambda: settings)
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    response = TestClient(app).post(
        "/api/v1/runs",
        data={"query": "A valid research question"},
        files={"file": ("notes.txt", b"not a pdf", "text/plain")},
    )
    assert response.status_code == 415
    repo.close()
