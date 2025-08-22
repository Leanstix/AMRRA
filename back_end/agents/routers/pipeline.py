# Agents/Pipeline/pipeline.py
import re
import uuid
from fastapi import APIRouter
from typing import Union

from model.retriever_model import RetrieveRequest
from model.extractor_model import Evidence, RetrievalOutput, ExtractionOutput, ExtractionError
from agents.Retriever.retriever import engine
from agents.Extractor.run_extraction import run_extraction
from agents.experimentation.tasks import run_experiment_task
from agents.experimentation.models import TwoSampleInput, ExperimentOutput
from agents.judging.models import ExperimentData
from agents.judging.gpt import generate_report_json
from celery.result import AsyncResult
import time

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

@router.post("/final", response_model=Union[ExtractionOutput, ExtractionError])
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
            text = re.sub(r"\bISBN[- ]?\d+\b", "", text, flags=re.IGNORECASE)
            text = re.sub(r"\b\d{4}\b", "", text)
            text = re.sub(r"\b\d+(\.\d+)?\s*(cm|kg|lbs|in|mm)\b", "", text)
            text = re.sub(r"\b[A-Z0-9]{8,}\b", "", text)
            text = re.sub(r"\b\d{5,}\b", "", text)

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
