FROM python:3.12-slim AS base

WORKDIR /app

RUN groupadd -r ohagent && useradd -r -g ohagent ohagent

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

FROM base AS runtime

COPY src/ ./src/
COPY knowledge_base/ ./knowledge_base/

RUN mkdir -p logs && chown -R ohagent:ohagent /app

USER ohagent

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD python -c "import httpx; r = httpx.get('http://localhost:8000/health'); r.raise_for_status()"

CMD ["uvicorn", "oh_agent.main:app", "--host", "0.0.0.0", "--port", "8000"]
