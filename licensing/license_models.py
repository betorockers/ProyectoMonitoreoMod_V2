from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class LicensePayload:
    schema_version: int
    app_id: str
    license_id: str
    edition: str
    license_type: str
    issued_at: str
    expires_at: str | None
    customer_name: str | None = None
    seat_label: str | None = None
    notes: str | None = None

    @property
    def is_perpetual(self) -> bool:
        return self.license_type.upper() == "PERPETUAL"

    @property
    def expiry_datetime(self) -> datetime | None:
        if not self.expires_at:
            return None
        return datetime.fromisoformat(self.expires_at)


@dataclass(slots=True)
class ActivationRecord:
    payload: dict
    signature_b64: str
    serial_hash: str
    bound_machine: str
    activated_at: str
    last_verified_at: str
    activation_source: str = "manual"


@dataclass(slots=True)
class LicenseState:
    valid: bool
    status: str
    message: str
    payload: LicensePayload | None = None
    activation: ActivationRecord | None = None

    @property
    def edition(self) -> str:
        return self.payload.edition if self.payload else "-"

    @property
    def license_type(self) -> str:
        return self.payload.license_type if self.payload else "-"
