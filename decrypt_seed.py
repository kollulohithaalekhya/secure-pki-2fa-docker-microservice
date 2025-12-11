# decrypt_seed.py
import base64, sys, binascii
from pathlib import Path
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

def main(enc_file="encrypted_seed.txt", priv_file="student_private.pem", out_file="data/seed.txt"):
    enc_b64 = Path(enc_file).read_bytes().strip()
    try:
        enc = base64.b64decode(enc_b64)
    except Exception as e:
        raise SystemExit("Base64 decode failed: "+str(e))

    pem = Path(priv_file).read_bytes()
    priv = serialization.load_pem_private_key(pem, password=None)

    try:
        pt = priv.decrypt(enc, padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    except Exception as e:
        raise SystemExit("RSA decryption failed: "+str(e))

    seed = pt.decode("utf-8").strip()
    if len(seed) != 64 or any(c not in "0123456789abcdef" for c in seed.lower()):
        raise SystemExit("Decrypted seed invalid (must be 64-hex). Got: %r" % seed[:40])

    Path(out_file).parent.mkdir(parents=True, exist_ok=True)
    Path(out_file).write_text(seed + "\n")
    print("Wrote decrypted seed to", out_file)

if __name__ == "__main__":
    import sys
    args=sys.argv[1:]
    main(*args)
