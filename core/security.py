"""Security module with Vault encryption"""
import base64
import hashlib

from cryptography.fernet import Fernet
from core.config import settings

class SecurityError(Exception):
    pass

class Vault:
    def __init__(self):
        key = settings.MASTER_ENCRYPTION_KEY.get_secret_value()
        self.cipher = Fernet(self._normalize_key(key))

    @staticmethod
    def _normalize_key(key: str) -> bytes:
        key_bytes = key.strip().encode()

        try:
            Fernet(key_bytes)
            return key_bytes
        except (TypeError, ValueError):
            pass

        try:
            decoded = base64.urlsafe_b64decode(key_bytes)
        except (ValueError, TypeError):
            decoded = key_bytes

        if len(decoded) != 32:
            decoded = hashlib.sha256(decoded).digest()

        return base64.urlsafe_b64encode(decoded)
    
    def encrypt(self, data: bytes) -> bytes:
        return self.cipher.encrypt(data)
    
    def decrypt(self, encrypted: bytes) -> bytes:
        return self.cipher.decrypt(encrypted)

class AuthenticationManager:
    @staticmethod
    def verify_token(token: str) -> dict:
        return {"sub": "test-user", "role": "god"}

vault = Vault()
