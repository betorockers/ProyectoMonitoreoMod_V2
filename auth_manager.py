# auth_manager.py

import os
import bcrypt
import datetime
from cryptography.fernet import InvalidToken
import re

class AuthManager:
    """
    Gestiona la autenticación, autorización y administración de usuarios.
    Utiliza SecureConfigManager para persistencia cifrada.
    """
    def __init__(self, secure_config_manager, base_path):
        self.users_file_path = os.path.join(base_path, "users.json")
        self.secure_config = secure_config_manager
        self.users = self._load_users() or {} # Aseguramos que sea un dict si no existe

    def _load_users(self):
        """Carga los usuarios desde el archivo seguro .json.enc."""
        try:
            loaded_users = self.secure_config.load(self.users_file_path)
            if not loaded_users:
                return None
            
            # Convertir el hash de la contraseña de nuevo a bytes para bcrypt
            for username, data in loaded_users.items():
                if 'password_hash' in data and isinstance(data['password_hash'], str):
                    data['password_hash'] = data['password_hash'].encode('latin-1')
            return loaded_users
        except FileNotFoundError:
            # Comportamiento esperado en la primera ejecución, no es un error.
            return None
        except InvalidToken:
            print("[!] ADVERTENCIA: La clave de cifrado ha cambiado o el archivo de usuarios está corrupto.")
            print("[!] Se iniciará una nueva configuración. Los datos de usuario anteriores se han perdido.")
            try:
                encrypted_path = self.secure_config._get_encrypted_path(self.users_file_path)
                ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                backup_path = f"{encrypted_path}.corrupt.{ts}"
                os.rename(encrypted_path, backup_path)
                print(f"[i] Se ha guardado una copia del archivo de usuarios inválido en: {backup_path}")
            except Exception as e:
                print(f"[!] No se pudo renombrar el archivo de usuarios corrupto: {e}")
            return None # Devolvemos None para forzar el reseteo.

    def _save_users(self):
        """Guarda el diccionario de usuarios en el archivo seguro .json.enc."""
        # Crear una copia serializable para no modificar el estado en memoria
        serializable_users = {}
        for username, data in self.users.items():
            serializable_data = data.copy()
            # Decodificar bytes a string para la serialización JSON
            if 'password_hash' in serializable_data and isinstance(serializable_data['password_hash'], bytes):
                serializable_data['password_hash'] = serializable_data['password_hash'].decode('latin-1')
            serializable_users[username] = serializable_data
        
        self.secure_config.save(serializable_users, self.users_file_path)

    def _hash_password(self, password):
        """Genera un hash seguro de la contraseña usando bcrypt."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    def _check_password(self, password, hashed):
        """Verifica si la contraseña coincide con el hash almacenado."""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed)
        except (ValueError, TypeError):
            return False

    def _validate_password(self, password):
        """Valida la complejidad de la contraseña según las políticas de seguridad."""
        if len(password) < 8:
            return False, "La contraseña debe tener al menos 8 caracteres."
        if not re.search(r"[A-Z]", password):
            return False, "La contraseña debe contener al menos una mayúscula."
        if not re.search(r"[a-z]", password):
            return False, "La contraseña debe contener al menos una minúscula."
        if not re.search(r"\d", password):
            return False, "La contraseña debe contener al menos un número."
        if not re.search(r"[!@#$%^&*(),.?:{}|<>]", password):
            return False, "La contraseña debe contener al menos un carácter especial."
        return True, ""

    def authenticate(self, username, password):
        """Autentica a un usuario y retorna sus datos si es exitoso."""
        user_data = self.users.get(username)
        if user_data and self._check_password(password, user_data['password_hash']):
            # Retornar una copia que incluya el nombre de usuario para la UI
            return {'username': username, **user_data}
        return None

    def create_initial_superuser(self, username, password):
        """Crea el primer usuario con rol super_admin para la configuración inicial."""
        if self.users:
            return False, "Ya existen usuarios. No se puede crear un super admin inicial."
        
        is_valid, msg = self._validate_password(password)
        if not is_valid:
            return False, msg

        self.users[username] = {
            'password_hash': self._hash_password(password),
            'password_plain': password,
            'role': 'super_admin',
            'full_name': 'Administrador Maestro',
            'force_change_password': False
        }
        self._save_users()
        return True, "Super administrador creado exitosamente."

    def add_user(self, username, password, role, fullname, current_user_role):
        """Agrega un nuevo usuario, verificando permisos del usuario actual."""
        if current_user_role not in ['admin', 'super_admin']:
            return False, "Permiso denegado."
        if role == 'super_admin':
            return False, "No se puede crear otro super_admin."
        if current_user_role == 'admin' and role == 'admin':
            return False, "Un admin no puede crear otro admin."
        if username in self.users:
            return False, "El nombre de usuario ya existe."

        # Para usuarios nuevos, se permite una clave simple que deberá ser cambiada.
        # No se valida complejidad aquí, se fuerza el cambio en el primer login.
        self.users[username] = {
            'password_hash': self._hash_password(password),
            'password_plain': password,
            'role': role,
            'full_name': fullname,
            'force_change_password': True 
        }
        self._save_users()
        return True, f"Usuario '{username}' creado. Deberá cambiar su clave al ingresar."

    def delete_user(self, username, current_user_role):
        """Elimina un usuario, verificando permisos."""
        if current_user_role != 'super_admin':
            return False, "Solo el super_admin puede eliminar usuarios."
        if username not in self.users:
            return False, "El usuario no existe."
        if self.users[username]['role'] == 'super_admin':
            return False, "No se puede eliminar al super_admin."
        
        del self.users[username]
        self._save_users()
        return True, f"Usuario '{username}' eliminado."

    def change_password(self, username, new_password):
        """Cambia la contraseña de un usuario y valida su complejidad."""
        if username not in self.users:
            return False, "Usuario no encontrado."
        
        is_valid, msg = self._validate_password(new_password)
        if not is_valid:
            return False, msg
            
        self.users[username]['password_hash'] = self._hash_password(new_password)
        self.users[username]['password_plain'] = new_password
        self.users[username]['force_change_password'] = False # Marcar como cambiada
        self._save_users()
        return True, "Contraseña actualizada exitosamente."

    def update_user(self, current_user_role, old_username, new_username, new_password, new_fullname, new_role):
        """Actualiza la información de un usuario existente (Super Admin)."""
        if current_user_role != 'super_admin':
            return False, "Permiso denegado."
            
        if old_username not in self.users:
            return False, "Usuario original no existe."
            
        if new_username != old_username and new_username in self.users:
            return False, "El nuevo nombre de usuario ya existe."
            
        user_data = self.users[old_username]
        
        # Actualizar datos
        user_data['full_name'] = new_fullname
        user_data['role'] = new_role
        
        if new_password and new_password.strip():
            user_data['password_hash'] = self._hash_password(new_password)
            user_data['password_plain'] = new_password
            
        # Mover si cambia el username
        if new_username != old_username:
            self.users[new_username] = user_data
            del self.users[old_username]
            
        self._save_users()
        return True, "Usuario actualizado exitosamente."

    def get_all_users(self, current_user_role):
        """Retorna una lista de todos los usuarios, filtrada por rol para evitar que un admin vea al super_admin."""
        if current_user_role not in ['admin', 'super_admin']:
            return []
        
        user_list = []
        for username, data in self.users.items():
            if current_user_role == 'admin' and data['role'] == 'super_admin':
                continue
            user_list.append({'username': username, **data})
        return user_list