FROM python:3.12-slim AS builder

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir . \
    && rm -rf src/ README.md

FROM python:3.12-slim AS runtime

WORKDIR /app

RUN groupadd -r ohagent && useradd -r -g ohagent -m ohagent

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn

COPY src/ ./src/
COPY knowledge_base/ ./knowledge_base/

RUN mkdir -p logs data/chroma data/logs \
    && chown -R ohagent:ohagent /app

USER ohagent

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "oh_agent.main:app", "--host", "0.0.0.0", "--port", "8000"]
