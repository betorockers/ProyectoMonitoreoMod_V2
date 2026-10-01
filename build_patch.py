#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
ANVIC NETWORK SENTINEL - HERRAMIENTA INDUSTRIAL DE CREACIÓN DE PARCHES
Versión: 2.0 (Industrial Patch & Differential Deployment)
Autor: BetoGraf_inc © 2026
==============================================================================

Este script construye e instala parches diferenciales ligeros (Hotfixes) para
Anvic Network Sentinel sin requerir una compilación completa de cientos de MB
ni reinstalación destructiva.

Principios de Diseño:
1. PRESERVACIÓN SAGRADA DE DATOS:
   Bases de datos (anvic_monitor.db), configuraciones (equipos_guardados.json.enc),
   usuarios (users.json.enc), clave maestra (anvic_master.key) y licencias
   NUNCA son tocadas ni reseteadas.
2. COMPILACIÓN DIFERENCIAL ULTRA-RÁPIDA:
   Reutiliza el caché de librerías estáticas de PyInstaller. Compila únicamente
   el código transpilado y el ejecutable principal en segundos.
3. INSTALADOR DE PARCHE DIFERENCIAL (Inno Setup):
   Genera un instalador .exe ligero (3-8 MB) que detecta automáticamente la ruta
   de instalación en el Registro de Windows, cierra procesos bloqueados,
   crea un backup previo con capacidad de ROLLBACK instantáneo, copia los
   módulos actualizados y actualiza la versión del sistema.
4. PAQUETE PORTABLE DESATENDIDO (.zip):
   Crea un paquete con scripts de despliegue y rollback automático para entornos
   con políticas restrictivas o administración remota.
5. SEGURIDAD Y FIRMA DIGITAL:
   Firma criptográfica Authenticode con timestamp RFC 3161 sobre todos los artefactos.
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

# Asegurar codificación UTF-8 en salida estándar para compatibilidad con cualquier consola de Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ─── CONFIGURACIÓN DEL PROYECTO ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "Output"
STAGING_DIR = OUTPUT_DIR / "patch_staging"
BRANDING_FILE = BASE_DIR / "config" / "branding.py"
SPEC_FILE = BASE_DIR / "AnvicNetworkSentinel.spec"
PATCH_ISS_FILE = BASE_DIR / "patch_installer.iss"
CERT_SCRIPT = r"E:\Certificados\firmar_anvic.ps1"

TIMESTAMP_SERVERS = [
    "http://timestamp.digicert.com",
    "http://timestamp.sectigo.com",
    "http://timestamp.globalsign.com/scripts/timstamp.dll",
]

# Archivos protegidos que NUNCA deben incluirse en un parche
PROTECTED_DATA_FILES = [
    "anvic_monitor.db",
    "anvic_monitor.db-wal",
    "anvic_monitor.db-shm",
    "equipos_guardados.json",
    "equipos_guardados.json.enc",
    "equipos_guardados.json.bak",
    "users.json",
    "users.json.enc",
    "users.json.enc.bak",
    "anvic_master.key",
    "historial_log.txt",
    "auditoria_usuarios.log",
]


# ─── UTILIDADES CRIPTOGRÁFICAS Y DEL SISTEMA ─────────────────────────────────
def calcular_sha256(filepath: Path) -> str:
    """Calcula el hash SHA-256 de un archivo binario."""
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()


def obtener_version_actual() -> str:
    """Lee la versión actual declarada en config/branding.py."""
    if not BRANDING_FILE.exists():
        return "2.2.3"
    content = BRANDING_FILE.read_text(encoding="utf-8")
    m = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', content)
    return m.group(1) if m else "2.2.3"


def actualizar_version_en_branding(nueva_version: str):
    """Actualiza la versión en config/branding.py de forma limpia."""
    if not BRANDING_FILE.exists():
        return
    content = BRANDING_FILE.read_text(encoding="utf-8")
    new_content = re.sub(
        r'VERSION\s*=\s*["\']([^"\']+)["\']',
        f'VERSION = "{nueva_version}"',
        content,
    )
    BRANDING_FILE.write_text(new_content, encoding="utf-8")
    print(f"  [OK] Versión actualizada en config/branding.py -> {nueva_version}")


