from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.runs import router as runs_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="AMRRA Agent API",
    version="2.0.0",
    description="Automated Machine Learning Research Reproducibility Assistant",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(runs_router, prefix=settings.api_prefix)


@app.get("/")
def root():
    return {"name": settings.app_name, "version": "2.0.0", "docs": "/docs"}
