import base64
import hashlib
import hmac
import os

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings

ITERATIONS = 120_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return f"{ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    iterations_str, salt_hex, digest_hex = encoded.split("$", maxsplit=2)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        int(iterations_str),
    )
    return hmac.compare_digest(digest.hex(), digest_hex)


def _build_fernet() -> Fernet:
    raw_key = get_settings().llm_encryption_key.encode("utf-8")
    derived_key = hashlib.sha256(raw_key).digest()
    return Fernet(base64.urlsafe_b64encode(derived_key))


def encrypt_secret(secret: str) -> str:
    token = _build_fernet().encrypt(secret.encode("utf-8")).decode("utf-8")
    return f"enc:{token}"


def decrypt_secret(encoded: str | None) -> str | None:
    if not encoded:
        return None
    if not encoded.startswith("enc:"):
        return encoded
    token = encoded.removeprefix("enc:")
    try:
        return _build_fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return None
