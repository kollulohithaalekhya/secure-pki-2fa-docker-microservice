#!/bin/sh
# simple cron job for testing: write timestamp to /data/cron-run.log
echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") - cron job ran" >> /data/cron-run.log
# do actual work below, e.g. call internal endpoint:
# curl -sS http://127.0.0.1:8080/some/task