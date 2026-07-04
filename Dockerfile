FROM python:3.12-slim AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

RUN groupadd -r ohagent && useradd -r -g ohagent ohagent

# Install dependencies only (cached layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

FROM base AS runtime

COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY knowledge_base/ ./knowledge_base/

RUN uv sync --frozen --no-dev \
    && mkdir -p logs data/chroma data/logs \
    && chown -R ohagent:ohagent /app

USER ohagent

ENV PATH="/app/.venv/bin:$PATH"
ENV PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
    CMD python -c "import os, httpx; port=os.environ.get('PORT','8000'); r=httpx.get(f'http://localhost:{port}/health'); r.raise_for_status()"

CMD ["sh", "-c", "uvicorn oh_agent.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
