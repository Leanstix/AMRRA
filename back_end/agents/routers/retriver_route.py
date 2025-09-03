from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, Form
from pydantic import BaseModel
from typing import List, Optional
import uuid, logging

from agents.Retriever.retriever import RetrieverAgent
from agents.shared.doc_store import doc_store  # ✅ unified shared store

retriever_router = APIRouter(prefix="/retriever", tags=["retriever"])
agent = RetrieverAgent()

# -----------------------------
# Ingest Endpoint (PDFs / URLs)
# -----------------------------
@retriever_router.post("/ingest")
async def ingest(
    background_tasks: BackgroundTasks,
    items: List[UploadFile] = [],
    urls: Optional[List[str]] = Form(None),
    titles: Optional[List[str]] = Form(None)
):
    if not items and not urls:
        raise HTTPException(status_code=400, detail="No PDFs or URLs provided.")

    doc_records = []

    def process_pdf(file_bytes, filename, doc_id, title):
        logging.info(f"[INGEST] Processing PDF: {filename} ({doc_id})")
        agent.ingest([{
            "doc_id": doc_id,
            "file_bytes": file_bytes,
            "title": title
        }])
        # ✅ Register in shared doc_store so tools can be built
        doc_store[doc_id] = {"type": "pdf", "title": title, "filename": filename}
        logging.info(f"[REGISTER] PDF added to doc_store: {doc_id}")

    def process_url(url, doc_id, title):
        logging.info(f"[INGEST] Processing URL: {url} ({doc_id})")
        agent.ingest([{"doc_id": doc_id, "url": url, "title": title}])
        # ✅ Register in shared doc_store
        doc_store[doc_id] = {"type": "url", "title": title, "url": url}
        logging.info(f"[REGISTER] URL added to doc_store: {doc_id}")

    # PDFs
    for i, file in enumerate(items):
        content = await file.read()
        doc_id = str(uuid.uuid4())
        title = titles[i] if titles and i < len(titles) else file.filename
        doc_records.append({"doc_id": doc_id, "title": title, "type": "pdf"})
        background_tasks.add_task(process_pdf, content, file.filename, doc_id, title)

    # URLs
    if urls:
        for i, url in enumerate(urls):
            doc_id = str(uuid.uuid4())
            title = titles[i] if titles and i < len(titles) else url
            doc_records.append({"doc_id": doc_id, "title": title, "type": "url", "url": url})
            background_tasks.add_task(process_url, url, doc_id, title)

    logging.info(f"[INGEST] Queued {len(doc_records)} docs for ingestion.")
    return {"status": "processing", "docs": doc_records}


# -----------------------------
# Retrieve Endpoint (JSON body)
# -----------------------------
class RetrieveRequest(BaseModel):
    query: str
    doc_ids: List[str]
    top_k: int = 5
    debug: bool = False
    alpha: Optional[float] = None

@retriever_router.post("/retrieve")
async def retrieve(request: RetrieveRequest):
    if not request.query or not request.doc_ids:
        raise HTTPException(status_code=400, detail="Query and doc_ids required.")

    logging.info(f"[RETRIEVE] Query='{request.query}' on docs={request.doc_ids}")

    try:
        result = agent.retrieve(
            query=request.query,
            doc_ids=request.doc_ids,
            top_k=request.top_k,
            debug=request.debug,
            alpha=request.alpha
        )
        logging.info(f"[RETRIEVE] Retrieved {len(result.evidence_chunks)} chunks for query.")
        return result.model_dump()
    except Exception as e:
        logging.error(f"[RETRIEVE] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
