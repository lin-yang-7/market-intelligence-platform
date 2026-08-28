import base64
import binascii
import hashlib
import hmac
import os

SECRET_PREFIX = "enc:v1:"
NONCE_SIZE = 16
TAG_SIZE = 32


class SecretDecryptionError(ValueError):
    pass


def is_encrypted_secret(value: str) -> bool:
    return value.startswith(SECRET_PREFIX)


def encrypt_secret(plaintext: str, key: str) -> str:
    if not key:
        raise SecretDecryptionError("SECRET_ENCRYPTION_KEY is required")
    nonce = os.urandom(NONCE_SIZE)
    key_bytes = _derive_key(key)
    plaintext_bytes = plaintext.encode("utf-8")
    ciphertext = _xor_stream(plaintext_bytes, key_bytes, nonce)
    tag = _tag(key_bytes, nonce, ciphertext)
    payload = base64.urlsafe_b64encode(nonce + ciphertext + tag).decode("ascii")
    return SECRET_PREFIX + payload


def decrypt_secret(value: str, key: str | None = None) -> str:
    if not is_encrypted_secret(value):
        return value
    key = key if key is not None else os.getenv("SECRET_ENCRYPTION_KEY", "")
    if not key:
        raise SecretDecryptionError("SECRET_ENCRYPTION_KEY is required")
    try:
        payload = base64.urlsafe_b64decode(value.removeprefix(SECRET_PREFIX).encode("ascii"))
    except (binascii.Error, ValueError) as exc:
        raise SecretDecryptionError("Invalid encrypted secret payload") from exc
    if len(payload) < NONCE_SIZE + TAG_SIZE:
        raise SecretDecryptionError("Invalid encrypted secret payload")
    nonce = payload[:NONCE_SIZE]
    ciphertext = payload[NONCE_SIZE:-TAG_SIZE]
    expected_tag = payload[-TAG_SIZE:]
    key_bytes = _derive_key(key)
    actual_tag = _tag(key_bytes, nonce, ciphertext)
    if not hmac.compare_digest(expected_tag, actual_tag):
        raise SecretDecryptionError("Encrypted secret authentication failed")
    return _xor_stream(ciphertext, key_bytes, nonce).decode("utf-8")


def _derive_key(key: str) -> bytes:
    return hashlib.sha256(key.encode("utf-8")).digest()


def _tag(key: bytes, nonce: bytes, ciphertext: bytes) -> bytes:
    return hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()


def _xor_stream(payload: bytes, key: bytes, nonce: bytes) -> bytes:
    output = bytearray()
    counter = 0
    while len(output) < len(payload):
        block = hmac.new(key, nonce + counter.to_bytes(8, "big"), hashlib.sha256).digest()
        output.extend(block)
        counter += 1
    return bytes(left ^ right for left, right in zip(payload, output, strict=False))
