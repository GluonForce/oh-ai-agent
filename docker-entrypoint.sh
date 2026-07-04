#!/bin/sh
set -e

mkdir -p /app/data/chroma /app/data/logs /app/logs
chown -R ohagent:ohagent /app/data /app/logs 2>/dev/null || true

exec "$@"
