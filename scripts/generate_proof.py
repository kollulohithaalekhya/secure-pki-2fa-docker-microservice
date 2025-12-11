#!/usr/bin/env python3
"""
Generate commit proof for submission.

Steps:
 1. Read commit hash (40 hex chars)
 2. Sign with student_private.pem using RSA-PSS-SHA256
 3. Encrypt signature with instructor_public.pem using RSA-OAEP-SHA256
 4. Print Base64-encoded encrypted signature (single-line)
"""

import sys
import base64
import re
from app.crypto import sign_commit_hash, encrypt_signature_with_instructor

HEX40 = re.compile(r'^[0-9a-fA-F]{40}$')


def main():
    if len(sys.argv) >= 2:
        commit_hash = sys.argv[1].strip()
    else:
        commit_hash = input("Enter 40-char commit hash: ").strip()

    if not HEX40.fullmatch(commit_hash):
        print("ERROR: commit hash must be 40 hex characters.", file=sys.stderr)
        sys.exit(2)

    # Normalize to lowercase (grader expects hex string ASCII; signing ASCII of that is OK)
    commit_hash = commit_hash.lower()

    try:
        sig = sign_commit_hash(commit_hash, "student_private.pem")
        ct = encrypt_signature_with_instructor(sig, "instructor_public.pem")
        b64 = base64.b64encode(ct).decode("utf-8")
    except Exception as e:
        print("ERROR during proof generation:", repr(e), file=sys.stderr)
        sys.exit(3)

    print("\n=== SUBMISSION PROOF ===\n")
    print("Commit Hash:")
    print(commit_hash)
    print("\nEncrypted Signature (Base64 single-line):")
    print(b64)
    print("\n=== END ===\n")


if __name__ == "__main__":
    main()
