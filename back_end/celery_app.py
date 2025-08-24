from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "agents",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.autodiscover_tasks(["agents.experimentation.tasks"])
