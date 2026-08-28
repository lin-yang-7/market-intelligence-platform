import pytest
from mip_common.config import get_settings
from mip_common.secrets import (
    SecretDecryptionError,
    decrypt_secret,
    encrypt_secret,
    is_encrypted_secret,
)


def test_encrypt_decrypt_secret_roundtrip() -> None:
    encrypted = encrypt_secret("super-secret", "unit-test-key")

    assert is_encrypted_secret(encrypted)
    assert decrypt_secret(encrypted, "unit-test-key") == "super-secret"


def test_decrypt_rejects_wrong_key() -> None:
    encrypted = encrypt_secret("super-secret", "unit-test-key")

    with pytest.raises(SecretDecryptionError):
        decrypt_secret(encrypted, "wrong-key")


def test_settings_decrypt_sensitive_env(monkeypatch: pytest.MonkeyPatch) -> None:
    encrypted = encrypt_secret("jwt-secret-value", "settings-key")
    monkeypatch.setenv("SECRET_ENCRYPTION_KEY", "settings-key")
    monkeypatch.setenv("JWT_SECRET", encrypted)
    get_settings.cache_clear()
    try:
        settings = get_settings()
    finally:
        get_settings.cache_clear()

    assert settings.jwt_secret == "jwt-secret-value"


def test_production_settings_reject_default_jwt_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("JWT_SECRET", "dev-secret-change-me")
    get_settings.cache_clear()
    try:
        with pytest.raises(ValueError, match="JWT_SECRET"):
            get_settings()
    finally:
        get_settings.cache_clear()
