from urllib3 import request
from fastapi import FastAPI, Query
from celery.result import AsyncResult
from back_end.celery_app import celery_app
from .agents.experimentation.models import TwoSampleInput, ExperimentOutput
from .agents.experimentation.tasks import run_experiment_task
from .agents.experimentation.explain import gpt5_explain_results 
from .agents.judging.gpt import generate_report_json
from .agents.judging.models import ExperimentData
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Back end for the Automated Machine learning Research Reproducibility Assistant!"}

@app.post("/experiment/")
def run_experiment(input_data: TwoSampleInput):
    """
        Queue an experiment to run in the background with Celery.
    """
    task = run_experiment_task.delay(input_data.dict())
    return {"status": "queued", "task_id": task.id}

@app.get("/experiment/result/{task_id}")
def get_experiment_result(task_id: str, explain: bool = Query(True, description="Whether to include GPT-5 explanation")):
    """
        Fetch experiment result. If explain=True, also return GPT-5 interpretation.
    """
    task_result = AsyncResult(task_id, app=celery_app)

    if not task_result.ready():
        return {"status": "running"}

    if task_result.failed():
        return {"status": "failed", "error": str(task_result.result)}

    result = task_result.result  # This is the ExperimentOutput dict

    # If explanation is requested, send to GPT-5
    explanation = None
    if explain:
        explanation = gpt5_explain_results(result)

    return {
        "status": "completed",
        "result": result,
        "explanation": explanation
    }

@app.post("/generate-report-json/")
async def generate_stat_report(input_data: ExperimentData):
    """
        Accepts raw JSON data in the request body,
        uses GPT-5 to generate a structured JSON report.
    """
    report_json = await generate_report_json(input_data.result.model_dump())
    return report_json
