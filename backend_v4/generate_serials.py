import os
import hashlib
import sqlite3
import random
import string
from typing import List

DB_PATH = os.path.join(os.path.dirname(__file__), "app", "infrastructure", "..", "..", "argos_guard.db")

TIERS = {
    "BASICO": 1000,
    "ESTANDAR": 1000,
    "ENTERPRISE": 1000,
    "DEV": 2,
    "TESTER": 3
}

def generate_random_string(length: int) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def generate_serial(tier: str) -> str:
    # Example: ARGOS-TRIAL-A1B2-C3D4-E5F6
    parts = [generate_random_string(4) for _ in range(3)]
    return f"ARGOS-{tier}-" + "-".join(parts)

def hash_serial(serial: str) -> str:
    return hashlib.sha256(serial.encode()).hexdigest()

def main():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}. Please run the app once to initialize.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Create table if not exists (just in case)
    c.execute('''
        CREATE TABLE IF NOT EXISTS valid_licenses (
            license_hash TEXT PRIMARY KEY,
            tier TEXT NOT NULL
        )
    ''')

    # Clear existing valid licenses
    c.execute('DELETE FROM valid_licenses')

    all_serials = []
    
    print("Generando seriales...")
    
    # Generate the single Trial key (10 digits alphanumeric)
    trial_key = generate_random_string(10)
    trial_hash = hash_serial(trial_key)
    all_serials.append(f"TRIAL: {trial_key}")
    c.execute('INSERT INTO valid_licenses (license_hash, tier) VALUES (?, ?)', (trial_hash, "TRIAL"))
    
    for tier, count in TIERS.items():
        for _ in range(count):
            serial = generate_serial(tier)
            hashed = hash_serial(serial)
            all_serials.append(f"{tier}: {serial}")
            c.execute('INSERT INTO valid_licenses (license_hash, tier) VALUES (?, ?)', (hashed, tier))

    conn.commit()
    conn.close()

    # Escribir a un archivo de texto
    out_file = os.path.join(os.path.dirname(__file__), "serials_generados.txt")
    with open(out_file, "w") as f:
        f.write("# Seriales Generados para Argos Guard Enterprise\n\n")
        current_tier = ""
        for line in all_serials:
            tier = line.split(":")[0]
            if tier != current_tier:
                f.write(f"\n## TRAMO: {tier}\n")
                current_tier = tier
            f.write(line.split(": ")[1] + "\n")

    print(f"✅ Se han generado {sum(TIERS.values())} seriales.")
    print(f"✅ Los hashes se guardaron en {DB_PATH}")
    print(f"✅ Las claves crudas se guardaron en {out_file} (NUNCA COMPARTIR ESTE ARCHIVO PUBLICAMENTE)")

if __name__ == "__main__":
    main()
