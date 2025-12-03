#  PKI + TOTP 2FA Microservice

This microservice implements **RSA-4096 (OAEP + PSS)** encryption/decryption and **TOTP (SHA-1, 6-digits, 30s)** for two-factor authentication.  
It uses **FastAPI** for endpoints, **Docker multi-stage builds**, and **cron jobs** for logging.

---

## Features
- RSA-4096 with OAEP (decryption) and PSS (signatures)
- TOTP generation and verification
- FastAPI endpoints
- Docker multi-stage build
- Cron job logging

---

## Endpoints

- **POST `/decrypt-seed`**  
  Decrypts seed via RSA-OAEP and stores it in `/data/seed.txt`

- **GET `/generate-2fa`**  
  Returns current TOTP and validity window

- **POST `/verify-2fa`**  
  Verifies a submitted TOTP code

---

## Cron Job

- **File used by Docker:** `cron/mycron`  
- Runs every minute and writes codes to `/cron/last_code.txt`  
- `cron/2fa-cron` included only to satisfy assignment LF requirement  

---

## Docker Usage

```bash
docker-compose build --no-cache
docker-compose up -d
