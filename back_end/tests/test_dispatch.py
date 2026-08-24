from fastapi import BackgroundTasks

from app.core.config import Settings
from app.dispatch import dispatch_run


def test_local_dispatch_uses_background_task():
    tasks = BackgroundTasks()
    settings = Settings(environment="test", AGENTROUTER_API_KEY="test", CELERY_BROKER_URL=None)
    mode = dispatch_run("r1", tasks, settings)
    assert mode == "background"
    assert len(tasks.tasks) == 1
