FROM node:20-alpine AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --no-audit --no-fund
COPY frontend ./
ARG USER_SLUG=robert
ARG BRAWLER_SUBJECT=englisch
ARG API_BASE=
ARG PUBLIC_DEV_TOKEN=
ENV USER_SLUG=$USER_SLUG \
    BRAWLER_SUBJECT=$BRAWLER_SUBJECT \
    API_BASE=$API_BASE \
    PUBLIC_DEV_TOKEN=$PUBLIC_DEV_TOKEN
RUN npm run build


FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml uv.lock* README.md ./
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./

RUN pip install --no-cache-dir \
    "fastapi>=0.115.0" \
    "uvicorn[standard]>=0.32.0" \
    "sqlalchemy>=2.0.36" \
    "alembic>=1.14.0" \
    "pydantic>=2.9.0" \
    "pydantic-settings>=2.6.0" \
    "python-jose[cryptography]>=3.3.0" \
    "pyyaml>=6.0.2" \
    "httpx>=0.28.0" \
 && pip install --no-cache-dir --no-deps -e .

COPY --from=frontend /frontend/dist ./frontend/dist
COPY assets ./assets

RUN mkdir -p /data
ENV DATABASE_URL=sqlite:////data/dashboard.db \
    FRONTEND_DIST=/app/frontend/dist \
    ASSETS_DIR=/app/assets

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz').read()" || exit 1

CMD ["sh", "-c", "alembic upgrade head && uvicorn dashboard.app:app --host 0.0.0.0 --port 8000"]
