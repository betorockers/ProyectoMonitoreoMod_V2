from __future__ import annotations

import base64
import hashlib
import json

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from config.licensing import LICENSE_PUBLIC_KEY_B64, LICENSE_SERIAL_PREFIX
from licensing.license_models import LicensePayload


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def normalize_serial(serial: str) -> str:
    return "".join((serial or "").strip().split())


def serial_hash(serial: str) -> str:
    return hashlib.sha256(normalize_serial(serial).encode("utf-8")).hexdigest().upper()


def payload_to_bytes(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def load_public_key() -> Ed25519PublicKey:
    key_bytes = base64.b64decode(LICENSE_PUBLIC_KEY_B64.encode("ascii"))
    return serialization.load_pem_public_key(key_bytes)


def encode_license_serial(payload: dict, private_key: Ed25519PrivateKey) -> str:
    payload_bytes = payload_to_bytes(payload)
    signature = private_key.sign(payload_bytes)
    return f"{LICENSE_SERIAL_PREFIX}.{_b64url_encode(payload_bytes)}.{_b64url_encode(signature)}"


def decode_and_verify_serial(serial: str) -> tuple[LicensePayload, str]:
    normalized = normalize_serial(serial)
    try:
        prefix, payload_part, signature_part = normalized.split(".", 2)
    except ValueError as exc:
        raise ValueError("Formato de serial invalido") from exc

    if prefix != LICENSE_SERIAL_PREFIX:
        raise ValueError("Prefijo de serial invalido")

    payload_bytes = _b64url_decode(payload_part)
    signature = _b64url_decode(signature_part)
    load_public_key().verify(signature, payload_bytes)
    payload_dict = json.loads(payload_bytes.decode("utf-8"))
    return LicensePayload(**payload_dict), _b64url_encode(signature)
