#!/bin/sh

API_URL="http://127.0.0.1:8080/generate-2fa"
OUT_FILE="/cron/last_code.txt"

RESP="$(curl -s "$API_URL")"
CODE="$(echo "$RESP" | grep -o '[0-9]\{6\}')"

TS="$(date -u '+%Y-%m-%d %H:%M:%S')"

echo "$TS - 2FA Code: $CODE" >> "$OUT_FILE"
