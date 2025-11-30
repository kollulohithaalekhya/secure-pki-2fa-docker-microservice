import base64
import re
import time
import pyotp
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

HEX64_RE = re.compile(r'^[0-9a-f]{64}$')

def load_private_key_from_file(path: str):
    with open(path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)

def decrypt_seed(encrypted_seed_b64: str, private_key_path: str) -> str:
    """
    Decrypt base64-encoded encrypted seed using RSA/OAEP (SHA-256, MGF1).
    Returns: 64-character hex seed.
    """
    try:
        ciphertext = base64.b64decode(encrypted_seed_b64.strip())
    except Exception as e:
        raise ValueError("Invalid base64 encrypted_seed") from e

    try:
        private_key = load_private_key_from_file(private_key_path)
    except Exception as e:
        raise ValueError("Failed to load private key") from e

    try:
        plaintext = private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
    except Exception as e:
        raise ValueError("Decryption failed") from e

    try:
        seed = plaintext.decode("utf-8").strip()
    except Exception as e:
        raise ValueError("Decrypted seed not UTF-8") from e

    if not HEX64_RE.fullmatch(seed):
        raise ValueError("Decrypted seed must be 64 lowercase hex")

    return seed

def _hex_to_base32(hex_seed: str) -> str:
    if len(hex_seed) != 64:
        raise ValueError("hex seed must be 64 characters")
    try:
        seed_bytes = bytes.fromhex(hex_seed)
    except Exception:
        raise ValueError("invalid hex seed")
    return base64.b32encode(seed_bytes).decode("utf-8")

def generate_totp_code(hex_seed: str):
    b32 = _hex_to_base32(hex_seed)
    totp = pyotp.TOTP(b32, digits=6, interval=30)
    code = totp.now()
    now = int(time.time())
    valid_for = 30 - (now % 30)
    return code, valid_for

def verify_totp_code(hex_seed: str, code: str, valid_window: int = 1) -> bool:
    b32 = _hex_to_base32(hex_seed)
    totp = pyotp.TOTP(b32, digits=6, interval=30)
    try:
        return bool(totp.verify(code, valid_window=valid_window))
    except Exception:
        return False
