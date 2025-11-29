from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from app.crypto import decrypt_seed

app = FastAPI()

DATA_DIR = "/data"
SEED_PATH = os.path.join(DATA_DIR, "seed.txt")
PRIVATE_KEY_PATH = "/app/student_private.pem"   # inside container

class DecryptRequest(BaseModel):
    encrypted_seed: str

@app.post("/decrypt-seed")
async def decrypt_seed_endpoint(req: DecryptRequest):
    if not req.encrypted_seed:
        raise HTTPException(status_code=400, detail={"error": "Missing encrypted_seed"})

    try:
        seed_hex = decrypt_seed(req.encrypted_seed, PRIVATE_KEY_PATH)
    except Exception:
        raise HTTPException(status_code=500, detail={"error": "Decryption failed"})

    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(SEED_PATH, "w") as f:
            f.write(seed_hex + "\n")
        os.chmod(SEED_PATH, 0o600)
    except Exception:
        raise HTTPException(status_code=500, detail={"error": "Decryption failed"})

    return {"status": "ok"}
