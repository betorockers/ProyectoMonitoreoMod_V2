# metrics_manager.py

import sqlite3
import datetime
import os
from utils.paths import get_base_path

class MetricasHistoricas:
    """
    Gestiona la persistencia de métricas de red en una base de datos SQLite.
    Reemplaza el antiguo sistema basado en JSON.
    """

    def __init__(self):
        db_path = os.path.join(get_base_path(), "anvic_monitor.db")
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._crear_tablas()

    def _crear_tablas(self):
        """Crea las tablas necesarias si no existen."""
        cursor = self.conn.cursor()
        # Tabla para mediciones de ping en tiempo real
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mediciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                latencia REAL,
                estado INTEGER NOT NULL -- 1 para Conectado, 0 para Desconectado
            )
        """)
        # Tabla para el registro de disponibilidad diaria (uptime)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS disponibilidad_diaria (
                ip TEXT NOT NULL,
                fecha DATE NOT NULL,
                uptime_porcentaje REAL NOT NULL,
                PRIMARY KEY (ip, fecha)
            )
        """)
        self.conn.commit()

    def agregar_medicion(self, ip, latencia, nuevo_status):
        """Agrega una nueva medición de ping a la base de datos."""
        estado_int = 1 if nuevo_status == "Conectado" else 0
        timestamp = datetime.datetime.now()
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO mediciones (ip, timestamp, latencia, estado)
            VALUES (?, ?, ?, ?)
        """, (ip, timestamp, latencia, estado_int))
        self.conn.commit()

    def obtener_datos(self, ip, periodo_horas=24):
        """
        Obtiene los datos de un equipo para un período de tiempo.
        Usado para alimentar los gráficos de la UI.
        """
        cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=periodo_horas)
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT timestamp, latencia, estado FROM mediciones
            WHERE ip = ? AND timestamp >= ?
            ORDER BY timestamp ASC
        """, (ip, cutoff_time))
        
        rows = cursor.fetchall()
        
        return {
            "timestamps": [datetime.datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S.%f") if isinstance(row["timestamp"], str) and "." in row["timestamp"] else datetime.datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S") if isinstance(row["timestamp"], str) else row["timestamp"] for row in rows],
            "latencias": [row["latencia"] if row["latencia"] is not None else 0 for row in rows],
            "estados": [row["estado"] for row in rows]
        }

    def calcular_uptime(self, ip, periodo_dias=30):
        """Calcula el uptime de un equipo en los últimos X días."""
        cutoff_date = datetime.date.today() - datetime.timedelta(days=periodo_dias)
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT AVG(uptime_porcentaje) FROM disponibilidad_diaria
            WHERE ip = ? AND fecha >= ?
        """, (ip, cutoff_date))
        
        resultado = cursor.fetchone()
        return resultado[0] if resultado and resultado[0] is not None else 100.0

    def registrar_disponibilidad_diaria(self):
        """
        Calcula y guarda el uptime de las últimas 24 horas para cada equipo.
        Se ejecuta periódicamente.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT ip FROM mediciones")
        ips = [row["ip"] for row in cursor.fetchall()]

        cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=24)
        today = datetime.date.today()

        for ip in ips:
            cursor.execute("""
                SELECT CAST(SUM(estado) AS REAL) / COUNT(estado) * 100
                FROM mediciones
                WHERE ip = ? AND timestamp >= ?
            """, (ip, cutoff_time))
            
            resultado = cursor.fetchone()
            if resultado and resultado[0] is not None:
                uptime_24h = resultado[0]
                cursor.execute("""
                    INSERT OR REPLACE INTO disponibilidad_diaria (ip, fecha, uptime_porcentaje)
                    VALUES (?, ?, ?)
                """, (ip, today, uptime_24h))
        
        self.conn.commit()
        print(f"Registro de disponibilidad diaria completado para {len(ips)} equipos.")

    def guardar_en_disco(self):
        """
        En el modelo SQLite, los datos se guardan continuamente.
        Esta función puede forzar un commit final o realizar tareas de limpieza.
        """
        self.conn.commit()
        self._limpiar_datos_antiguos()

    def _limpiar_datos_antiguos(self, dias_retencion=35):
        """Elimina registros de mediciones más antiguos que X días para mantener la DB ligera."""
        cutoff_time = datetime.datetime.now() - datetime.timedelta(days=dias_retencion)
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM mediciones WHERE timestamp < ?", (cutoff_time,))
        self.conn.commit()
        print(f"Datos de mediciones con más de {dias_retencion} días han sido purgados.")

    def __del__(self):
        """Asegura que la conexión a la base deatos se cierre al destruir el objeto."""
        self.conn.close()