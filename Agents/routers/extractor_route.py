# extractor.py
from fastapi import APIRouter
from typing import Union

from model.extractor_model import RetrievalOutput, ExtractionOutput, ExtractionError
from Agents.Extractor.run_extraction import run_extraction

extractor_router = APIRouter(prefix="/extractor", tags=["extractor"])

@extractor_router.post("/run", response_model=Union[ExtractionOutput, ExtractionError])
def run_extractor_endpoint(input_data: RetrievalOutput):
    """
    Endpoint to run the extraction workflow on given evidence chunks.
    Expects RetrievalOutput containing evidence_chunks (PDFs, URLs, or text).
    """
    return run_extraction(input_data)
