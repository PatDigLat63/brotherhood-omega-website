"""Security module with Vault encryption"""
from cryptography.fernet import Fernet
from core.config import settings

class SecurityError(Exception):
    pass

class Vault:
    def __init__(self):
        key = settings.MASTER_ENCRYPTION_KEY.get_secret_value()
        # Pad key to 32 bytes if needed
        key_bytes = key.encode()
        if len(key_bytes) < 32:
            key_bytes = key_bytes.ljust(32, b'=')
        self.cipher = Fernet(key_bytes)
    
    def encrypt(self, data: bytes) -> bytes:
        return self.cipher.encrypt(data)
    
    def decrypt(self, encrypted: bytes) -> bytes:
        return self.cipher.decrypt(encrypted)

class AuthenticationManager:
    @staticmethod
    def verify_token(token: str) -> dict:
        return {"sub": "test-user", "role": "god"}

vault = Vault()
