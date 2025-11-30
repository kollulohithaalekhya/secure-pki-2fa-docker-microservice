# Stage 1: Builder - install Python deps into /install
FROM python:3.11-slim AS builder
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Install build deps required by wheels (e.g. cryptography)
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential gcc libssl-dev libffi-dev python3-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip && \
    python -m pip install --prefix=/install -r /app/requirements.txt

# Stage 2: Runtime - minimal image + cron + tzdata
FROM python:3.11-slim
ENV TZ=UTC
ENV PATH=/install/bin:$PATH
ENV PYTHONPATH=/install/lib/python3.11/site-packages:$PYTHONPATH
WORKDIR /app

# Install runtime system deps: cron + tzdata, configure UTC
RUN apt-get update && \
    apt-get install -y --no-install-recommends cron tzdata && \
    ln -fs /usr/share/zoneinfo/UTC /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata || true && \
    rm -rf /var/lib/apt/lists/*

# Copy installed python packages from builder
COPY --from=builder /install /install

# Copy application code into the image (including keys & cron config)
COPY . /app

# Create runtime directories (to be mounted as volumes at runtime if desired)
RUN mkdir -p /data /cron && chmod 755 /data /cron

# Install cron file if provided in repo at cron/2fa-cron
RUN if [ -f /app/cron/2fa-cron ]; then \
      install -m 0644 /app/cron/2fa-cron /etc/cron.d/2fa-cron && \
      chmod 0644 /etc/cron.d/2fa-cron && \
      crontab /etc/cron.d/2fa-cron; \
    fi

# Copy entrypoint and make executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose API port
EXPOSE 8080

# Entrypoint will start cron and then the app server (uvicorn)
ENTRYPOINT ["/entrypoint.sh"]
