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
    encrypted_seed: str
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


@app.post("/decrypt-seed")
async def decrypt_seed_endpoint(req: DecryptRequest):
    if not req.encrypted_seed:
        return JSONResponse(status_code=400, content={"error": "Missing encrypted_seed"})

    # decrypt 
    try:
        seed_hex = decrypt_seed(req.encrypted_seed, PRIVATE_KEY_PATH)
    except Exception:
        return JSONResponse(status_code=500, content={"error": "Decryption failed"})

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
            # ignore chmod failures on Windows / restricted FS
            pass
    except Exception:
        return JSONResponse(status_code=500, content={"error": "Decryption failed"})

    return JSONResponse(status_code=200, content={"status": "ok"})

@app.get("/generate-2fa")
async def generate_2fa():
    seed_path = _get_seed_path()
    if not seed_path:
        return JSONResponse(status_code=500, content={"error": "Seed not decrypted yet"})

    try:
        with open(seed_path, "r", encoding="utf-8") as f:
            seed_hex = f.read().strip()
        code, valid_for = generate_totp_code(seed_hex)
    except Exception:
        return JSONResponse(status_code=500, content={"error": "Seed not decrypted yet"})

    return JSONResponse(status_code=200, content={"code": code, "valid_for": valid_for})

@app.post("/verify-2fa")
async def verify_2fa(req: VerifyRequest):
    # Validate code presence
    if not req.code:
        return JSONResponse(status_code=400, content={"error": "Missing code"})

    seed_path = _get_seed_path()
    if not seed_path:
        return JSONResponse(status_code=500, content={"error": "Seed not decrypted yet"})

    try:
        with open(seed_path, "r", encoding="utf-8") as f:
            seed_hex = f.read().strip()
        valid = verify_totp_code(seed_hex, req.code, valid_window=1)
    except Exception:
        return JSONResponse(status_code=500, content={"error": "Seed not decrypted yet"})

    return JSONResponse(status_code=200, content={"valid": bool(valid)})
