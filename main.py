# main.py
import os
import uuid
from fastapi import FastAPI, HTTPException, APIRouter, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import Union

from model.retriever_model import IngestRequest, RetrieveRequest
from model.extractor_model import Evidence, RetrievalOutput, ExtractionOutput, ExtractionError
from Agents.retriever import engine
from Agents.extractor import run_extraction
from utils import extract_pdf_text, fetch_and_clean_url
from redis_client import get_cached_chunk, set_cached_chunk

# =========================================================
# FastAPI setup
# =========================================================
app = FastAPI(title="Multi-Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# Helper for text extraction with Redis cache
# =========================================================
async def get_text_from_item(item):
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

    if not text_data.strip():
        raise HTTPException(400, "Text content is empty.")

    await set_cached_chunk(key, text_data)
    return text_data, meta

# =========================================================
# Routers
# =========================================================
retriever_router = APIRouter(prefix="/retriever", tags=["retriever"])
extractor_router = APIRouter(prefix="/extractor", tags=["extractor"])
pipeline_router = APIRouter(prefix="/pipeline", tags=["pipeline"])
judge_router = APIRouter(prefix="/judge", tags=["judge"])

# --- Retriever endpoints ---
@retriever_router.get("/health")
def health():
    return {
        "ok": True,
        "sources": {src: len(engine.chunks[src]) for src in engine.SOURCES},
        "model": os.getenv("EMBEDDING_MODEL", "embed-english-v3.0"),
    }

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

# --- Extractor endpoint ---
@extractor_router.post("/run", response_model=Union[ExtractionOutput, ExtractionError])
def run_extractor_endpoint(input_data: RetrievalOutput):
    return run_extraction(input_data)

# --- Pipeline endpoint ---
@pipeline_router.post("/final", response_model=Union[ExtractionOutput, ExtractionError])
async def pipeline_run(req: RetrieveRequest):
    """
    Full workflow:
    - If PDFs or URLs provided in request, use them directly.
    - Otherwise, run retriever with given section filters.
    - Clean text (remove junk, numeric noise).
    - Require at least 3 usable chunks.
    - Send cleaned evidence to extractor.
    - If no numeric data found → force descriptive test type.
    """
    import re

    all_results = []

    # --- Case 1: PDFs explicitly provided ---
    if req.pdfs:
        for pdf in req.pdfs:
            all_results.append({
                "chunk_id": pdf["doc_id"] + "_0",
                "doc_id": pdf["doc_id"],
                "title": pdf.get("title", ""),
                "text": pdf["content"],
                "meta": {"source": "pdf"}
            })

    # --- Case 2: URLs explicitly provided ---
    elif req.urls:
        for url in req.urls:
            all_results.append({
                "chunk_id": url["doc_id"] + "_0",
                "doc_id": url["doc_id"],
                "title": url.get("title", ""),
                "text": url["content"],
                "meta": {"source": "url"}
            })

    # --- Case 3: Fall back to retriever ---
    else:
        section_filters = req.section_filter
        if isinstance(section_filters, str):
            section_filters = [s.strip() for s in section_filters.split(",")]

        for src in section_filters:
            all_results.extend(
                engine.retrieve(query=req.query, k=req.k, alpha=req.alpha, source_type=src)
            )

    if not all_results:
        return ExtractionError(
            run_id=str(uuid.uuid4()),
            error="No chunks found from PDFs, URLs, or retriever",
            reason_code="MISSING_DATA"
        )

    # --- Clean & truncate ---
    cleaned_chunks = []
    for c in all_results:
        text = re.sub(
            r"(Cached - Similar pages.*|Search Preferences.*|Next Search.*)",
            "",
            c["text"],
            flags=re.IGNORECASE
        )
        text = re.sub(r"\s+", " ", text).strip()[:1000]

        if text:
            # Drop irrelevant numeric noise
            text = re.sub(r"\bISBN[- ]?\d+\b", "", text, flags=re.IGNORECASE)   # ISBN
            text = re.sub(r"\b\d{4}\b", "", text)                               # Years like 1997, 2024
            text = re.sub(r"\b\d+(\.\d+)?\s*(cm|kg|lbs|in|mm)\b", "", text)     # Dimensions/weights
            text = re.sub(r"\b[A-Z0-9]{8,}\b", "", text)                        # Product/order IDs
            text = re.sub(r"\b\d{5,}\b", "", text)                              # Large IDs

            cleaned_chunks.append({
                "chunk_id": c["chunk_id"],
                "doc_id": c["doc_id"],
                "title": c.get("title", ""),
                "text": text,
                "meta": c.get("meta", {})
            })

    if len(cleaned_chunks) < 3:
        return ExtractionError(
            run_id=str(uuid.uuid4()),
            error="Need at least 3 non-empty evidence chunks",
            reason_code="MISSING_DATA"
        )

    # --- Wrap as Evidence ---
    evidence_chunks = [
        Evidence(
            chunk_id=c["chunk_id"],
            doc_id=c["doc_id"],
            text=c["text"],
            title=c.get("title"),
            meta=c.get("meta", {})
        )
        for c in cleaned_chunks
    ]

    retrieval_output = RetrievalOutput(
        run_id=str(uuid.uuid4()),
        query=req.query,
        evidence_chunks=evidence_chunks,
        provenance={"chunks_used": len(evidence_chunks)}
    )

    # --- Guardrail: check for numeric data ---
    numeric_present = any(re.search(r"\d+", c["text"]) for c in cleaned_chunks)

    result = run_extraction(retrieval_output)

    # Force descriptive tests if no numeric data
    if isinstance(result, ExtractionOutput) and not numeric_present:
        for h in result.hypotheses:
            h["test"] = "descriptive"

    return result


# =========================================================
# Register Routers
# =========================================================
app.include_router(retriever_router)
app.include_router(extractor_router)
app.include_router(pipeline_router)
app.include_router(judge_router)

@app.get("/")
def root():
    return {"message": "Multi-Agent API running. Endpoints: /retriever, /extractor, /pipeline, /judge"}
