# -------------------------
# Stage 1: Builder
# -------------------------
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build deps (only if your packages need them)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency file and install to a wheel cache
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Copy app source (only needed to build if you compile assets; otherwise optional)
COPY . /app

# -------------------------
# Stage 2: Runtime
# -------------------------
FROM python:3.11-slim AS runtime

# Set timezone env (critical) and minimal env
ENV TZ=UTC
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install runtime system dependencies (cron, tzdata)
RUN apt-get update \
 && apt-get install -y --no-install-recommends cron tzdata ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Configure timezone to UTC
RUN ln -sf /usr/share/zoneinfo/UTC /etc/localtime \
 && echo "UTC" > /etc/timezone

# Copy python wheels from builder and install
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy application code, scripts, and cron config
COPY --chown=root:root . /app

# Ensure scripts are executable
RUN chmod +x /app/start.sh /app/scripts/cron-job.sh

# Place cron schedule into /etc/cron.d
COPY cron/mycron /etc/cron.d/mycron
RUN chmod 0644 /etc/cron.d/mycron

# Install the cron file (optional: register with crontab so 'crontab -l' shows it)
RUN crontab /etc/cron.d/mycron || true

# Create required runtime directories and set perms
RUN mkdir -p /data /cron /var/log/myapp \
 && chmod 755 /data /cron

VOLUME ["/data", "/cron"]

# Expose service port
EXPOSE 8080

# Use entrypoint script to start cron and the app
ENTRYPOINT ["/app/start.sh"]