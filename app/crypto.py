import base64
import re
import time
import pyotp
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

# regex for 64-lowercase-hex
HEX64_RE = re.compile(r'^[0-9a-f]{64}$')


# -------------------------
# Key loading helpers
# -------------------------
def load_private_key_from_file(path: str):
    """Load a PEM private key from file (no password)."""
    with open(path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def load_public_key_from_file(path: str):
    """Load a PEM public key from file."""
    with open(path, "rb") as f:
        return serialization.load_pem_public_key(f.read())


# -------------------------
# Seed decryption (RSA-OAEP SHA-256)
# -------------------------
def decrypt_seed(encrypted_seed_b64: str, private_key_path: str) -> str:
    """
    Decrypt base64-encoded encrypted seed using RSA/OAEP (SHA-256, MGF1).
    Returns: 64-character hex seed (lowercase).
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


# -------------------------
# TOTP helpers
# -------------------------
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


# -------------------------
# Commit proof helpers (new)
# -------------------------
def sign_commit_hash(commit_hash: str, private_key_path: str) -> bytes:
    """
    Sign ASCII commit_hash using RSA-PSS with SHA-256 (salt = MAX_LENGTH).
    commit_hash must be the 40-char hex string (ASCII).
    Returns signature bytes.
    """
    if not isinstance(commit_hash, str) or len(commit_hash) != 40:
        raise ValueError("commit_hash must be 40-character hex string")

    # load private key
    priv = load_private_key_from_file(private_key_path)

    msg = commit_hash.encode("utf-8")  # ASCII bytes

    signature = priv.sign(
        msg,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature


def encrypt_signature_with_instructor(signature: bytes, instructor_pub_path: str) -> bytes:
    """
    Encrypt signature bytes using instructor_public.pem with RSA-OAEP-SHA256.
    Returns ciphertext bytes.
    """
    pub = load_public_key_from_file(instructor_pub_path)

    ct = pub.encrypt(
        signature,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return ct
