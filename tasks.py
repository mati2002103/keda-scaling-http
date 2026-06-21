import os
import time
import random

from celery import Celery

BROKER_URL = os.environ.get("CELERY_BROKER_URL", "amqp://poc:poc@rabbitmq:5672//")

app = Celery("poc", broker=BROKER_URL)

app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
)


@app.task(name="poc.process")
def process(n):
    max_sec = int(os.environ.get("TASK_DURATION_MAX_SEC", "180"))
    min_sec = int(os.environ.get("TASK_DURATION_MIN_SEC", "60"))
    duration = random.uniform(min_sec, max_sec)
    elapsed = 0
    while elapsed < duration:
        chunk = min(15, duration - elapsed)
        time.sleep(chunk)
        elapsed += chunk
        print(f"task {n}: still running ({elapsed:.0f}/{duration:.0f}s)", flush=True)
    return {"n": n, "slept": round(duration, 1)}
