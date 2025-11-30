#!/usr/bin/env bash
set -e
echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") cleanup_2fa: running" >> /var/log/2fa-cleanup.log
# Add your cleanup logic here, e.g. remove stale files under /data/tmp
find /data -type f -name '*.tmp' -mtime +1 -delete || true
