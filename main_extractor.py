from __future__ import annotations

from fastapi import FastAPI

from core.contracts import ExtractionError, ExtractionOutput, RetrievalOutput
from extractor import run_extraction

app = FastAPI()


@app.post("/extractor/run", response_model=ExtractionOutput | ExtractionError)
def run_extractor(input_data: RetrievalOutput):
    return run_extraction(input_data)


