from agents.experimentation.models import TwoSampleInput, ExperimentOutput
from agents.experimentation.tasks import run_experiment_task
from agents.experimentation.explain import gpt5_explain_results
from celery_app import celery_app
from celery.result import AsyncResult
from fastapi import APIRouter, Query

experimentation_router = APIRouter()

@experimentation_router.post("/experiment/")
def run_experiment(input_data: TwoSampleInput):
    """
        Queue an experiment to run in the background with Celery.
    """
    task = run_experiment_task.delay(input_data.dict())
    return {"status": "queued", "task_id": task.id}

@experimentation_router.get("/experiment/result/{task_id}")
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
