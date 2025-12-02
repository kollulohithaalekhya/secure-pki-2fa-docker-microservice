from app.crypto import decrypt_seed, generate_totp_code, verify_totp_code
import sys

try:
    enc = open("encrypted_seed.txt", "r").read().strip()
except FileNotFoundError:
    print("encrypted_seed.txt not found")
    sys.exit(1)

try:
    hex_seed = decrypt_seed(enc, "student_private.pem")
except Exception as e:
    print("Decryption failed:", e)
    sys.exit(2)

print("Hex seed:", hex_seed)

code, valid_for = generate_totp_code(hex_seed)
print("TOTP code:", code)
print("Valid for (seconds):", valid_for)

print("Verify code (expected True):", verify_totp_code(hex_seed, code))
print("Verify '000000' (expected False):", verify_totp_code(hex_seed, "000000"))
