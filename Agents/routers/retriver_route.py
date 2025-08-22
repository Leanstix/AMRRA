# Agents/Retriever/retriever.py
import os
import uuid
from fastapi import APIRouter, HTTPException, BackgroundTasks
from model.retriever_model import IngestRequest
from Agents.Retriever.utils import extract_pdf_text, fetch_and_clean_url
from redis_client import get_cached_chunk, set_cached_chunk
from Agents.Retriever.retriever import engine  # your ingestion engine

retriever_router = APIRouter(prefix="/retriever", tags=["retriever"])

@retriever_router.get("/health")
def health():
    return {
        "ok": True,
        "sources": {src: len(engine.chunks[src]) for src in engine.SOURCES},
        "model": os.getenv("EMBEDDING_MODEL", "embed-english-v3.0"),
    }

async def get_text_from_item(item):
    """Helper to fetch text from PDF, URL, or raw text, with Redis caching."""
    key = item.doc_id or item.url or item.file_path
    cached = await get_cached_chunk(key)
    if cached:
        return cached, {"source_type": "text" if getattr(item, "text", None) else "url" if getattr(item, "url", None) else "pdf"}

    if getattr(item, "text", None):
        text_data = item.text.strip()
        meta = {"source_type": "text"}
    elif getattr(item, "url", None):
        raw = fetch_and_clean_url(item.url)
        text_data = " ".join([p.get("text", "") for p in raw]) if isinstance(raw, list) else raw or ""
        meta = {"source_type": "url", "url": item.url}
    elif getattr(item, "file_path", None):
        raw = extract_pdf_text(item.file_path)
        text_data = " ".join([p.get("text", "") for p in raw]) if isinstance(raw, list) else raw or ""
        meta = {"source_type": "pdf", "file": item.file_path}
    else:
        raise HTTPException(400, "Provide text, URL, or file_path.")

    await set_cached_chunk(key, text_data)
    return text_data, meta

@retriever_router.post("/ingest")
async def ingest(req: IngestRequest, background_tasks: BackgroundTasks):
    if not req.items:
        raise HTTPException(400, "No items provided.")

    async def process_batch():
        batch = {"pdf": [], "url": [], "text": []}
        for item in req.items:
            text_data, meta = await get_text_from_item(item)
            batch[meta["source_type"]].append({
                "doc_id": item.doc_id or str(uuid.uuid4()),
                "title": item.title or "",
                "text": text_data,
                "meta": meta,
            })
        for src, items in batch.items():
            if items:
                engine.ingest_batch(items, source_type=src)
        engine.save()

    background_tasks.add_task(process_batch)
    return {"status": "processing"}
