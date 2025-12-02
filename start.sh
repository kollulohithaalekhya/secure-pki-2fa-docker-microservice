#!/bin/sh
set -e

# Start cron in background (writes logs to /var/log/cron.log)
# Debian cron: service cron start or /usr/sbin/cron -f (foreground)
# We'll start cron in background and then exec the app in foreground.

echo "Starting cron..."
/usr/sbin/cron

# Ensure log file exists and tail it in background so logs show up in `docker logs`
touch /var/log/cron.log
tail -F /var/log/cron.log >/dev/stdout 2>&1 &

# Start the app (example: uvicorn for FastAPI)
echo "Starting app on 0.0.0.0:8080..."
# Replace below with your actual app command if it's different
exec uvicorn app.main:app --host 0.0.0.0 --port 8080