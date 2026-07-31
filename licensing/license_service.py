from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone

from config.licensing import APP_LICENSE_ID, LICENSE_EDITIONS, LICENSE_SCHEMA_VERSION, LICENSE_TIME_SKEW_SECONDS, LICENSE_TYPES
from licensing.license_crypto import decode_and_verify_serial, serial_hash
from licensing.license_models import ActivationRecord, LicensePayload, LicenseState
from licensing.license_storage import LicenseStorage
from licensing.machine_fingerprint import get_machine_fingerprint


class LicenseService:
    def __init__(self, storage: LicenseStorage | None = None):
        self.storage = storage or LicenseStorage()

    @staticmethod
    def utcnow() -> datetime:
        return datetime.now(timezone.utc)

    def _payload_from_dict(self, payload_dict: dict) -> LicensePayload:
        return LicensePayload(**payload_dict)

    def _activation_from_dict(self, data: dict) -> ActivationRecord:
        return ActivationRecord(**data)

    def _validate_payload(self, payload: LicensePayload) -> None:
        if payload.schema_version != LICENSE_SCHEMA_VERSION:
            raise ValueError("Version de licencia no compatible")
        if payload.app_id != APP_LICENSE_ID:
            raise ValueError("La licencia no corresponde a este producto")
        if payload.edition not in LICENSE_EDITIONS:
            raise ValueError("Edicion de licencia invalida")
        if payload.license_type not in LICENSE_TYPES:
            raise ValueError("Tipo de licencia invalido")
        if payload.license_type in {"ANNUAL", "TRIAL"} and not payload.expires_at:
            raise ValueError("La licencia temporal no tiene vencimiento")

    def _build_activation(self, payload: LicensePayload, signature_b64: str, serial: str, source: str) -> ActivationRecord:
        now_iso = self.utcnow().isoformat()
        return ActivationRecord(
            payload=asdict(payload),
            signature_b64=signature_b64,
            serial_hash=serial_hash(serial),
            bound_machine=get_machine_fingerprint(),
            activated_at=now_iso,
            last_verified_at=now_iso,
            activation_source=source,
        )

    def get_state(self) -> LicenseState:
        activation_dict = self.storage.load_activation()
        if not activation_dict:
            return LicenseState(False, "missing", "No hay una licencia activa registrada.")

        try:
            activation = self._activation_from_dict(activation_dict)
            payload = self._payload_from_dict(activation.payload)
            self._validate_payload(payload)
        except Exception as exc:
            return LicenseState(False, "invalid", f"La licencia almacenada es invalida: {exc}")

        if activation.bound_machine != get_machine_fingerprint():
            return LicenseState(False, "mismatch", "La licencia pertenece a otro equipo.", payload, activation)

        now = self.utcnow()
        try:
            last_verified = datetime.fromisoformat(activation.last_verified_at)
        except ValueError:
            last_verified = now

        if now.timestamp() + LICENSE_TIME_SKEW_SECONDS < last_verified.timestamp():
            return LicenseState(False, "clock_tamper", "Se detecto una inconsistencia en la fecha del sistema.", payload, activation)

        if not payload.is_perpetual:
            expiry = payload.expiry_datetime
            if expiry:
                expiry_utc = expiry.replace(tzinfo=timezone.utc) if expiry.tzinfo is None else expiry.astimezone(timezone.utc)
                if now > expiry_utc:
                    message = (
                        "La licencia de prueba se encuentra vencida."
                        if payload.license_type == "TRIAL"
                        else "La licencia anual se encuentra vencida."
                    )
                    return LicenseState(False, "expired", message, payload, activation)

        activation.last_verified_at = now.isoformat()
        self.storage.save_activation(asdict(activation))
        self.storage.save_marker("LastLicenseId", payload.license_id)
        self.storage.save_marker("LastLicenseType", payload.license_type)
        self.storage.save_marker("LastEdition", payload.edition)
        self.storage.save_marker("LastStatus", "valid")
        if payload.expires_at:
            self.storage.save_marker("LastExpiry", payload.expires_at)
        return LicenseState(True, "valid", "Licencia valida.", payload, activation)

    def activate_serial(self, serial: str, source: str = "manual") -> LicenseState:
        try:
            payload, signature_b64 = decode_and_verify_serial(serial)
            self._validate_payload(payload)
        except Exception as exc:
            return LicenseState(False, "invalid", f"Serial invalido: {exc}")

        activation = self._build_activation(payload, signature_b64, serial, source)
        self.storage.save_activation(asdict(activation))
        self.storage.clear_pending_serial()
        return self.get_state()

    def consume_pending_serial(self) -> LicenseState | None:
        pending = self.storage.load_pending_serial()
        if not pending:
            return None
        state = self.activate_serial(pending, source="installer")
        if not state.valid:
            self.storage.clear_pending_serial()
        return state

    def clear_license(self) -> None:
        self.storage.clear_activation()

    def get_summary(self) -> dict:
        state = self.get_state()
        payload = state.payload
        activation = state.activation
        return {
            "valid": state.valid,
            "status": state.status,
            "message": state.message,
            "edition": payload.edition if payload else "-",
            "license_type": payload.license_type if payload else "-",
            "license_id": payload.license_id if payload else "-",
            "expires_at": payload.expires_at if payload else "-",
            "customer_name": payload.customer_name if payload else "-",
            "bound_machine": activation.bound_machine if activation else get_machine_fingerprint(),
        }
