import os
import sqlite3
import pytest
import datetime
from database.database_manager import DatabaseManager
from secure_config_manager import SecureConfigManager
from auth_manager import AuthManager

def test_virgin_database_and_auth_initialization(tmp_path):
    """
    Simula una instalación limpia (virgen).
    Verifica que la base de datos se cree correctamente sin datos residuales,
    y que el AuthManager detecte que no hay usuarios, permitiendo el setup inicial.
    """
    base_path = str(tmp_path)
    
    # --- Parte 1: Base de Datos ---
    db_name = "test_virgin_anvic.db"
    db_path = os.path.join(base_path, db_name)
    
    old_cwd = os.getcwd()
    try:
        os.chdir(base_path)
        
        # We pass absolute path for db_name to force it into our tmp dir
        db_manager = DatabaseManager(db_name=db_path)
        
        # 2. Verificar que el archivo existe
        assert os.path.exists(db_path), "El archivo de base de datos no fue creado."
        
        # 3. Verificar que la tabla metricas existe y esta vacía
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='metricas'")
        table_exists = cursor.fetchone()[0]
        assert table_exists == 1, "La tabla 'metricas' no fue creada."
        
        cursor.execute("SELECT COUNT(*) FROM metricas")
        count = cursor.fetchone()[0]
        assert count == 0, f"La base de datos virgen no debería tener registros, pero tiene {count}."
        
        conn.close()
        db_manager.close()
    
    finally:
        os.chdir(old_cwd)

    # --- Parte 2: AuthManager / Usuarios ---
    key_path = os.path.join(base_path, "test.key")
    from cryptography.fernet import Fernet
    with open(key_path, "wb") as f:
        f.write(Fernet.generate_key())
        
    class MockKeyManager:
        @staticmethod
        def load_key():
            with open(key_path, "rb") as f:
                return f.read()

    import key_manager
    original_load_key = key_manager.load_key
    key_manager.load_key = MockKeyManager.load_key
    
    try:
        secure_manager = SecureConfigManager(key_manager.load_key())
        
        auth_manager = AuthManager(secure_manager, base_path)
        
        # 4. Verificar que no hay usuarios cargados
        assert auth_manager.users == {}, "En un entorno virgen, la lista de usuarios debe estar vacía."
        
        # 5. Intentar crear un superusuario inicial
        success, msg = auth_manager.create_initial_superuser("admin", "Anvic_2026!")
        assert success is True, f"Fallo al crear el superusuario inicial: {msg}"
        
        # 6. Verificar que el archivo .enc fue creado
        users_enc_path = os.path.join(base_path, "users.json.enc")
        assert os.path.exists(users_enc_path), "El archivo users.json.enc no fue guardado tras crear el usuario."
        
        # 7. Intentar crear OTRO superusuario (debería fallar porque ya no es virgen)
        success2, msg2 = auth_manager.create_initial_superuser("admin2", "Anvic_2026!")
        assert success2 is False, "El sistema permitió crear un segundo superusuario inicial, rompiendo la lógica de setup."
    
    finally:
        key_manager.load_key = original_load_key
