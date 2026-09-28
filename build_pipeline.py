import os
import shutil
import subprocess
import sys
import time

# ── Archivos a transpilar con Cython ──────────────────────────────────────
TARGET_FILES = [
    "network_tools_logic.py",
    "auth_manager.py",
    "key_manager.py",
    "secure_config_manager.py",
    "licensing/license_service.py",
    "licensing/license_crypto.py",
    "licensing/license_storage.py",
    "licensing/machine_fingerprint.py",
]

# ── Configuracion de firma ─────────────────────────────────────────────────
CERT_SCRIPT   = r"E:\Certificados\firmar_anvic.ps1"
INSTALLER_OUT = r"e:\AnvicNetworkMonitorV2.1\Output\ANS_Setup_V2.2.3.exe"
DIST_EXE      = r"e:\AnvicNetworkMonitorV2.1\dist\AnvicNetworkSentinel\AnvicNetworkSentinel.exe"

# Servidores de timestamp RFC 3161 (se prueba en orden)
TIMESTAMP_SERVERS = [
    "http://timestamp.digicert.com",
    "http://timestamp.sectigo.com",
    "http://timestamp.globalsign.com/scripts/timstamp.dll",
]

def rename_to_bak():
    for f in TARGET_FILES:
        if os.path.exists(f):
            os.rename(f, f + ".bak")

def restore_from_bak():
    for f in TARGET_FILES:
        if os.path.exists(f + ".bak"):
            if os.path.exists(f):
                os.remove(f)
            os.rename(f + ".bak", f)

def get_iscc_path():
    search_dirs = [
        r'D:\Inno Setup 7',
        'C:\\Program Files (x86)',
        'C:\\Program Files',
        'C:\\Users\\BetoRock Toledo\\AppData\\Local\\Programs'
    ]
    for d in search_dirs:
        if not os.path.exists(d):
            continue
        for r, _, fs in os.walk(d):
            for f in fs:
                if f.lower() == 'iscc.exe':
                    return os.path.join(r, f)
    return None

def get_signtool_path():
    """Busca signtool.exe en las rutas tipicas del Windows SDK."""
    sdk_base = r"C:\Program Files (x86)\Windows Kits\10\bin"
    if os.path.exists(sdk_base):
        for root, dirs, files in os.walk(sdk_base):
            for f in files:
                if f.lower() == "signtool.exe" and "x64" in root:
                    return os.path.join(root, f)
    # Fallback: esperar que este en PATH
    return "signtool.exe"

def sign_file(filepath, signtool, cert_name="Anvic Network Sentinel"):
    """Firma un archivo con reintentos en distintos timestamp servers."""
    if not os.path.exists(filepath):
        print(f"  [SKIP] No encontrado: {filepath}")
        return False

    print(f"  Firmando: {os.path.basename(filepath)}")
    for ts in TIMESTAMP_SERVERS:
        try:
            result = subprocess.run([
                signtool, "sign",
                "/fd", "SHA256",
                "/td", "SHA256",
                "/tr", ts,
                "/n", cert_name,
                "/a",
                filepath
            ], capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                print(f"  [OK] Firmado | Timestamp: {ts}")
                return True
            else:
                print(f"  [!] Fallo con {ts}: {result.stderr.strip()[:100]}")
        except subprocess.TimeoutExpired:
            print(f"  [!] Timeout con {ts}")
        except Exception as e:
            print(f"  [!] Error: {e}")

    print("  [WARN] No se pudo obtener timestamp. Firmando sin timestamp...")
    try:
        subprocess.run([signtool, "sign", "/fd", "SHA256", "/n", cert_name, "/a", filepath],
                       check=True, capture_output=True)
        print("  [OK] Firmado sin timestamp.")
        return True
    except Exception as e:
        print(f"  [ERROR] Firma fallida: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("  ANVIC NETWORK SENTINEL v2.2.3 — BUILD PIPELINE (COMERCIAL DÍA CERO)")
    print("="*60 + "\n")

    print("=== PASO 0: Configurando Perfil Comercial Día Cero ===")
    comm_profile = os.path.join(os.path.dirname(__file__), "build_profiles", "commercial.json")
    target_profile = os.path.join(os.path.dirname(__file__), "build_profile.json")
    if os.path.exists(comm_profile):
        shutil.copy2(comm_profile, target_profile)
        print("  [OK] Perfil Comercial activo (sin marcas dev, con licenciamiento industrial y siembra inicial).")

    print("\n=== PASO 1: Transpilacion Cython ===")
    subprocess.run([sys.executable, "build_cython.py"], check=True)

    print("\n=== PASO 2: Ocultando archivos .py (Backups) ===")
    rename_to_bak()

    try:
        print("\n=== PASO 3: Empaquetando con PyInstaller ===")
        subprocess.run([sys.executable, "-m", "PyInstaller", "--clean", "-y", "AnvicNetworkSentinel.spec"], check=True)
    finally:
        print("\n=== PASO 4: Restaurando archivos .py ===")
        restore_from_bak()

    print("\n=== PASO 5: Firma Digital de Ejecutable Principal (DIST_EXE) ===")
    signtool = get_signtool_path()
    print(f"  signtool: {signtool}")
    sign_file(DIST_EXE, signtool)

    print("\n=== PASO 6: Compilando instalador Inno Setup ===")
    iscc_path = get_iscc_path()
    if iscc_path:
        sign_cmd = f'$q{signtool}$q sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /n $qAnvic Network Sentinel$q /a $f'
        cmd_line = f'"{iscc_path}" /dUseSignTool "/SMySignTool={sign_cmd}" "e:\\AnvicNetworkMonitorV2.1\\installer.iss"'
        print(f"Ejecutando ISCC: {cmd_line}")
        try:
            subprocess.run(cmd_line, shell=True, check=True)
            print("[OK] Instalador generado y firmado con Inno Setup.")
        except subprocess.CalledProcessError:
            print("[WARN] Falló firma interna en ISCC. Compilando instalador limpio y firmando post-proceso...")
            cmd_line_fallback = f'"{iscc_path}" "e:\\AnvicNetworkMonitorV2.1\\installer.iss"'
            subprocess.run(cmd_line_fallback, shell=True, check=True)
            print("[OK] Instalador generado con Inno Setup (modo limpio).")
    else:
        print("[ERROR] No se encontro ISCC.exe. Instala Inno Setup.")
        sys.exit(1)

    print("\n=== PASO 7: Firma Digital Authenticode del Instalador ===")
    sign_file(INSTALLER_OUT, signtool)

    # Verificar la firma del instalador
    print("\n=== PASO 7: Verificacion de Firma ===")
    try:
        verify = subprocess.run(
            [signtool, "verify", "/pa", "/v", INSTALLER_OUT],
            capture_output=True, text=True
        )
        if verify.returncode == 0:
            print("[OK] Firma verificada correctamente.")
        else:
            print(f"[WARN] La verificacion reporto advertencias:\n{verify.stdout[:300]}")
    except Exception as e:
        print(f"[WARN] No se pudo verificar: {e}")

    print("\n" + "="*60)
    print("  COMPILACION v2.2.3 COMPLETADA EXITOSAMENTE")
    print(f"  Instalador: {INSTALLER_OUT}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()

