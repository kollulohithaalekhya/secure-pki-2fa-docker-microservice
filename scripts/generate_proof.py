#!/usr/bin/env python3
"""
Auto-proof generator.

Usage:
  # auto-detect latest commit (recommended)
  python scripts/generate_proof.py

  # or manually pass a commit hash (40 hex chars)
  python scripts/generate_proof.py f0a73f3a6bb33bcb44e47b806d31ebab14c515f9
"""

import os
import sys
import subprocess
import base64
import re

# ensure repo root (parent of scripts/) is on sys.path so `import app` works
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# now safe to import from app
try:
    from app.crypto import sign_commit_hash, encrypt_signature_with_instructor
except Exception as e:
    print("ERROR: Failed to import app.crypto - are you running this from the repo root?")
    print("Exception:", repr(e))
    sys.exit(2)

HEX40 = re.compile(r'^[0-9a-f]{40}$', re.IGNORECASE)


def get_latest_commit_hash():
    """Return the latest git commit hash (40 chars)."""
    try:
        out = subprocess.check_output(["git", "log", "-1", "--format=%H"], cwd=ROOT, universal_newlines=True)
        return out.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError("Could not get git commit hash. Make sure git is available and you're in a git repo.") from e


def generate_proof_for_hash(commit_hash: str):
    # normalize
    commit_hash = commit_hash.strip().lower()
    if not HEX40.fullmatch(commit_hash):
        raise ValueError("Commit hash must be 40 hex characters (got: {})".format(commit_hash))

    # sign using student_private.pem (path relative to ROOT)
    priv_path = os.path.join(ROOT, "student_private.pem")
    instr_pub_path = os.path.join(ROOT, "instructor_public.pem")

    if not os.path.isfile(priv_path):
        raise FileNotFoundError(f"student_private.pem not found at {priv_path}")
    if not os.path.isfile(instr_pub_path):
        raise FileNotFoundError(f"instructor_public.pem not found at {instr_pub_path}")

    # call helpers (these expect file paths)
    signature = sign_commit_hash(commit_hash, priv_path)
    ciphertext = encrypt_signature_with_instructor(signature, instr_pub_path)
    b64 = base64.b64encode(ciphertext).decode("utf-8")

    return commit_hash, b64


def main():
    # select commit hash: argument or auto
    if len(sys.argv) >= 2:
        commit_hash = sys.argv[1].strip()
        print(f"[MANUAL] Using commit hash: {commit_hash}")
    else:
        try:
            commit_hash = get_latest_commit_hash()
            print(f"[AUTO] Using latest commit hash: {commit_hash}")
        except Exception as e:
            print("ERROR: could not determine latest git commit hash:", repr(e))
            sys.exit(3)

    try:
        ch, b64 = generate_proof_for_hash(commit_hash)
    except Exception as e:
        print("ERROR during proof generation:", repr(e))
        sys.exit(4)

    print("\n=== SUBMISSION PROOF ===\n")
    print("Commit Hash:")
    print(ch)
    print("\nEncrypted Signature (Base64 single-line):")
    print(b64)
    print("\n=== END ===\n")


if __name__ == "__main__":
    main()