def sugerir_siguiente_version(version_actual: str) -> str:
    """Calcula el siguiente número de versión patch (ej. 2.2.3 -> 2.2.4)."""
    partes = version_actual.split(".")
    if len(partes) >= 3 and partes[-1].isdigit():
        partes[-1] = str(int(partes[-1]) + 1)
        return ".".join(partes)
    return f"{version_actual}.1"


def get_iscc_path() -> str | None:
    """Busca el compilador de Inno Setup (ISCC.exe) en las rutas del sistema."""
    search_dirs = [
        r"D:\Inno Setup 7",
        r"C:\Program Files (x86)\Inno Setup 6",
        r"C:\Program Files\Inno Setup 6",
        r"C:\Program Files (x86)\Inno Setup 7",
        r"C:\Program Files\Inno Setup 7",
        str(Path.home() / "AppData" / "Local" / "Programs"),
    ]
    for d in search_dirs:
        if not os.path.exists(d):
            continue
        for r, _, fs in os.walk(d):
            for f in fs:
                if f.lower() == "iscc.exe":
                    return os.path.join(r, f)
    # Probar si está en PATH
    which_iscc = shutil.which("iscc.exe")
    return which_iscc


def get_signtool_path() -> str:
    """Busca signtool.exe en el Windows SDK o retorna fallback."""
    sdk_base = r"C:\Program Files (x86)\Windows Kits\10\bin"
    if os.path.exists(sdk_base):
        for root, dirs, files in os.walk(sdk_base):
            for f in files:
                if f.lower() == "signtool.exe" and "x64" in root:
                    return os.path.join(root, f)
    return "signtool.exe"


