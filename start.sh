#!/bin/sh
set -e

echo "Starting cron..."
/usr/sbin/cron

# Cron logs visible in docker logs
touch /var/log/cron.log
tail -F /var/log/cron.log >/dev/stdout 2>&1 &

echo "Starting FastAPI app..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8080
