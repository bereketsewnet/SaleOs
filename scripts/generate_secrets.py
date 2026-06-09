"""
Run once before first docker compose up:
    pip install cryptography
    python scripts/generate_secrets.py

Copy the output values into your .env file.
"""
import secrets
from cryptography.fernet import Fernet

print("# Paste these into your .env file")
print(f"JWT_SECRET={secrets.token_hex(32)}")
print(f"X_SERVICE_TOKEN={secrets.token_hex(32)}")
print(f"ENCRYPTION_KEY={Fernet.generate_key().decode()}")
print(f"WS_SECRET={secrets.token_hex(16)}")
