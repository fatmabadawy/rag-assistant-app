# Backend image. Build from the REPOSITORY ROOT so rag_core/ is in context:
#   docker build -f backend/Dockerfile -t rag-backend .
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HOME=/app/.cache/huggingface

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY rag_core/ ./rag_core/
COPY backend/app/ ./app/
COPY backend/data/vector_store/ ./data/vector_store/

EXPOSE 8000

# Ollama runs on the host, not in this container. On Docker Desktop reach it with
#   -e OLLAMA_HOST=http://host.docker.internal:11434
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s \
    CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
