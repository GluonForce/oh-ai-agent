#!/bin/sh
set -e

CHROMA_DIR="${OH_CHROMA_PERSIST_DIR:-/app/data/chroma}"
AUDIT_DIR="$(dirname "${OH_AUDIT_LOG_FILE:-/app/data/logs/audit.jsonl}")"

mkdir -p "$CHROMA_DIR" "$AUDIT_DIR" /app/logs

echo "Starting OH AI Agent on 0.0.0.0:${PORT:-8000} (chroma=${CHROMA_DIR})"
exec uvicorn oh_agent.main:app --host 0.0.0.0 --port "${PORT:-8000}"
