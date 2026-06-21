FROM python:3.12-slim

WORKDIR /app
RUN pip install --no-cache-dir "celery[amqp]==5.4.0"
COPY tasks.py producer.py worker-entrypoint.sh ./
RUN chmod +x worker-entrypoint.sh

CMD ["./worker-entrypoint.sh"]
