"""
fitglyph-ml — FastAPI ML microservice for FitGlyph.

Exposes:
  - ACWR / fatigue engine  →  /api/ml/fatigue/*
  - Bayesian 1RM estimator →  /api/ml/bayesian/*  (stub)
  - RAG exercise guide     →  /api/ml/rag/*       (stub)

Port: 8001  (main Flask app runs on 8000)
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from fatigue.compute import router as fatigue_router
from bayesian.one_rm import router as bayesian_router
from rag.query import router as rag_router

load_dotenv()

SERVICE_KEY = os.getenv("SERVICE_KEY", "dev-key")
_ALLOWED_HOSTS = {"127.0.0.1", "::1", "localhost"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-ingest corpus on first boot (when ChromaDB collection is empty)
    try:
        from rag.ingest import get_collection, ingest_corpus
        col = get_collection()
        if col.count() == 0:
            print("[startup] ChromaDB collection empty — running corpus ingest...")
            ingest_corpus()
    except Exception as exc:
        print(f"[startup] RAG ingest skipped: {exc}")
    yield


app = FastAPI(title="fitglyph-ml", version="0.1.0", lifespan=lifespan)


@app.middleware("http")
async def enforce_auth(request: Request, call_next):
    """
    Restrict access to localhost or callers presenting the correct service key.
    In dev both conditions are permissive by default; tighten SERVICE_KEY in prod.
    """
    client_host = request.client.host if request.client else ""
    service_key = request.headers.get("X-Service-Key", "")
    host_ok = client_host in _ALLOWED_HOSTS
    key_ok = service_key == SERVICE_KEY

    if not (host_ok or key_ok):
        return JSONResponse(
            status_code=403,
            content={"error": "forbidden", "message": "Access restricted to localhost or valid service key."},
        )
    return await call_next(request)


@app.get("/health")
def health():
    return {"status": "ok", "service": "fitglyph-ml", "port": 8001}


app.include_router(fatigue_router, prefix="/api/ml/fatigue")
app.include_router(bayesian_router, prefix="/api/ml/bayesian")
app.include_router(rag_router, prefix="/api/ml/rag")
