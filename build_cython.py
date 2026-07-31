import os
import shutil
from distutils.core import setup
from Cython.Build import cythonize

def ejecutar():
    target_files = [
        "monitor.py",
        "ping_logic.py",
        "network_tools_logic.py",
        "auth/auth_manager.py",
        "database/key_manager.py",
        "licensing/license_service.py",
        "licensing/license_crypto.py"
    ]
    
    # Verify files exist
    valid_files = [f for f in target_files if os.path.exists(f)]
    print(f"Transpilando {len(valid_files)} archivos a Cython...")
    
    modules = cythonize(valid_files, compiler_directives={"language_level": "3"}, build_dir="build_tmp")
    setup(ext_modules=modules, script_args=["build_ext", "--inplace"])
    
    if os.path.exists("build_tmp"): 
        shutil.rmtree("build_tmp")
    
    print("Transpilación completa.")

if __name__ == "__main__":
    ejecutar()
