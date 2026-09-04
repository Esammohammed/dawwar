FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Nothing ever calls into this service — it only calls out to news sites and
# in to the Django backend — so the CMD runs the scheduler loop directly.
# No FastAPI/uvicorn stub (unlike scraper/'s Dockerfile, which points at a
# main:app that doesn't exist).
CMD ["python", "scheduler.py"]
