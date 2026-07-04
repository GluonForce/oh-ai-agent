FROM python:3.12-slim AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies only (cached layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

FROM base AS runtime

COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/
COPY knowledge_base/ ./knowledge_base/

RUN uv sync --frozen --no-dev \
    && mkdir -p /app/data/chroma /app/data/logs /app/logs \
    && uv run python -c "\
import chromadb; \
client = chromadb.PersistentClient(path='/tmp/chroma-warmup'); \
col = client.get_or_create_collection('warmup'); \
col.add(documents=['warmup'], ids=['1']); \
client.delete_collection('warmup'); \
"

COPY start.sh /start.sh
RUN chmod +x /start.sh

ENV PATH="/app/.venv/bin:$PATH"
ENV PORT=8000
ENV ANONYMIZED_TELEMETRY=False

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s \
    CMD python -c "import os, httpx; port=os.environ.get('PORT','8000'); r=httpx.get(f'http://localhost:{port}/health'); r.raise_for_status()"

CMD ["/start.sh"]
