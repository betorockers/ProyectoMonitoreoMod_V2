# database/database_manager.py
"""
Capa de abstracción SQLite para Argos Guard.
Gestiona la conexión, creación de tablas e inserción/consulta de métricas.
"""

import sqlite3
import os
from datetime import datetime
from utils.paths import get_base_path
from config.settings import DB_FILENAME


class DatabaseManager:
    """Gestiona la conexión y operaciones con la base de datos SQLite."""

    def __init__(self, db_name: str = DB_FILENAME):
        self.db_path = os.path.join(get_base_path(), db_name)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA temp_store=MEMORY;")
        self.conn.commit()
        self._create_tables()

    def _create_tables(self) -> None:
        """Crea las tablas necesarias si no existen."""
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metricas (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                ip        TEXT    NOT NULL,
                latencia  REAL,
                estado    INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Índice compuesto para mejorar velocidad de consultas por ip+timestamp
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_ip_timestamp ON metricas(ip, timestamp)"
        )

        self.conn.commit()

    def insert_metric(self, ip: str, latencia: float | None, estado: str) -> None:
        """
        Inserta una nueva medición en la base de datos.

        Args:
            ip: Dirección IP del equipo monitoreado.
            latencia: Latencia en ms, o None si no disponible.
            estado: String "Conectado" o "Desconectado".
        """
        try:
            estado_int = 1 if estado == "Conectado" else 0
            latencia_val = latencia if latencia is not None else 0.0

            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO metricas (ip, latencia, estado, timestamp) VALUES (?, ?, ?, ?)",
                (ip, latencia_val, estado_int, datetime.now()),
            )
            self.conn.commit()
        except Exception as e:
            print(f"[DB] Error al insertar métrica: {e}")

    def get_metrics(self, ip: str, hours: int = 24) -> dict:
        """
        Obtiene las métricas de un equipo en las últimas X horas.

        Returns:
            dict con listas 'timestamps', 'latencias' y 'estados'.
        """
        try:
            cursor = self.conn.cursor()
            time_modifier = f"-{hours} hours"
            cursor.execute(
                """
                SELECT timestamp, latencia, estado
                FROM metricas
                WHERE ip = ? AND timestamp >= datetime('now', 'localtime', ?)
                ORDER BY timestamp ASC
                """,
                (ip, time_modifier),
            )
            rows = cursor.fetchall()

            timestamps, latencias, estados = [], [], []
            for row in rows:
                try:
                    ts = datetime.fromisoformat(row[0])
                except ValueError:
                    clean_ts = row[0].replace("T", " ").split(".")[0]
                    ts = datetime.strptime(clean_ts, "%Y-%m-%d %H:%M:%S")

                timestamps.append(ts)
                latencias.append(row[1])
                estados.append(row[2])

            return {"timestamps": timestamps, "latencias": latencias, "estados": estados}

        except Exception as e:
            print(f"[DB] Error al obtener métricas: {e}")
            return {"timestamps": [], "latencias": [], "estados": []}

    def get_distinct_ips(self, hours: int = 24) -> list[str]:
        """
        Retorna las IPs con actividad en las últimas X horas.
        Encapsula el acceso directo a la conexión (FIX H-15).
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT DISTINCT ip FROM metricas WHERE timestamp >= datetime('now', ?)",
                (f"-{hours} hours",),
            )
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"[DB] Error al obtener IPs activas: {e}")
            return []

    def close(self) -> None:
        """Cierra la conexión a la base de datos."""
        self.conn.close()
