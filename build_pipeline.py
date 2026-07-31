import os
import subprocess
import time

TARGET_FILES = [
    "monitor.py",
    "ping_logic.py",
    "network_tools_logic.py",
    "auth/auth_manager.py",
    "database/key_manager.py",
    "licensing/license_service.py",
    "licensing/license_crypto.py"
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

def main():
    print("=== 1. Ejecutando Transpilación Cython ===")
    subprocess.run(["python", "build_cython.py"], check=True)
    
    print("=== 2. Ocultando archivos .py (Backups) ===")
    rename_to_bak()
    
    try:
        print("=== 3. Empaquetando con PyInstaller ===")
        subprocess.run(["pyinstaller", "--clean", "-y", "AnvicNetworkSentinel.spec"], check=True)
    finally:
        print("=== 4. Restaurando archivos .py ===")
        restore_from_bak()
    
    print("=== 5. Compilando instalador Inno Setup ===")
    iscc_path = get_iscc_path()
    if iscc_path:
        subprocess.run([iscc_path, r"e:\AnvicNetworkMonitorV2.1\installer.iss"], check=True)
        print("=== COMPILACIÓN INDUSTRIAL EXITOSA ===")
    else:
        print("ERROR: No se encontró ISCC.exe")

if __name__ == "__main__":
    main()
