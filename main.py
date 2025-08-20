import os
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import IngestRequest, RetrieveRequest, RetrieveResponse, ChunkOut
from retriever import engine
from utils import extract_pdf_text, fetch_and_clean_url

app = FastAPI(title="Retriever Agent (Hybrid RAG)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {
        "ok": True,
        "chunks_indexed": len(engine.chunks),
        "model": os.getenv("EMBEDDING_MODEL", "embed-english-v3.0"),
    }

@app.post("/ingest")
def ingest(req: IngestRequest):
    if len(req.items) != 1:
        raise HTTPException(400, "Provide exactly ONE item per ingestion.")

    item = req.items[0]
    meta = item.meta or {}
    text_data = None

    sources = [bool(item.text), bool(item.url), bool(item.file_path)]
    if sum(sources) != 1:
        raise HTTPException(400, "Provide exactly one source: text, url, or file_path per item.")

    if item.text:
        text_data = item.text
        meta.update({"source_type": "text"})
    elif item.url:
        raw_text = fetch_and_clean_url(item.url)
        if isinstance(raw_text, list):
            text_data = " ".join([p.get("text", "") for p in raw_text])
        else:
            text_data = raw_text
        if not text_data.strip():
            raise HTTPException(400, f"Empty content from URL: {item.url}")
        meta.update({"url": item.url, "source_type": "url"})
    elif item.file_path:
        if not os.path.exists(item.file_path):
            raise HTTPException(400, f"File not found: {item.file_path}")
        raw_text = extract_pdf_text(item.file_path)
        if isinstance(raw_text, list):
            text_data = " ".join([p.get("text", "") for p in raw_text])
        else:
            text_data = raw_text
        if not text_data.strip():
            raise HTTPException(400, f"PDF is empty: {item.file_path}")
        meta.update({"file": item.file_path, "source_type": "pdf"})

    result = engine.ingest_items(item.doc_id or str(uuid.uuid4()), item.title or "", text_data, meta)
    engine.save()
    return {"status": "ok", "added": result["added"], "chunks_total": result["chunks_total"]}


@app.post("/retrieve", response_model=RetrieveResponse)
def retrieve(req: RetrieveRequest):
    # determine which index to query
    source_type = req.section_filter  # now use section_filter to specify "pdf", "url", or "text"
    results = engine.retrieve(req.query, k=req.k, alpha=req.alpha, source_type=source_type)

    prov = {
    "k": req.k,
    "alpha": req.alpha,
    "embedding_model": os.getenv("EMBEDDING_MODEL", "embed-english-v3.0"),
    "chunks_indexed": len(engine.chunks),
}


    return RetrieveResponse(
        query=req.query,
        results=[ChunkOut(**r) for r in results],
        provenance=prov,
    )


@app.post("/wipe")
def wipe():
    engine.wipe()
    engine.save()
    return {"status": "ok", "message": "All chunks wiped."}
