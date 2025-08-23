from celery_app import celery_app
from .runner import run_experiment
from .models import TwoSampleInput

@celery_app.task
def run_experiment_task(payload: dict) -> dict:
    input_data = payload if isinstance(payload, TwoSampleInput) else TwoSampleInput(**payload)
    out = run_experiment(input_data)
    return out.dict()
