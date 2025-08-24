from agents.judging.gpt import generate_report_json
from agents.judging.models import ExperimentData, ExperimentResultForJudging
from agents.judging.pdf_generator import generate_pdf_report
from fastapi import APIRouter
from fastapi.responses import FileResponse
import os

judging_router = APIRouter()

@judging_router.post("/generate-report-json/")
async def generate_stat_report(input_data: ExperimentData):
    """
        Accepts raw JSON data in the request body,
        uses GPT-5 to generate a structured JSON report.
    """
    report_json = await generate_report_json(input_data.result.model_dump())
    return report_json

@judging_router.post("/judge")
async def judge_experiment(input_data: ExperimentResultForJudging):
    """
    Accepts the result of an experiment, generates a report, and returns it as a PDF.
    """
    report_json = await generate_report_json(input_data.result.model_dump())
    
    pdf_path = "report.pdf"
    generate_pdf_report(report_json, pdf_path)
    
    return FileResponse(pdf_path, media_type='application/pdf', filename='report.pdf')