"""
Wrapper de compatibilidad para la rama modular.

Reutiliza el AuthManager seguro del nucleo activo para evitar mantener
una segunda implementacion menos segura con JSON plano y SHA-256 simple.
"""

from auth_manager import AuthManager

__all__ = ["AuthManager"]
