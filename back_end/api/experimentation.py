from fastapi import APIRouter
from back_end.agents.experimentation.models import TwoSampleInput, ExperimentOutput
from agents.experimentation.tasks import run_experiment_task

router = APIRouter(prefix="/experiment", tags=["experimentation"])

@router.post("/", response_model=ExperimentOutput)
def experiment(input_data: TwoSampleInput):
    # For synchronous execution (dev): return run_experiment(input_data.dict()).dict()
    # For async/background via Celery:
    task = run_experiment_task.delay(input_data.dict())
    return {"test_used":"queued","conclusion":"task queued","quality_flags":[f"task_id:{task.id}"]}