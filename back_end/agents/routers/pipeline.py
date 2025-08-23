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
from celery_app import celery_app
import time

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

def map_extraction_to_experiment_input(hypothesis_obj):
    return {
        "hypothesis": hypothesis_obj["hypothesis"],
        "test": hypothesis_obj.get("test", "ttest"),
        "alpha": 0.05,
        "groups_raw": [
            {"name": g["name"], "values": g["data"]} for g in hypothesis_obj.get("groups_raw", [])
        ]
    }

@router.post("/final", response_model=dict)
async def pipeline_run(req: RetrieveRequest):
    """
    Full pipeline:
    1. Retrieve and clean text (PDFs, URLs, or retriever).
    2. Extract hypotheses and structured data.
    3. For each hypothesis, run experiment via Celery.
    4. Pass all experiment results to judging agent for final report.
    """
    all_results = []

    # --- Step 1: Collect raw chunks ---
    if req.pdfs:
        for pdf in req.pdfs:
            all_results.append({
                "chunk_id": pdf["doc_id"] + "_0",
                "doc_id": pdf["doc_id"],
                "title": pdf.get("title", ""),
                "text": pdf["content"],
                "meta": {"source": "pdf"}
            })

    elif req.urls:
        for url in req.urls:
            all_results.append({
                "chunk_id": url["doc_id"] + "_0",
                "doc_id": url["doc_id"],
                "title": url.get("title", ""),
                "text": url["content"],
                "meta": {"source": "url"}
            })

    else:
        section_filters = req.section_filter
        if isinstance(section_filters, str):
            section_filters = [s.strip() for s in section_filters.split(",")]

        for src in section_filters:
            all_results.extend(
                engine.retrieve(query=req.query, k=req.k, alpha=req.alpha, source_type=src)
            )

    if not all_results:
        return {
            "status": "error",
            "error": "No chunks found from PDFs, URLs, or retriever",
            "reason_code": "MISSING_DATA"
        }

    # --- Step 2: Clean chunks ---
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
        return {
            "status": "error",
            "error": "Need at least 3 non-empty evidence chunks",
            "reason_code": "MISSING_DATA"
        }

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

    numeric_present = any(re.search(r"\d+", c["text"]) for c in cleaned_chunks)

    # --- Step 3: Run extraction agent ---
    extraction_result = run_extraction(retrieval_output)

    if isinstance(extraction_result, ExtractionOutput) and not numeric_present:
        for h in extraction_result.hypotheses:
            h["test"] = "descriptive"

    # --- Step 4: Run experimentation for each hypothesis ---
    experiment_results = []
    if isinstance(extraction_result, ExtractionOutput):
        for hypothesis in extraction_result.hypotheses:
            experiment_input = map_extraction_to_experiment_input(hypothesis)

            task = run_experiment_task.apply_async(args=[experiment_input])
            timeout = 60  # seconds
            start = time.time()

            while not task.ready():
                if time.time() - start > timeout:
                    return {
                        "status": "error",
                        "error": "Experiment timed out",
                        "hypothesis": hypothesis.get("hypothesis")
                    }
                time.sleep(2)

            if task.failed():
                experiment_results.append({
                    "hypothesis": hypothesis.get("hypothesis"),
                    "status": "failed",
                    "error": str(task.result)
                })
            else:
                result: ExperimentOutput = task.result
                experiment_results.append(result)

    # --- Step 5: Judging agent for final structured report ---
    final_report = await generate_report_json({"experiments": experiment_results})

    return {
        "status": "completed",
        "retrieval_output": retrieval_output.model_dump(),
        "extraction_output": extraction_result.model_dump() if isinstance(extraction_result, ExtractionOutput) else {},
        "experiments": experiment_results,
        "final_report": final_report
    }