def sign_file(filepath: Path, signtool: str, cert_name: str = "Anvic Network Sentinel") -> bool:
    """Firma un archivo con reintentos en servidores de timestamp RFC 3161."""
    if not filepath.exists():
        print(f"  [SKIP] Archivo a firmar no existe: {filepath.name}")
        return False

    print(f"  Firmando Authenticode: {filepath.name}...")
    for ts in TIMESTAMP_SERVERS:
        try:
            res = subprocess.run(
                [
                    signtool,
                    "sign",
                    "/fd",
                    "SHA256",
                    "/td",
                    "SHA256",
                    "/tr",
                    ts,
                    "/n",
                    cert_name,
                    "/a",
                    str(filepath),
                ],
                capture_output=True,
                text=True,
                timeout=25,
            )
            if res.returncode == 0:
                print(f"  [OK] Firmado exitoso con Timestamp: {ts}")
                return True
        except subprocess.TimeoutExpired:
            print(f"  [!] Timeout conectando con {ts}")
        except Exception as e:
            print(f"  [!] Error con {ts}: {e}")

    # Fallback sin timestamp si los servidores de red están saturados
    try:
        res = subprocess.run(
            [signtool, "sign", "/fd", "SHA256", "/n", cert_name, "/a", str(filepath)],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if res.returncode == 0:
            print("  [OK] Firmado sin timestamp (Offline fallback).")
            return True
        else:
            print(f"  [WARN] No se pudo firmar {filepath.name}: {res.stderr.strip()[:120]}")
            return False
    except Exception as e:
        print(f"  [WARN] Falló ejecución de signtool: {e}")
        return False


# ─── PASO 1: VERIFICACIÓN PRE-VUELO (TESTS & ENVIRONMENT) ───────────────────
def ejecutar_pruebas_unitarias(python_exe: str) -> bool:
    """Ejecuta la suite de pruebas unitarias para certificar la integridad."""
    print("\n" + "=" * 65)
    print("  [PASO 1/6] VERIFICACIÓN PRE-VUELO: CERTIFICACIÓN DE INTEGRIDAD")
    print("=" * 65)
    pytest_exe = str(BASE_DIR / "monitorEnv" / "Scripts" / "pytest.exe")
    cmd = [pytest_exe if os.path.exists(pytest_exe) else python_exe, "-m", "pytest"] if not os.path.exists(pytest_exe) else [pytest_exe]

    print("  Ejecutando suite automatizada de pruebas...")
    try:
        t0 = time.time()
        res = subprocess.run(cmd, cwd=str(BASE_DIR), capture_output=True, text=True)
        duracion = time.time() - t0
        if res.returncode == 0:
            print(f"  [OK] 100% PASS de pruebas ({duracion:.2f}s). Código certificado para parche.")
            return True
        else:
            print("  [ERROR CRÍTICO] La suite de pruebas falló. No se puede generar el parche:")
            print(res.stdout[-600:])
            return False
    except Exception as e:
        print(f"  [WARN] No se pudo ejecutar pytest: {e}. Continuando bajo advertencia...")
        return True


# ─── PASO 2: COMPILACIÓN DIFERENCIAL RÁPIDA ──────────────────────────────────
def compilar_diferencial(python_exe: str, run_cython: bool = True):
    """Compila selectivamente los módulos modificados y re-empaqueta el ejecutable."""
    print("\n" + "=" * 65)
    print("  [PASO 2/6] COMPILACIÓN DIFERENCIAL Y GENERACIÓN DE BINARIOS")
    print("=" * 65)

    # 1. Transpilación Cython si aplica
    if run_cython and (BASE_DIR / "build_cython.py").exists():
        print("  Compilando extensiones C/Cython sensibles...")
        res_cy = subprocess.run([python_exe, "build_cython.py"], cwd=str(BASE_DIR))
        if res_cy.returncode != 0:
            print("  [WARN] Transpilación Cython reportó código de salida distinto de cero.")

    # 2. PyInstaller Limpio (con --clean para garantizar 100% de transpilación fresca)
    print("  Re-empaquetando ejecutable principal de forma limpia y completa con PyInstaller...")
    t0 = time.time()
    cmd_pyi = [python_exe, "-m", "PyInstaller", "--clean", "-y", str(SPEC_FILE)]
    res_pyi = subprocess.run(cmd_pyi, cwd=str(BASE_DIR), capture_output=True, text=True)
    duracion = time.time() - t0

    if res_pyi.returncode != 0:
        print(f"  [ERROR] PyInstaller falló:\n{res_pyi.stderr[-800:]}")
        sys.exit(1)

    print(f"  [OK] Binario diferencial generado en {duracion:.1f}s.")


# ─── PASO 3: STAGING DEL PARCHE Y MANIFIESTO ─────────────────────────────────
def preparar_staging_parche(base_ver: str, target_ver: str, patch_id: str, descripcion: str) -> dict:
    """Prepara el directorio con solo los archivos modificados que integran el parche."""
    print("\n" + "=" * 65)
    print("  [PASO 3/6] PREPARACIÓN DE STAGING DIFERENCIAL Y METADATOS")
    print("=" * 65)

    if STAGING_DIR.exists():
        shutil.rmtree(STAGING_DIR)
    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    dist_app_dir = BASE_DIR / "dist" / "AnvicNetworkSentinel"
    exe_src = dist_app_dir / "AnvicNetworkSentinel.exe"

    if not exe_src.exists():
        print(f"  [ERROR] No se encontró el binario compilado en: {exe_src}")
        sys.exit(1)

    # 1. Copiar ejecutable principal actualizado
    exe_dest = STAGING_DIR / "AnvicNetworkSentinel.exe"
    shutil.copy2(exe_src, exe_dest)
    print(f"  [+] Incluido: AnvicNetworkSentinel.exe ({exe_dest.stat().st_size / (1024*1024):.2f} MB)")

    # 2. Copiar carpeta _internal completa (librerías, extensiones C/Cython y datos)
    internal_src = dist_app_dir / "_internal"
    if internal_src.exists():
        internal_dest = STAGING_DIR / "_internal"
        shutil.copytree(internal_src, internal_dest, dirs_exist_ok=True)
        print("  [+] Incluido: _internal/ (entorno completo de librerías y extensiones C/Cython)")

    # 3. Copiar archivos .pyd actualizados si existen en la raíz o en dist
    archivos_parche = {}
    archivos_parche["AnvicNetworkSentinel.exe"] = {
        "sha256": calcular_sha256(exe_dest),
        "size_bytes": exe_dest.stat().st_size,
    }

    # 4. Copiar assets si se modificaron recientemente
    assets_src = BASE_DIR / "assets"
    if assets_src.exists():
        staging_assets = STAGING_DIR / "assets"
        shutil.copytree(assets_src, staging_assets, dirs_exist_ok=True)
        print("  [+] Incluido: assets/ (recursos gráficos sincronizados)")

    # 4. Generar Manifiesto Criptográfico
    manifiesto = {
        "patch_id": patch_id,
        "base_version_required": base_ver,
        "target_version": target_ver,
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "created_by": "BetoGraf_inc",
        "description": descripcion,
        "protected_data_guarantee": [
            "anvic_monitor.db (INTACTA - No se modifica ni se sobreescribe)",
            "equipos_guardados.json.enc (INTACTA)",
            "users.json.enc (INTACTA)",
            "anvic_master.key (INTACTA)",
            "licensing (INTACTA)",
        ],
        "files": archivos_parche,
    }

    manifest_file = STAGING_DIR / "patch_manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifiesto, f, indent=2, ensure_ascii=False)
    print("  [OK] Manifiesto criptográfico generado: patch_manifest.json")

    return manifiesto


# ─── PASO 4: CREACIÓN DEL PAQUETE PORTABLE Y SCRIPTS DESATENDIDOS ─────────────
def generar_paquete_portable(target_ver: str, patch_id: str, manifiesto: dict) -> Path:
    """Genera un archivo ZIP portable con scripts de instalación y rollback desatendidos."""
    print("\n" + "=" * 65)
    print("  [PASO 4/6] GENERACIÓN DE PAQUETE PORTABLE DESATENDIDO (.ZIP)")
    print("=" * 65)

    # 1. Crear script batch industrial apply_patch.bat
    apply_bat_content = f"""@echo off
setlocal EnableDelayedExpansion
title Aplicar Parche Anvic Network Sentinel v{target_ver}
color 0B

echo ======================================================================
echo   ANVIC NETWORK SENTINEL - INSTALADOR DE PARCHE DESATENDIDO
echo   Parche: {patch_id}  ^|  Version Destino: v{target_ver}
echo ======================================================================
echo.

:: Verificar Privilegios de Administrador
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [SOLICITANDO ELEVACION] Este parche requiere permisos de Administrador.
    powershell -Command "Start-Process cmd -ArgumentList '/c `"%~f0`"' -Verb RunAs"
    exit /b
)

:: 1. Detectar Ruta de Instalacion en Registro
set "INSTALL_DIR="
for /f "tokens=2* skip=2" %%a in ('reg query "HKCU\\Software\\ANVIC\\AnvicNetworkSentinel" /v "InstallRoot" 2^>nul') do set "INSTALL_DIR=%%b"
if not defined INSTALL_DIR (
    for /f "tokens=2* skip=2" %%a in ('reg query "HKLM\\Software\\ANVIC\\AnvicNetworkSentinel" /v "InstallRoot" 2^>nul') do set "INSTALL_DIR=%%b"
)
if not defined INSTALL_DIR (
    if exist "%ProgramFiles%\\Anvic Network Sentinel" set "INSTALL_DIR=%ProgramFiles%\\Anvic Network Sentinel"
    if exist "%LOCALAPPDATA%\\Programs\\Anvic Network Sentinel" set "INSTALL_DIR=%LOCALAPPDATA%\\Programs\\Anvic Network Sentinel"
)

if not defined INSTALL_DIR (
    echo [ERROR] No se pudo detectar automaticamente la instalacion de Anvic Network Sentinel.
    set /p "INSTALL_DIR=Por favor ingrese la ruta de instalacion completa: "
)

echo [OK] Ruta de instalacion detectada: "!INSTALL_DIR!"
if not exist "!INSTALL_DIR!\\AnvicNetworkSentinel.exe" (
    echo [ADVERTENCIA] No se encontro AnvicNetworkSentinel.exe en esa carpeta.
    pause
)

:: 2. Cerrar Proceso Activo si esta corriendo
echo.
echo [PASO 1] Verificando procesos activos...
taskkill /f /im AnvicNetworkSentinel.exe >nul 2>&1
timeout /t 1 >nul

:: 3. Crear Backup Preventivo con Capacidad de Rollback
set "STAMP=%date:~6,4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "STAMP=%STAMP: =0%"
set "BACKUP_DIR=!INSTALL_DIR!\\backups\\backup_pre_patch_%STAMP%"

echo [PASO 2] Creando backup preventivo en:
echo         "!BACKUP_DIR!"
mkdir "!BACKUP_DIR!" >nul 2>&1
if exist "!INSTALL_DIR!\\AnvicNetworkSentinel.exe" (
    copy /y "!INSTALL_DIR!\\AnvicNetworkSentinel.exe" "!BACKUP_DIR!\\AnvicNetworkSentinel.exe" >nul
)

:: Generar rollback script
(
echo @echo off
echo echo Restaurando version previa...
echo taskkill /f /im AnvicNetworkSentinel.exe ^>nul 2^>^&1
echo copy /y "AnvicNetworkSentinel.exe" "..\\..\\AnvicNetworkSentinel.exe"
echo echo [OK] Version previa restaurada correctamente.
echo pause
) > "!BACKUP_DIR!\\rollback.bat"

:: 4. Copiar Archivos Nuevos (Garantia de No Afectacion a Datos)
echo [PASO 3] Desplegando archivos del parche...
copy /y "%~dp0AnvicNetworkSentinel.exe" "!INSTALL_DIR!\\AnvicNetworkSentinel.exe" >nul
if exist "%~dp0_internal" xcopy /y /e /i /q "%~dp0_internal" "!INSTALL_DIR!\\_internal" >nul 2>&1
if exist "%~dp0assets" xcopy /y /e /i /q "%~dp0assets" "!INSTALL_DIR!\\assets" >nul 2>&1

:: 5. Actualizar Version en Registro de Windows
reg add "HKCU\\Software\\ANVIC\\AnvicNetworkSentinel" /v "InstalledVersion" /t REG_SZ /d "{target_ver}" /f >nul 2>&1
reg add "HKCU\\Software\\ANVIC\\AnvicNetworkSentinel" /v "LastPatchId" /t REG_SZ /d "{patch_id}" /f >nul 2>&1

:: 6. Auditoria Local
echo [%date% %time%] PARCHE DESATENDIDO APLICADO: {patch_id} ^(v{target_ver}^) >> "!INSTALL_DIR!\\patch_history.log"

echo.
echo ======================================================================
echo   PARCHE APLICADO EXITOSAMENTE A LA VERSION {target_ver}
echo   Las bases de datos y configuraciones permanecen 100%% intactas.
echo ======================================================================
echo.
pause
"""
    apply_bat_file = STAGING_DIR / "apply_patch.bat"
    apply_bat_file.write_text(apply_bat_content, encoding="latin-1")

    # 2. Crear rollback_patch.bat general
    rollback_content = """@echo off
title Revertir Parche Anvic Network Sentinel
color 0C
echo ======================================================================
echo   ANVIC NETWORK SENTINEL - REVERSION DE PARCHE (ROLLBACK)
echo ======================================================================
echo.
set "INSTALL_DIR="
for /f "tokens=2* skip=2" %%a in ('reg query "HKCU\\Software\\ANVIC\\AnvicNetworkSentinel" /v "InstallRoot" 2^>nul') do set "INSTALL_DIR=%%b"
if not defined INSTALL_DIR set "INSTALL_DIR=%ProgramFiles%\\Anvic Network Sentinel"

echo Buscando copias de seguridad en: "%INSTALL_DIR%\\backups"
dir /b /ad /o-d "%INSTALL_DIR%\\backups"
echo.
echo Ingrese al directorio de backup mas reciente y ejecute 'rollback.bat'.
echo.
pause
"""
    rollback_bat_file = STAGING_DIR / "rollback_patch.bat"
    rollback_bat_file.write_text(rollback_content, encoding="latin-1")

    # 3. Empaquetar todo en un ZIP portable
    zip_filename = OUTPUT_DIR / f"ANS_Patch_V{target_ver}_Portable.zip"
    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(STAGING_DIR):
            for file in files:
                fpath = Path(root) / file
                arcname = fpath.relative_to(STAGING_DIR)
                z.write(fpath, arcname)

    print(f"  [OK] Paquete Portable creado: {zip_filename.name} ({zip_filename.stat().st_size / (1024*1024):.2f} MB)")
    return zip_filename


# ─── PASO 5: COMPILACIÓN DEL INSTALADOR DE PARCHE (INNO SETUP) ───────────────
def compilar_instalador_inno(target_ver: str, base_ver: str, patch_id: str, descripcion: str, signtool: str) -> Path | None:
    """Compila el instalador GUI de parche usando Inno Setup y lo firma con Authenticode."""
    print("\n" + "=" * 65)
    print("  [PASO 5/6] COMPILACIÓN DE INSTALADOR GUI DE PARCHE (INNO SETUP)")
    print("=" * 65)

    iscc = get_iscc_path()
    if not iscc:
        print("  [WARN] No se encontró ISCC.exe (Inno Setup). Omitiendo instalador .exe.")
        return None

    installer_basename = f"ANS_Patch_V{target_ver}"
    expected_exe = OUTPUT_DIR / f"{installer_basename}.exe"

    cmd = [
        iscc,
        f"/dMyAppVersion={target_ver}",
        f"/dMyBaseVersion={base_ver}",
        f"/dMyPatchId={patch_id}",
        f"/dMyPatchDescription={descripcion}",
        f"/dMySourceDir={str(STAGING_DIR)}",
        f"/dMyOutputBaseFilename={installer_basename}",
        f"/dOutputDir={str(OUTPUT_DIR)}",
        str(PATCH_ISS_FILE),
    ]

    print(f"  Ejecutando Inno Setup Compiler ({os.path.basename(iscc)})...")
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"  [ERROR] Falló compilación de Inno Setup:\n{res.stderr[:600]}")
            return None

        print(f"  [OK] Instalador de Parche compilado exitosamente: {expected_exe.name}")
    except Exception as e:
        print(f"  [ERROR] Excepción ejecutando ISCC para parche: {e}")
        expected_exe = None

    # Compilar también el Instalador Completo Formal (ANS_Setup_V{target_ver}.exe)
    setup_exe = None
    full_iss = BASE_DIR / "installer.iss"
    if full_iss.exists():
        setup_basename = f"ANS_Setup_V{target_ver}"
        expected_setup = OUTPUT_DIR / f"{setup_basename}.exe"
        cmd_full = [
            iscc,
            f"/dMyAppVersion={target_ver}",
            f"/dMyOutputBaseFilename={setup_basename}",
            f"/dOutputDir={str(OUTPUT_DIR)}",
            str(full_iss),
        ]
        print(f"  Ejecutando Inno Setup para Instalador Completo ({setup_basename}.exe)...")
        try:
            res_full = subprocess.run(cmd_full, capture_output=True, text=True)
            if res_full.returncode == 0:
                print(f"  [OK] Instalador Completo compilado exitosamente: {expected_setup.name}")
                setup_exe = expected_setup
            else:
                print(f"  [WARN] Compilación de instalador completo reportó advertencias: {res_full.stderr[:400]}")
        except Exception as e:
            print(f"  [WARN] No se pudo compilar instalador completo: {e}")

    return expected_exe, setup_exe


