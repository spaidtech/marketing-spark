FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1

COPY backend/requirements.txt /tmp/requirements.txt
COPY backend/common /app/backend/common
COPY backend/billing-service /app/backend/billing-service

RUN pip install --no-cache-dir -r /tmp/requirements.txt && \
    pip install --no-cache-dir -e /app/backend/common

WORKDIR /app/backend/billing-service
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]

