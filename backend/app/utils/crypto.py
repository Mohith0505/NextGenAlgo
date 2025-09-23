from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import struct
import threading
from typing import Any, Mapping, Protocol

try:
    from cryptography.fernet import Fernet, InvalidToken  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional dependency fallback
    Fernet = None  # type: ignore[assignment]
    InvalidToken = Exception  # type: ignore[assignment]

from app.core.config import settings


class CredentialCipherError(Exception):
    """Base exception for credential encryption issues."""


class CredentialDecryptError(CredentialCipherError):
    """Raised when stored credentials cannot be decrypted."""


class _CipherLike(Protocol):
    def encrypt(self, data: bytes) -> bytes: ...

    def decrypt(self, token: bytes) -> bytes: ...


class _FallbackCipher:  # pragma: no cover - exercised via runtime fallback
    """Simple XOR/HMAC based cipher used when cryptography is unavailable."""

    def __init__(self, key_bytes: bytes) -> None:
        self._key = key_bytes

    def _keystream(self, nonce: bytes, length: int) -> bytes:
        blocks: list[bytes] = []
        counter = 0
        produced = 0
        while produced < length:
            counter_bytes = struct.pack(">Q", counter)
            digest = hashlib.sha256(self._key + nonce + counter_bytes).digest()
            blocks.append(digest)
            produced += len(digest)
            counter += 1
        stream = b"".join(blocks)[:length]
        return stream

    def encrypt(self, data: bytes) -> bytes:
        nonce = os.urandom(16)
        keystream = self._keystream(nonce, len(data))
        ciphertext = bytes(a ^ b for a, b in zip(data, keystream))
        tag = hmac.new(self._key, nonce + ciphertext, hashlib.sha256).digest()
        token = base64.urlsafe_b64encode(nonce + ciphertext + tag)
        return token

    def decrypt(self, token: bytes) -> bytes:
        raw = base64.urlsafe_b64decode(token)
        if len(raw) < 16 + 32:
            raise CredentialDecryptError("Stored credential token malformed")
        nonce = raw[:16]
        tag = raw[-32:]
        ciphertext = raw[16:-32]
        expected_tag = hmac.new(self._key, nonce + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(tag, expected_tag):
            raise CredentialDecryptError("Credential signature mismatch")
        keystream = self._keystream(nonce, len(ciphertext))
        plaintext = bytes(a ^ b for a, b in zip(ciphertext, keystream))
        return plaintext


_cipher_lock = threading.Lock()
_cipher: _CipherLike | None = None


def _derive_key(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def _get_cipher() -> _CipherLike:
    global _cipher
    if _cipher is None:
        with _cipher_lock:
            if _cipher is None:
                key = _derive_key(settings.secret_key)
                if Fernet is not None:
                    _cipher = Fernet(key)  # type: ignore[assignment]
                else:  # pragma: no cover - fallback path
                    raw_key = hashlib.sha256(settings.secret_key.encode("utf-8")).digest()
                    _cipher = _FallbackCipher(raw_key)
    return _cipher


def encrypt_credentials(payload: Mapping[str, Any]) -> str:
    serialized = json.dumps(payload, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
    token = _get_cipher().encrypt(serialized.encode("utf-8"))
    return token.decode("utf-8") if isinstance(token, bytes) else token


def decrypt_credentials(token: str) -> dict[str, Any]:
    try:
        decrypted_bytes = _get_cipher().decrypt(token.encode("utf-8"))
    except InvalidToken as exc:  # type: ignore[arg-type]
        raise CredentialDecryptError("Unable to decrypt stored broker credentials") from exc
    except CredentialDecryptError:
        raise
    except Exception as exc:  # pragma: no cover - unexpected failure
        raise CredentialDecryptError("Unable to decrypt stored broker credentials") from exc
    payload = json.loads(decrypted_bytes.decode("utf-8"))
    if not isinstance(payload, dict):
        raise CredentialDecryptError("Stored broker credential payload is malformed")
    return payload


__all__ = [
    "CredentialCipherError",
    "CredentialDecryptError",
    "decrypt_credentials",
    "encrypt_credentials",
]
