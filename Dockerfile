FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN pip install --no-cache-dir uv==0.11.6

COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-install-project --no-dev || uv sync --no-dev

COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./

RUN uv pip install --system --no-deps -e .

RUN mkdir -p /data
ENV DATABASE_URL=sqlite:////data/dashboard.db

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz').read()" || exit 1

CMD ["sh", "-c", "alembic upgrade head && uvicorn dashboard.app:app --host 0.0.0.0 --port 8000"]
