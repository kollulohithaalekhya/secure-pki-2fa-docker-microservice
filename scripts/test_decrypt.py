from app.crypto import decrypt_seed
import sys

try:
    encrypted = open("encrypted_seed.txt").read().strip()
except FileNotFoundError:
    print("encrypted_seed.txt not found")
    sys.exit(1)

try:
    seed = decrypt_seed(encrypted, "student_private.pem")
    print("Decrypted seed:", seed)
except Exception as e:
    print("ERROR:", e)
    sys.exit(2)