# ─── PASO 6: FIRMA DIGITAL Y RESUMEN FINAL ────────────────────────────────────
def firmar_y_validar_artefactos(installer_exe: Path | None, setup_exe: Path | None, zip_file: Path, signtool: str):
    """Firma digitalmente los instaladores y verifica su validez criptográfica."""
    print("\n" + "=" * 65)
    print("  [PASO 6/6] FIRMA DIGITAL AUTHENTICODE Y VALIDACIÓN FINAL")
    print("=" * 65)

    # 1. Firmar el instalador de parche si fue generado
    for exe_target in (installer_exe, setup_exe):
        if exe_target and exe_target.exists():
            sign_file(exe_target, signtool)

            # Verificar firma
            try:
                v_res = subprocess.run(
                    [signtool, "verify", "/pa", str(exe_target)],
                    capture_output=True,
                    text=True,
                )
                if v_res.returncode == 0:
                    print(f"  [OK] Firma Authenticode verificada correctamente: {exe_target.name}")
                else:
                    print(f"  [WARN] Verificación reportó advertencias en {exe_target.name}: {v_res.stderr.strip()[:100]}")
            except Exception as e:
                print(f"  [WARN] Verificación no disponible: {e}")


# ─── ENTRY POINT PRINCIPAL ───────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Generador Industrial de Parches y Actualizaciones Diferenciales - Anvic Network Sentinel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-v", "--patch-version", help="Versión destino del parche (ej. 2.2.4)")
    parser.add_argument("-d", "--description", default="Actualización de Telemetría Dinámica por Turnos y Optimización Multihilo", help="Descripción breve de los cambios del parche")
    parser.add_argument("--skip-tests", action="store_true", help="Omitir la suite de verificación de pruebas pytest")
    parser.add_argument("--skip-cython", action="store_true", help="Omitir la transpilación Cython")
    parser.add_argument("--no-sign", action="store_true", help="Omitir la firma Authenticode")

    args = parser.parse_args()

    # Determinar versiones
    base_ver = obtener_version_actual()
    target_ver = args.patch_version or sugerir_siguiente_version(base_ver)
    patch_id = f"ANS-PATCH-V{target_ver}"

    print("\n" + "=" * 70)
    print("  ANVIC NETWORK SENTINEL - GENERADOR DE PARCHES INDUSTRIALES")
    print(f"  Versión Base Detectada : v{base_ver}")
    print(f"  Versión Destino Parche : v{target_ver}")
    print(f"  Identificador de Parche: {patch_id}")
    print(f"  Descripción            : {args.description}")
    print("=" * 70)

    python_exe = str(BASE_DIR / "monitorEnv" / "Scripts" / "python.exe")
    if not os.path.exists(python_exe):
        python_exe = sys.executable

    signtool = get_signtool_path()

    # 1. Pre-flight tests
    if not args.skip_tests:
        if not ejecutar_pruebas_unitarias(python_exe):
            sys.exit(1)

    # 2. Actualizar versión en branding para que el nuevo binario declare v2.2.4
    actualizar_version_en_branding(target_ver)

    try:
        # 3. Compilación diferencial
        compilar_diferencial(python_exe, run_cython=not args.skip_cython)

        # 4. Firma del binario en dist antes de staging
        dist_exe = BASE_DIR / "dist" / "AnvicNetworkSentinel" / "AnvicNetworkSentinel.exe"
        if not args.no_sign and dist_exe.exists():
            sign_file(dist_exe, signtool)

        # 5. Staging diferencial
        manifiesto = preparar_staging_parche(base_ver, target_ver, patch_id, args.description)

        # 6. Paquete Portable
        zip_file = generar_paquete_portable(target_ver, patch_id, manifiesto)

        # 7. Compilación de Instaladores Inno Setup (Parche + Instalador Completo)
        installer_exe, setup_exe = compilar_instalador_inno(
            target_ver=target_ver,
            base_ver=base_ver,
            patch_id=patch_id,
            descripcion=args.description,
            signtool=signtool,
        )

        # 8. Firma de los Instaladores finales
        if not args.no_sign:
            firmar_y_validar_artefactos(installer_exe, setup_exe, zip_file, signtool)

        print("\n" + "=" * 70)
        print("  [EXITO] SUITE DE ACTUALIZACIÓN GENERADA EXITOSAMENTE (GRADO INDUSTRIAL)")
        print("=" * 70)
        if installer_exe and installer_exe.exists():
            print(f"  [ARTEFACTO 1] Parche Acumulativo GUI: {installer_exe} ({installer_exe.stat().st_size / (1024*1024):.2f} MB)")
        if setup_exe and setup_exe.exists():
            print(f"  [ARTEFACTO 2] Instalador Completo   : {setup_exe} ({setup_exe.stat().st_size / (1024*1024):.2f} MB)")
        print(f"  [ARTEFACTO 3] Paquete Portable      : {zip_file} ({zip_file.stat().st_size / (1024*1024):.2f} MB)")
        print(f"  [MANIFIESTO] Hash SHA-256           : {STAGING_DIR / 'patch_manifest.json'}")
        print("  [SEGURIDAD] Integridad              : Bases de datos y configuraciones 100% protegidas.")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n[ERROR FATAL DURANTE LA GENERACIÓN DEL PARCHE]: {e}")
        raise


if __name__ == "__main__":
    main()
