# database/metrics_manager.py
"""
Gestor de métricas históricas de Argos Guard.
Interfaz de alto nivel para cálculos estadísticos sobre los datos de SQLite.
"""

import json
import os
from datetime import datetime
from database.database_manager import DatabaseManager
from utils.paths import get_base_path
from config.settings import MONTHLY_AVAILABILITY_FILE


class MetricasHistoricas:
    """Interfaz de alto nivel para métricas de disponibilidad y latencia."""

    def __init__(self, max_puntos=None, archivo_datos=None):
        # max_puntos y archivo_datos se mantienen por compatibilidad retroactiva
        self.db = DatabaseManager()
        self.archivo_mensual = os.path.join(get_base_path(), MONTHLY_AVAILABILITY_FILE)

    def agregar_medicion(self, ip: str, latencia: float | None, estado: str) -> None:
        """Agrega una medición a la base de datos."""
        self.db.insert_metric(ip, latencia, estado)

    def obtener_datos(self, ip: str, periodo_horas: int = 24) -> dict:
        """Obtiene datos de las últimas X horas desde SQLite."""
        return self.db.get_metrics(ip, periodo_horas)

    def calcular_uptime(self, ip: str, periodo_horas: int = 24) -> float:
        """Calcula el porcentaje de uptime para una IP en un período dado."""
        datos = self.obtener_datos(ip, periodo_horas)
        estados = datos.get("estados", [])
        if not estados:
            return 100.0
        total = len(estados)
        conectados = sum(estados)
        return (conectados / total * 100) if total > 0 else 100.0

    def registrar_disponibilidad_diaria(self) -> None:
        """Guarda el promedio de disponibilidad del día actual en el log mensual."""
        try:
            fecha_hoy = datetime.now().strftime("%Y-%m-%d")

            # Cargar historial mensual existente
            historial_mensual = {}
            if os.path.exists(self.archivo_mensual):
                with open(self.archivo_mensual, "r", encoding="utf-8") as f:
                    historial_mensual = json.load(f)

            # Obtener IPs activas (FIX H-15: usa método encapsulado, NO acceso directo a conn)
            ips_activas = self.db.get_distinct_ips(hours=24)

            for ip in ips_activas:
                uptime_24h = self.calcular_uptime(ip, periodo_horas=24)
                if ip not in historial_mensual:
                    historial_mensual[ip] = []

                # Evitar duplicados para el mismo día
                historial_mensual[ip] = [
                    r for r in historial_mensual[ip] if r["fecha"] != fecha_hoy
                ]
                historial_mensual[ip].append(
                    {"fecha": fecha_hoy, "uptime": round(uptime_24h, 2)}
                )

                # Conservar solo los últimos 30 días
                if len(historial_mensual[ip]) > 30:
                    historial_mensual[ip] = historial_mensual[ip][-30:]

            with open(self.archivo_mensual, "w", encoding="utf-8") as f:
                json.dump(historial_mensual, f, indent=4)

            print(f"[Métricas] Disponibilidad diaria guardada para {fecha_hoy}")
        except Exception as e:
            print(f"[Métricas] Error al registrar disponibilidad diaria: {e}")
