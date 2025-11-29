import base64
import re
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
    # 1. Base64 decode
    try:
        ciphertext = base64.b64decode(encrypted_seed_b64.strip())
    except Exception as e:
        raise ValueError("Invalid base64 encrypted_seed") from e

    # 2. Load student private key
    try:
        private_key = load_private_key_from_file(private_key_path)
    except Exception as e:
        raise ValueError("Failed to load private key") from e

    # 3. RSA/OAEP decrypt
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

    # 4. UTF-8 decode
    try:
        seed = plaintext.decode("utf-8").strip()
    except Exception as e:
        raise ValueError("Decrypted seed not UTF-8") from e

    # 5. Validate 64-character hex string
    if not HEX64_RE.fullmatch(seed):
        raise ValueError("Decrypted seed must be 64 lowercase hex")

    return seed
