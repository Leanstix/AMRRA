from agents.judging.gpt import generate_report_json
from agents.judging.models import ExperimentData
from fastapi import APIRouter

judging_router = APIRouter()

@judging_router.post("/generate-report-json/")
async def generate_stat_report(input_data: ExperimentData):
    """
        Accepts raw JSON data in the request body,
        uses GPT-5 to generate a structured JSON report.
    """
    report_json = await generate_report_json(input_data.result.model_dump())
    return report_json