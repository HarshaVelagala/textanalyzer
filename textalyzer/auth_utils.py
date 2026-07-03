import hashlib
import secrets


def hash_password(password: str, salt: str = None):
    """PBKDF2-HMAC-SHA256, pure standard library. No network calls, no API keys."""
    if salt is None:
        salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000
    ).hex()
    return pwd_hash, salt


def verify_password(password: str, salt: str, stored_hash: str) -> bool:
    pwd_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(pwd_hash, stored_hash)
