from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
from typing import Optional

from app.crypto import decrypt_seed, generate_totp_code, verify_totp_code

app = FastAPI()
DATA_DIR = "/data"
SEED_PATH = os.path.join(DATA_DIR, "seed.txt")
FALLBACK_SEED_PATH = os.path.join(os.getcwd(), "data", "seed.txt")
PRIVATE_KEY_PATH = "student_private.pem"

class DecryptRequest(BaseModel):
    # accept either field name used by some docs
    encrypted_seed: Optional[str] = None
    encrypted_seed_b64: Optional[str] = None

class VerifyRequest(BaseModel):
    code: Optional[str] = None

def _get_seed_path():
    """
    Return path to seed file if present, or None if not present.
    Check /data/seed.txt first (container), then ./data/seed.txt (local).
    """
    if os.path.isfile(SEED_PATH):
        return SEED_PATH
    if os.path.isfile(FALLBACK_SEED_PATH):
        return FALLBACK_SEED_PATH
    return None

def _is_valid_hex64(s: str) -> bool:
    return isinstance(s, str) and len(s) == 64 and all(c in "0123456789abcdef" for c in s.lower())

@app.post("/decrypt-seed")
async def decrypt_seed_endpoint(req: DecryptRequest):
    # accept either encrypted_seed or encrypted_seed_b64 for flexibility
    enc = None
    if getattr(req, "encrypted_seed_b64", None):
        enc = req.encrypted_seed_b64
    elif getattr(req, "encrypted_seed", None):
        enc = req.encrypted_seed

    if not enc:
        return JSONResponse(status_code=400, content={"error": "Missing encrypted_seed (base64)"})

    # decrypt using helper from app.crypto
    try:
        seed_hex = decrypt_seed(enc, PRIVATE_KEY_PATH)
    except Exception as e:
        # include a short message for debugging in logs (not leaking sensitive data)
        print("decrypt_seed failed:", repr(e))
        return JSONResponse(status_code=500, content={"error": "Decryption failed"})

    # validate result is a 64-char hex string
    if not _is_valid_hex64(seed_hex):
        print("decrypted seed invalid format:", seed_hex[:32])
        return JSONResponse(status_code=500, content={"error": "Decrypted seed invalid format"})

    # store to /data/seed.txt
    try:
        target_dir = os.path.dirname(SEED_PATH)
        if not os.path.isdir(target_dir):
            os.makedirs(target_dir, exist_ok=True)
        with open(SEED_PATH, "w", encoding="utf-8") as f:
            f.write(seed_hex + "\n")
        try:
            os.chmod(SEED_PATH, 0o600)
        except Exception:
            # chmod may not be available on some Windows mounts; ignore
            pass
    except Exception as e:
        print("writing seed failed:", repr(e))
        return JSONResponse(status_code=500, content={"error": "Failed to write seed to disk"})

    return JSONResponse(status_code=200, content={"status": "ok"})

@app.get("/generate-2fa")
async def generate_2fa():
    seed_path = _get_seed_path()
    if not seed_path:
        return JSONResponse(status_code=500, content={"error": "Seed not decrypted yet"})

    try:
        with open(seed_path, "r", encoding="utf-8") as f:
            seed_hex = f.read().strip()
        if not _is_valid_hex64(seed_hex):
            return JSONResponse(status_code=500, content={"error": "Seed invalid format"})
        code, valid_for = generate_totp_code(seed_hex)
    except Exception as e:
        print("generate_2fa error:", repr(e))
        return JSONResponse(status_code=500, content={"error": "Failed to generate TOTP"})
    return JSONResponse(status_code=200, content={"code": code, "valid_for": valid_for})

@app.post("/verify-2fa")
async def verify_2fa(req: VerifyRequest):
    if not req.code:
        return JSONResponse(status_code=400, content={"error": "Missing code"})

    seed_path = _get_seed_path()
    if not seed_path:
        return JSONResponse(status_code=500, content={"error": "Seed not decrypted yet"})

    try:
        with open(seed_path, "r", encoding="utf-8") as f:
            seed_hex = f.read().strip()
        if not _is_valid_hex64(seed_hex):
            return JSONResponse(status_code=500, content={"error": "Seed invalid format"})
        # verify with ±1 period tolerance
        valid = verify_totp_code(seed_hex, req.code, valid_window=1)
    except Exception as e:
        print("verify_2fa error:", repr(e))
        return JSONResponse(status_code=500, content={"error": "Failed to verify code"})

    return JSONResponse(status_code=200, content={"valid": bool(valid)})

# ------------------------
# NEW ENDPOINTS FOR STEP 8
# ------------------------

@app.get("/")
def read_root():
    return {"status":"ok","message":"hello from container"}

@app.get("/health")
def health():
    return {"status":"healthy"}
