#!/bin/sh
# PID 1 ignores SIGTERM so Celery does not warm-shutdown on scale-down.
# Tasks stay unacked until Kubernetes sends SIGKILL after grace period.
trap 'echo "SIGTERM ignored — tasks remain unacked" >&2' TERM
trap 'echo "SIGINT ignored" >&2' INT

celery -A tasks worker --loglevel=info --concurrency=4 &
wait $!
