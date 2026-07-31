import sqlite3
import os
import sys
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name="argos_guard.db"):
        # Determinar ruta base persistente
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        self.db_path = os.path.join(base_path, db_name)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        """Crea las tablas necesarias si no existen"""
        cursor = self.conn.cursor()
        
        # Tabla de métricas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metricas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT NOT NULL,
                latencia REAL,
                estado INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Índices para mejorar velocidad de consultas
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ip_timestamp ON metricas(ip, timestamp)')
        
        self.conn.commit()

    def insert_metric(self, ip, latencia, estado):
        """Inserta una nueva medición"""
        try:
            # Convertir estado: "Conectado" -> 1, Otros -> 0
            estado_int = 1 if estado == "Conectado" else 0
            latencia_val = latencia if latencia is not None else 0.0
            
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO metricas (ip, latencia, estado, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (ip, latencia_val, estado_int, datetime.now()))
            self.conn.commit()
        except Exception as e:
            print(f"Error DB insert: {e}")

    def get_metrics(self, ip, hours=24):
        """Obtiene métricas de las últimas X horas"""
        try:
            cursor = self.conn.cursor()
            # SQLite modifier for datetime
            time_modifier = f'-{hours} hours'
            
            cursor.execute('''
                SELECT timestamp, latencia, estado 
                FROM metricas 
                WHERE ip = ? AND timestamp >= datetime('now', 'localtime', ?)
                ORDER BY timestamp ASC
            ''', (ip, time_modifier))
            
            rows = cursor.fetchall()
            
            timestamps = []
            latencias = []
            estados = []
            
            for row in rows:
                # row[0] es string "YYYY-MM-DD HH:MM:SS..."
                try:
                    ts = datetime.fromisoformat(row[0])
                except ValueError:
                    # Fallback para formatos sin microsegundos
                    ts = datetime.strptime(row[0].split('.')[0], "%Y-%m-%d %H:%M:%S")
                
                timestamps.append(ts)
                latencias.append(row[1])
                estados.append(row[2])
                
            return {
                'timestamps': timestamps,
                'latencias': latencias,
                'estados': estados
            }
        except Exception as e:
            print(f"Error DB get: {e}")
            return {'timestamps': [], 'latencias': [], 'estados': []}

    def close(self):
        self.conn.close()