# config/branding.py
"""
Fuente de la Verdad para la identidad visual de Anvic Network Sentinel.
Centraliza nombre, versión, copy principal y paleta de colores.

SEGURIDAD: Este archivo NO contiene tokens ni credenciales.
           Los secrets viven ÚNICAMENTE en el archivo .env de la raíz.
"""

# --- Identidad del Proyecto ---
APP_NAME = "Anvic Network Sentinel"
VERSION = "2.2.3"
AUTHOR = "BetoGraf_inc"
POWERED_BY = f"Powered By {AUTHOR}"
APP_TAGLINE = "El pulso de tu red bajo vigilancia."
WINDOW_TITLE = "Apps desarrollada para uso exclusivo de Anvic Seguridad Integral Powered By BetoGraf_inc"
REPORT_FILE_PREFIX = "Reporte_Anvic_Network_Sentinel"

# --- Paleta de Colores (Tema Sentinel) ---
COLOR_PRIMARY = "#00d9ff"      # Cyan brillante (Login, Botones principales)
COLOR_BG_DARK = "#1A1A1A"     # Fondo Oscuro
COLOR_SUCCESS = "#51cf66"      # Verde (Online)
COLOR_DANGER = "#ff6b6b"       # Rojo (Offline)
COLOR_WARNING = "#ffd43b"      # Amarillo (Latencia alta)
COLOR_TEXT_WHITE = "#FFFFFF"
COLOR_TEXT_GRAY = "#AAAAAA"
COLOR_CARD_BG = "#2B2B2B"      # Fondo de tarjetas

# --- Recursos ---
ICON_FILE = "IconoAnvic.ico"
LOGO_FILE = "logoAnvic.png"
