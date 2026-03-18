FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-api.txt /app/requirements-api.txt
RUN python -m pip install --upgrade pip && \
    grep -v '^torch==' /app/requirements-api.txt > /app/requirements-api-docker.txt && \
    pip install -r /app/requirements-api-docker.txt && \
    pip install --index-url https://download.pytorch.org/whl/cpu torch==2.5.1

COPY api_min.py crud.py db.py models.py /app/
COPY Model /app/Model

RUN mkdir -p /app/Result/api_result /app/Result/uploads

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "api_min:app", "--host", "0.0.0.0", "--port", "8000"]
