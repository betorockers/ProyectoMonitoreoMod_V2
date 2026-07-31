from __future__ import annotations

from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from config.licensing import APP_LICENSE_ID, LICENSE_SCHEMA_VERSION
from licensing.license_crypto import encode_license_serial
from licensing.license_service import LicenseService


class FakeStorage:
    def __init__(self):
        self.values = {}
        self.activation = None

    def save_activation(self, data: dict) -> None:
        self.activation = data

    def load_activation(self) -> dict | None:
        return self.activation

    def clear_activation(self) -> None:
        self.activation = None

    def save_pending_serial(self, serial: str) -> None:
        self.values["PendingSerial"] = serial

    def load_pending_serial(self) -> str | None:
        return self.values.get("PendingSerial")

    def clear_pending_serial(self) -> None:
        self.values.pop("PendingSerial", None)

    def save_marker(self, name: str, value: str) -> None:
        self.values[name] = value

    def load_marker(self, name: str) -> str | None:
        return self.values.get(name)


def _make_payload(license_type: str = "PERPETUAL", expires_at: str | None = None) -> dict:
    return {
        "schema_version": LICENSE_SCHEMA_VERSION,
        "app_id": APP_LICENSE_ID,
        "license_id": "TEST-0001",
        "edition": "PRO",
        "license_type": license_type,
        "issued_at": datetime(2026, 3, 19, tzinfo=timezone.utc).isoformat(),
        "expires_at": expires_at,
        "customer_name": "ANVIC",
        "seat_label": "LAB-01",
        "notes": "Prueba automatizada",
    }


def test_license_service_activates_valid_perpetual_license(monkeypatch):
    private_key = Ed25519PrivateKey.generate()
    monkeypatch.setattr("licensing.license_crypto.load_public_key", lambda: private_key.public_key())
    monkeypatch.setattr("licensing.license_service.get_machine_fingerprint", lambda: "MACHINE-ABC-123")

    service = LicenseService(FakeStorage())
    serial = encode_license_serial(_make_payload(), private_key)
    state = service.activate_serial(serial)

    assert state.valid is True
    assert state.status == "valid"
    assert state.payload is not None
    assert state.payload.license_type == "PERPETUAL"
    assert service.get_summary()["edition"] == "PRO"


def test_license_service_marks_expired_annual_license(monkeypatch):
    private_key = Ed25519PrivateKey.generate()
    monkeypatch.setattr("licensing.license_crypto.load_public_key", lambda: private_key.public_key())
    monkeypatch.setattr("licensing.license_service.get_machine_fingerprint", lambda: "MACHINE-XYZ-999")

    service = LicenseService(FakeStorage())
    service.utcnow = lambda: datetime(2026, 3, 19, tzinfo=timezone.utc)

    expired_at = (datetime(2026, 3, 18, tzinfo=timezone.utc) - timedelta(days=1)).isoformat()
    serial = encode_license_serial(_make_payload("ANNUAL", expired_at), private_key)
    state = service.activate_serial(serial)

    assert state.valid is False
    assert state.status == "expired"


def test_license_service_marks_expired_trial_license(monkeypatch):
    private_key = Ed25519PrivateKey.generate()
    monkeypatch.setattr("licensing.license_crypto.load_public_key", lambda: private_key.public_key())
    monkeypatch.setattr("licensing.license_service.get_machine_fingerprint", lambda: "MACHINE-TRIAL-321")

    service = LicenseService(FakeStorage())
    service.utcnow = lambda: datetime(2026, 3, 19, tzinfo=timezone.utc)

    expired_at = (datetime(2026, 2, 10, tzinfo=timezone.utc)).isoformat()
    serial = encode_license_serial(_make_payload("TRIAL", expired_at), private_key)
    state = service.activate_serial(serial)

    assert state.valid is False
    assert state.status == "expired"
    assert "prueba" in state.message.lower()
