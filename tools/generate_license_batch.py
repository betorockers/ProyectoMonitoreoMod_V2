from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography.hazmat.primitives import serialization

from config.licensing import APP_LICENSE_ID, LICENSE_SCHEMA_VERSION
from licensing.license_crypto import encode_license_serial


def build_payload(index: int, edition: str, license_type: str, customer: str) -> dict:
    issued = datetime.now(timezone.utc)
    expires = None
    normalized_type = license_type.upper()
    if normalized_type == "ANNUAL":
        expires = (issued + timedelta(days=365)).isoformat()
    elif normalized_type == "TRIAL":
        expires = (issued + timedelta(days=30)).isoformat()

    return {
        "schema_version": LICENSE_SCHEMA_VERSION,
        "app_id": APP_LICENSE_ID,
        "license_id": f"{edition[:3]}-{license_type[:3]}-{index:04d}",
        "edition": edition.upper(),
        "license_type": normalized_type,
        "issued_at": issued.isoformat(),
        "expires_at": expires,
        "customer_name": customer,
        "seat_label": f"SERIE-{index:04d}",
        "notes": "Emitida por herramienta interna de ANVIC",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera un lote de seriales firmados.")
    parser.add_argument("--private-key", required=True, help="Ruta a la clave privada PEM de firma")
    parser.add_argument("--output", required=True, help="CSV de salida")
    parser.add_argument("--count", type=int, required=True, help="Cantidad de seriales a generar")
    parser.add_argument("--edition", required=True, choices=["STANDARD", "ADVANCED", "PRO"])
    parser.add_argument("--license-type", required=True, choices=["PERPETUAL", "ANNUAL", "TRIAL"])
    parser.add_argument("--customer", default="ANVIC")
    args = parser.parse_args()

    private_key = serialization.load_pem_private_key(Path(args.private_key).read_bytes(), password=None)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["license_id", "edition", "license_type", "expires_at", "serial"])
        writer.writeheader()
        for index in range(1, args.count + 1):
            payload = build_payload(index, args.edition, args.license_type, args.customer)
            serial = encode_license_serial(payload, private_key)
            writer.writerow(
                {
                    "license_id": payload["license_id"],
                    "edition": payload["edition"],
                    "license_type": payload["license_type"],
                    "expires_at": payload["expires_at"] or "",
                    "serial": serial,
                }
            )

    print(f"Lote generado en {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
