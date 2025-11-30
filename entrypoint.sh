#!/usr/bin/env bash
set -euo pipefail

# Default env values (can be overridden at docker run)
: "${APP_MODULE:=main:app}"   # python module: uvicorn expects "module:app"
: "${HOST:=0.0.0.0}"
: "${PORT:=8080}"
: "${WORKERS:=1}"
: "${PYTHONUNBUFFERED:=1}"

export TZ=UTC
ln -fs /usr/share/zoneinfo/UTC /etc/localtime || true

# Start cron in background (system cron)
if command -v cron >/dev/null 2>&1; then
    echo "Starting cron..."
    cron || /etc/init.d/cron start || true
else
    echo "cron not found, skipping cron start"
fi

# Ensure /data and /cron exist and are writable
mkdir -p /data /cron
chmod 755 /data /cron || true

# Start the app (uvicorn) in foreground so container stays alive
# Use exec so signals are forwarded to uvicorn process
echo "Starting uvicorn on ${HOST}:${PORT} (module=${APP_MODULE})"
exec uvicorn --host "${HOST}" --port "${PORT}" --workers "${WORKERS}" "${APP_MODULE}"
