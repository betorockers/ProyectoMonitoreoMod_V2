from datetime import datetime
import json
import os
import sys
from database_manager import DatabaseManager

class MetricasHistoricas:
    """Gestor de métricas usando SQLite para persistencia robusta (Argos Guard)"""
    
    def __init__(self, max_puntos=None, archivo_datos=None):
        # max_puntos y archivo_datos se mantienen por compatibilidad pero no se usan
        # Inicializar conexión a Base de Datos
        self.db = DatabaseManager()
        
        # Determinar ruta base persistente
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        self.archivo_mensual = os.path.join(base_path, "disponibilidad_mensual.json")
    
    def agregar_medicion(self, ip, latencia, estado):
        """Agregar una medición a la base de datos"""
        self.db.insert_metric(ip, latencia, estado)
    
    def obtener_datos(self, ip, periodo_horas=24):
        """Obtener datos de las últimas X horas desde SQLite"""
        return self.db.get_metrics(ip, periodo_horas)
    
    def calcular_uptime(self, ip, periodo_horas=24):
        """Calcular % de uptime basado en un periodo de horas"""
        datos = self.obtener_datos(ip, periodo_horas)
        if not datos or len(datos['estados']) == 0:
            return 100.0
        
        estados = datos['estados']
        total = len(estados)
        conectados = sum(estados)
        
        return (conectados / total * 100) if total > 0 else 100.0

    def registrar_disponibilidad_diaria(self):
        """Guarda el promedio de disponibilidad del día actual en el log mensual"""
        try:
            registro_diario = {}
            fecha_hoy = datetime.now().strftime("%Y-%m-%d")
            
            # Cargar historial mensual existente
            historial_mensual = {}
            if os.path.exists(self.archivo_mensual):
                with open(self.archivo_mensual, "r") as f:
                    historial_mensual = json.load(f)
            
            # Obtener lista de IPs activas en las últimas 24h
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT DISTINCT ip FROM metricas WHERE timestamp >= datetime('now', '-24 hours')")
            ips_activas = [row[0] for row in cursor.fetchall()]

            for ip in ips_activas:
                uptime_24h = self.calcular_uptime(ip, periodo_horas=24)
                if ip not in historial_mensual:
                    historial_mensual[ip] = []
                
                # Evitar duplicados para el mismo día
                historial_mensual[ip] = [r for r in historial_mensual[ip] if r['fecha'] != fecha_hoy]
                
                historial_mensual[ip].append({
                    'fecha': fecha_hoy,
                    'uptime': round(uptime_24h, 2)
                })
                
                # Mantener solo los últimos 30 días
                if len(historial_mensual[ip]) > 30:
                    historial_mensual[ip] = historial_mensual[ip][-30:]
            
            with open(self.archivo_mensual, "w") as f:
                json.dump(historial_mensual, f, indent=4)
                
            print(f"Registro de disponibilidad diaria guardado para {fecha_hoy}")
        except Exception as e:
            print(f"Error al registrar disponibilidad diaria: {e}")
