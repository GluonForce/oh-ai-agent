#!/bin/sh
set -e

# Railway volumes mount as root; ensure app user can write ChromaDB + audit logs.
mkdir -p /app/data/chroma /app/data/logs /app/logs
chown -R ohagent:ohagent /app/data /app/logs

exec su -s /bin/sh ohagent -c 'exec "$@"' _ "$@"
