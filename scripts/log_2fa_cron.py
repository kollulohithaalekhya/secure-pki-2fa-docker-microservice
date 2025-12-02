#!/usr/bin/env python3
# Cron script to log 2FA codes every minute

#!/usr/bin/env python3
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime, timezone
from app.crypto import generate_totp_code

# 1. Load seed
seed_path = "/data/seed.txt"
try:
    with open(seed_path, "r") as f:
        hex_seed = f.read().strip()
except FileNotFoundError:
    print("[ERROR] Seed file not found:", seed_path)
    exit(1)

# 2. Generate current TOTP
code, valid_for = generate_totp_code(hex_seed)

# 3. Get timestamp in UTC (very important)
timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

# 4. Print formatted output
print(f"{timestamp} UTC - 2FA Code: {code}")