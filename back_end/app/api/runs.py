from __future__ import annotations

import io
import uuid

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile, status
from pydantic import ValidationError
from pypdf import PdfReader

from app.core.config import get_settings
from app.dispatch import DispatchError, dispatch_run
from app.domain.schemas import RunRequest, RunSnapshot, RunStatus, SourceInput
from app.factory import build_orchestrator, get_repository

router = APIRouter(prefix="/runs", tags=["runs"])


def _extract_pdf(data: bytes, max_pages: int) -> str:
    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception as exc:
            raise ValueError("encrypted PDFs are not supported") from exc
    if len(reader.pages) > max_pages:
        raise ValueError(f"PDF exceeds the {max_pages}-page limit")
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    return " ".join(text.split())


async def _execute_run(run_id: str) -> None:
    orchestrator = build_orchestrator()
    await orchestrator.run(run_id)


@router.post("", response_model=RunSnapshot, status_code=status.HTTP_202_ACCEPTED)
async def create_run(
    background_tasks: BackgroundTasks,
    query: str = Form(...),
    url: str | None = Form(default=None),
    text: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    top_k: int = Form(default=8),
):
    settings = get_settings()
    sources: list[SourceInput] = []
    if text and text.strip():
        sources.append(
            SourceInput(
                kind="text",
                title="Submitted text",
                content=text.strip()[: settings.max_source_chars],
            )
        )
    if url and url.strip():
        sources.append(SourceInput(kind="url", title=url.strip(), url=url.strip()))
    if file is not None:
        is_pdf = file.content_type in {"application/pdf", "application/x-pdf"} or (
            file.filename or ""
        ).lower().endswith(".pdf")
        if not is_pdf:
            raise HTTPException(status_code=415, detail="Only PDF uploads are supported")
        data = await file.read(settings.max_upload_bytes + 1)
        if len(data) > settings.max_upload_bytes:
            raise HTTPException(status_code=413, detail="PDF exceeds the upload size limit")
        try:
            pdf_text = _extract_pdf(data, settings.max_pdf_pages)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Could not parse PDF: {exc}") from exc
        if not pdf_text:
            raise HTTPException(status_code=422, detail="PDF contains no extractable text")
        sources.append(
            SourceInput(
                kind="text",
                title=file.filename or "Uploaded PDF",
                content=pdf_text[: settings.max_source_chars],
            )
        )

    try:
        request = RunRequest(query=query, sources=sources, top_k=top_k)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc

    run_id = str(uuid.uuid4())
    repository = get_repository()
    repository.create_run(run_id, request.query, request.model_dump(mode="json"))

    if settings.execute_inline:
        await _execute_run(run_id)
    else:
        try:
            dispatch_run(run_id, background_tasks, settings)
        except DispatchError as exc:
            repository.set_status(
                run_id,
                RunStatus.FAILED,
                error_code="DISPATCH_FAILED",
                error_message=str(exc),
            )
            raise HTTPException(status_code=503, detail=str(exc)) from exc
    return repository.snapshot(run_id)


@router.get("/{run_id}", response_model=RunSnapshot)
def get_run(run_id: str):
    try:
        return get_repository().snapshot(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc
