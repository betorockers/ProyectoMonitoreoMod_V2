import json
import hashlib
import os
import sys


class AuthManager:
    def __init__(self, users_file="users.json"):
        # Determinar ruta base persistente (donde está el exe o el script)
        if getattr(sys, "frozen", False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        self.users_file = os.path.join(base_path, users_file)
        self.audit_log = os.path.join(base_path, "auditoria_usuarios.log")
        self.users = self._load_users()

    def _log_event(self, message):
        """Escribe un evento en el archivo de auditoría."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.audit_log, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            print(f"Error escribiendo en log de auditoría: {e}")

    def validate_password(self, password):
        """Valida que la contraseña cumpla con los requisitos de seguridad."""
        if len(password) < 8:
            return False, "La contraseña debe tener al menos 8 caracteres."
        if not any(c.isupper() for c in password):
            return False, "Debe contener al menos una letra mayúscula."
        if not any(c.isdigit() for c in password):
            return False, "Debe contener al menos un número."
        special_chars = "!@#$%^&*()-_=+[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            return False, f"Debe contener al menos un carácter especial ({special_chars})."
        return True, ""

    def _load_users(self):
        users = {}
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, "r") as f:
                    users = json.load(f)
            except Exception as e:
                print(f"Error loading users: {e}")
                users = {}
        return users

    def _save_users(self, users):
        try:
            with open(self.users_file, "w") as f:
                json.dump(users, f, indent=4)
        except Exception as e:
            print(f"Error saving users: {e}")

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate(self, username, password):
        if username in self.users:
            if self.users[username]["password"] == self._hash_password(password):
                return {
                    "username": username,
                    "role": self.users[username]["role"],
                    "full_name": self.users[username]["full_name"],
                    "force_change_password": self.users[username].get(
                        "force_change_password", False
                    ),
                }
        return None

    def add_user(self, username, password, role, full_name, creator_role):
        if creator_role not in ["super_admin", "admin"]:
            return False, "No tiene permisos para agregar usuarios."

        # super_admin can create admin and user
        # admin can only create user
        if creator_role == "admin" and role != "user":
            return False, "Un administrador solo puede crear usuarios normales."

        if username in self.users:
            return False, "El usuario ya existe."

        # Para creación inicial por admin, solo validamos que no esté vacía
        if not password or len(password) < 1:
            return False, "La contraseña no puede estar vacía."

        self.users[username] = {
            "password": self._hash_password(password),
            "role": role,
            "full_name": full_name,
            "force_change_password": True,  # Obligar cambio de contraseña
        }
        self._save_users(self.users)
        
        # Registrar en el log de auditoría
        self._log_event(f"CREACIÓN: El administrador '{creator_role}' creó al usuario '{username}' (Rol: {role}). Clave inicial: {password}")
        
        return True, "Usuario creado exitosamente."

    def create_initial_superuser(self, username, password):
        """Crea el primer super administrador si no existen usuarios."""
        if self.users:
            return False, "Ya existen usuarios en el sistema."
            
        # Validar contraseña
        is_valid, msg = self.validate_password(password)
        if not is_valid:
            return False, msg

        self.users[username] = {
            "password": self._hash_password(password),
            "role": "super_admin",
            "full_name": "Administrador Principal",
            "force_change_password": False
        }
        self._save_users(self.users)
        return True, "Administrador configurado correctamente."

    def change_password(self, username, new_password):
        if username in self.users:
            # Validar nueva contraseña
            is_valid, msg = self.validate_password(new_password)
            if not is_valid:
                return False, msg

            self.users[username]["password"] = self._hash_password(new_password)
            self.users[username]["force_change_password"] = False
            self._save_users(self.users)
            
            # Registrar en el log de auditoría
            self._log_event(f"CAMBIO DE CLAVE: El usuario '{username}' realizó su cambio de contraseña obligatorio. Nueva clave: {new_password}")
            
            return True, "Contraseña actualizada correctamente."
        return False, "Usuario no encontrado."

    def delete_user(self, username, creator_role):
        if creator_role != "super_admin":
            return False, "No tiene permisos para eliminar usuarios."

        if username in self.users:
            del self.users[username]
            self._save_users(self.users)
            return True, "Usuario eliminado."
        return False, "Usuario no encontrado."

    def get_all_users(self, creator_role):
        if creator_role not in ["super_admin", "admin"]:
            return []

        users_list = []
        for u, d in self.users.items():
            # Ocultar super_admin si el que solicita no es super_admin
            if d["role"] == "super_admin" and creator_role != "super_admin":
                continue
            users_list.append(
                {
                    "username": u,
                    "role": d["role"],
                    "full_name": d["full_name"],
                }
            )

        return users_list
