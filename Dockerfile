# Dockerfile — Nextfarm AI Production Container
# Base image Python 3.11-slim on dinh, nhe va tuong thich cao voi PyTorch & pgvector
FROM python:3.11-slim as base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    APP_ENV=production \
    PORT=8000

WORKDIR /app

# Cai dat dependencies he thong can thiet cho psycopg, build C-extensions va healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Cai dat cac goi Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir \
       sentence-transformers==3.3.1 \
       google-genai==2.19.0 \
       httpx==0.28.1

# Tao user non-root de tang cuong bao mat theo tieu chuan enterprise
RUN groupadd -r nextfarm && useradd -r -g nextfarm -d /app -s /sbin/nologin nextfarm

# Copy ma nguon ung dung, tri thuc va frontend
COPY app/ /app/app/
COPY frontend/ /app/frontend/
COPY knowledge/ /app/knowledge/
COPY db/ /app/db/
COPY evaluation/results/ /app/evaluation/results/
COPY docs/PHIEU_CHAM_CHUYEN_GIA.md /app/docs/PHIEU_CHAM_CHUYEN_GIA.md

# Pre-cache model embedding local de container san sang chay offline / khoi dong nhanh
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('bkai-foundation-models/vietnamese-bi-encoder')" || true

RUN chown -R nextfarm:nextfarm /app

USER nextfarm

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
