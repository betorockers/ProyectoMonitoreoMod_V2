import os
import shutil
from setuptools import setup
from Cython.Build import cythonize

def ejecutar():
    target_files = [
        "network_tools_logic.py",
        "auth_manager.py",
        "key_manager.py",
        "secure_config_manager.py",
        "licensing/license_service.py",
        "licensing/license_crypto.py",
        "licensing/license_storage.py",
        "licensing/machine_fingerprint.py",
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
