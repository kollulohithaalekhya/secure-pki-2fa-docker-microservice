#!/bin/sh

API_URL="http://127.0.0.1:8080/generate-2fa"
OUT_FILE="/cron/last_code.txt"

# Call API – will return JSON: {"code":"123456","valid_for":27}
RESPONSE="$(curl -s "$API_URL")"

# Extract digits only → removes JSON, quotes, braces
CODE="$(echo "$RESPONSE" | grep -o '[0-9]\{6\}')"

# Timestamp (UTC)
TS="$(date -u '+%Y-%m-%d %H:%M:%S')"

echo "$TS - 2FA Code: $CODE" >> "$OUT_FILE"
