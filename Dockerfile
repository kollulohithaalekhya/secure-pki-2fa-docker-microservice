# -------------------------
# Stage 1: Builder
# -------------------------
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

COPY . /app


# -------------------------
# Stage 2: Runtime
# -------------------------
FROM python:3.11-slim AS runtime

ENV TZ=UTC
ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends cron tzdata ca-certificates curl \
 && rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/share/zoneinfo/UTC /etc/localtime \
 && echo "UTC" > /etc/timezone

COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*

COPY . /app

# FIX LINE ENDINGS + PERMISSIONS
RUN sed -i 's/\r$//' /app/start.sh && chmod 755 /app/start.sh \
 && sed -i 's/\r$//' /app/scripts/cron-job.sh && chmod 755 /app/scripts/cron-job.sh \
 && sed -i 's/\r$//' /app/cron/mycron

# Install cron schedule
COPY cron/mycron /etc/cron.d/mycron
RUN chmod 0644 /etc/cron.d/mycron && crontab /etc/cron.d/mycron

RUN mkdir -p /data /cron /var/log/myapp && chmod 755 /data /cron

VOLUME ["/data", "/cron"]

EXPOSE 8080

ENTRYPOINT ["/app/start.sh"]
