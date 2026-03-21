import os
from cryptography.fernet import Fernet

key = os.environ.get('DATABASE_ENCRYPTION_KEY')
cipher_suite = Fernet(key.encode()) if key else None

def encrypt_data(data: str) -> str:
    if not data or not cipher_suite:
        return data
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_data(data: str) -> str:
    if not data or not cipher_suite:
        return data
    try:
        return cipher_suite.decrypt(data.encode()).decode()
    except Exception:
        return data