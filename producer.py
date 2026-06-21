import os
import socket
import sys
import time
from urllib.parse import urlparse

from tasks import app

BROKER_URL = os.environ.get("CELERY_BROKER_URL", "amqp://guest:guest@rabbitmq:5672//")
WAIT_SEC = int(os.environ.get("BROKER_WAIT_SEC", "120"))
RETRY_SEC = float(os.environ.get("BROKER_RETRY_SEC", "2"))


def wait_for_broker(url: str, timeout_sec: int) -> None:
    parsed = urlparse(url)
    host = parsed.hostname or "rabbitmq"
    port = parsed.port or 5672
    deadline = time.time() + timeout_sec

    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=2):
                print(f"Broker reachable at {host}:{port}", flush=True)
                return
        except OSError as exc:
            print(f"Waiting for broker {host}:{port}: {exc}", flush=True)
            time.sleep(RETRY_SEC)

    raise TimeoutError(f"Broker not reachable at {host}:{port} after {timeout_sec}s")


wait_for_broker(BROKER_URL, WAIT_SEC)

count = int(sys.argv[1]) if len(sys.argv) > 1 else 16

for i in range(count):
    app.send_task("poc.process", args=[i])

print(f"Enqueued {count} tasks to {BROKER_URL}", flush=True)
