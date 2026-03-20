FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip && \
    grep -v '^torch==' /app/requirements.txt > /app/requirements-docker.txt && \
    pip install -r /app/requirements-docker.txt && \
    pip install --index-url https://download.pytorch.org/whl/cpu torch==2.5.1

COPY api_min.py /app/
COPY APP /app/APP
COPY Model /app/Model

RUN mkdir -p /app/Docs/result /app/Docs/uploads

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "api_min:app", "--host", "0.0.0.0", "--port", "8000"]
