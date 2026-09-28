# metrics_manager.py

import sqlite3
import datetime
import os
from utils.paths import get_base_path

# Registrar adaptadores compatibles con Python 3.12 y 3.13 para evitar DeprecationWarning
sqlite3.register_adapter(datetime.datetime, lambda val: val.isoformat(sep=" "))
sqlite3.register_adapter(datetime.date, lambda val: val.isoformat())


def _parse_timestamp(val):
    """
    Parsea de forma robusta cualquier formato de timestamp:
    - Instancias nativas de datetime
    - ISO-8601 con 'T' (ej: '2026-09-25T16:19:24.860481')
    - ISO-8601 con espacio (ej: '2026-09-25 16:19:24.860481')
    - Sin microsegundos (ej: '2026-09-25 16:19:24')
    """
    if isinstance(val, datetime.datetime):
        return val
    if not isinstance(val, str):
        return val
    try:
        return datetime.datetime.fromisoformat(val)
    except ValueError:
        clean = val.replace("T", " ")
        try:
            if "." in clean:
                return datetime.datetime.strptime(clean, "%Y-%m-%d %H:%M:%S.%f")
            return datetime.datetime.strptime(clean, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return val


class MetricasHistoricas:
    """
    Gestiona la persistencia de métricas de red en una base de datos SQLite.
    Reemplaza el antiguo sistema basado en JSON.
    """

    def __init__(self):
        db_path = os.path.join(get_base_path(), "anvic_monitor.db")
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # --- FASE 3: OPTIMIZACIÓN DE BASE DE DATOS (WAL & BULK) ---
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA temp_store=MEMORY;")
        self.conn.commit()
        
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
            "timestamps": [_parse_timestamp(row["timestamp"]) for row in rows],
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
        self._limpiar_datos_antiguos(dias_retencion=90)
        print(f"Registro de disponibilidad diaria completado para {len(ips)} equipos.")

    def guardar_en_disco(self):
        """
        En el modelo SQLite, los datos se guardan continuamente.
        Esta función fuerza un commit y realiza mantenimiento de retención.
        """
        self.conn.commit()
        self._limpiar_datos_antiguos(dias_retencion=90)

    def _limpiar_datos_antiguos(self, dias_retencion=90):
        """Elimina registros de mediciones más antiguos que X días para mantener la DB ligera y optimizada."""
        try:
            cutoff_time = datetime.datetime.now() - datetime.timedelta(days=dias_retencion)
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM mediciones WHERE timestamp < ?", (cutoff_time,))
            self.conn.commit()
            cursor.execute("PRAGMA optimize;")
            self.conn.commit()
            print(f"Mantenimiento SQLite: purga > {dias_retencion} días y PRAGMA optimize completados.")
        except Exception as e:
            print(f"Error en mantenimiento SQLite: {e}")

    def analizar_desconexiones_y_downtime(self, ip, periodo_horas=24):
        """
        Analiza detalladamente los eventos de desconexión, microcortes y tiempo offline acumulado.
        """
        cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=periodo_horas)
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT timestamp, latencia, estado FROM mediciones
            WHERE ip = ? AND timestamp >= ?
            ORDER BY timestamp ASC
        """, (ip, cutoff_time))
        rows = cursor.fetchall()

        if not rows:
            return {
                "total_desconexiones": 0,
                "downtime_segundos": 0.0,
                "downtime_str": "0s",
                "microcortes_count": 0,
                "cortes_medios_count": 0,
                "caidas_criticas_count": 0,
                "peor_incidencia": None,
                "uptime_periodo": 100.0,
                "latencia_promedio": 0.0,
                "latencia_p95": 0.0,
            }

        parse_ts = _parse_timestamp

        desconexiones = []
        en_caida = False
        inicio_caida = None
        latencias_validas = []

        for i, row in enumerate(rows):
            estado = row["estado"]
            ts = parse_ts(row["timestamp"])
            lat = row["latencia"]
            if lat is not None and lat > 0:
                latencias_validas.append(lat)

            if estado == 0 and not en_caida:
                en_caida = True
                inicio_caida = ts
            elif estado == 1 and en_caida:
                en_caida = False
                duracion = max(1.0, (ts - inicio_caida).total_seconds())
                desconexiones.append({
                    "inicio": inicio_caida,
                    "fin": ts,
                    "duracion_seg": duracion
                })
                inicio_caida = None

        if en_caida and inicio_caida:
            duracion = max(1.0, (datetime.datetime.now() - inicio_caida).total_seconds())
            desconexiones.append({
                "inicio": inicio_caida,
                "fin": datetime.datetime.now(),
                "duracion_seg": duracion
            })

        total_downtime = sum(d["duracion_seg"] for d in desconexiones)
        microcortes = [d for d in desconexiones if d["duracion_seg"] < 30]
        cortes_medios = [d for d in desconexiones if 30 <= d["duracion_seg"] <= 300]
        caidas_criticas = [d for d in desconexiones if d["duracion_seg"] > 300]

        peor = max(desconexiones, key=lambda d: d["duracion_seg"]) if desconexiones else None
        peor_dict = None
        if peor:
            peor_dict = {
                "inicio": peor["inicio"].strftime("%H:%M:%S"),
                "duracion_seg": peor["duracion_seg"],
                "duracion_str": self._formatear_duracion(peor["duracion_seg"])
            }

        total_samples = len(rows)
        up_samples = sum(1 for r in rows if r["estado"] == 1)
        uptime = (up_samples / total_samples * 100.0) if total_samples > 0 else 100.0

        latencias_sorted = sorted(latencias_validas)
        lat_avg = sum(latencias_validas) / len(latencias_validas) if latencias_validas else 0.0
        lat_p95 = latencias_sorted[int(len(latencias_sorted) * 0.95)] if latencias_sorted else lat_avg

        return {
            "total_desconexiones": len(desconexiones),
            "downtime_segundos": total_downtime,
            "downtime_str": self._formatear_duracion(total_downtime),
            "microcortes_count": len(microcortes),
            "cortes_medios_count": len(cortes_medios),
            "caidas_criticas_count": len(caidas_criticas),
            "peor_incidencia": peor_dict,
            "uptime_periodo": uptime,
            "latencia_promedio": lat_avg,
            "latencia_p95": lat_p95,
        }

    def obtener_matriz_semanal(self, ip=None, dias=7):
        """
        Calcula una matriz de 7 días (Lunes a Domingo) por 24 horas (00 a 23h).
        Retorna matriz de disponibilidad (0.0 a 1.0) y matriz de conteos.
        """
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=dias)
        cursor = self.conn.cursor()

        if ip:
            cursor.execute("""
                SELECT timestamp, estado FROM mediciones
                WHERE ip = ? AND timestamp >= ?
                ORDER BY timestamp ASC
            """, (ip, cutoff_date))
        else:
            cursor.execute("""
                SELECT timestamp, estado FROM mediciones
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
            """, (cutoff_date,))

        rows = cursor.fetchall()
        matriz_up = [[0 for _ in range(24)] for _ in range(7)]
        matriz_total = [[0 for _ in range(24)] for _ in range(7)]

        for r in rows:
            ts = _parse_timestamp(r["timestamp"])

            dia = ts.weekday()  # 0: Lunes, ..., 6: Domingo
            hora = ts.hour      # 0 .. 23
            matriz_total[dia][hora] += 1
            if r["estado"] == 1:
                matriz_up[dia][hora] += 1

        matriz_disponibilidad = [[0.0 for _ in range(24)] for _ in range(7)]
        for d in range(7):
            for h in range(24):
                tot = matriz_total[d][h]
                if tot > 0:
                    matriz_disponibilidad[d][h] = matriz_up[d][h] / tot
                else:
                    matriz_disponibilidad[d][h] = 1.0  # Si no hay muestras, normalizado

        return {
            "disponibilidad": matriz_disponibilidad,
            "totales": matriz_total,
            "dias_etiquetas": ["L", "M", "X", "J", "V", "S", "D"],
            "horas_etiquetas": [f"{h:02d}h" for h in range(24)]
        }

    def evaluar_estabilidad_global(self, equipos, periodo_horas=24):
        """
        Motor heurístico de telemetría: Evalúa la salud global de la red en las últimas X horas
        y emite diagnóstico, causa probable y recomendaciones de ingeniería.
        """
        downtime_total_acumulado = 0.0
        microcortes_totales = 0
        cortes_mayores_totales = 0
        uptimes = []
        latencias_avg = []

        equipos_con_fallas = []
        for eq in equipos:
            ip = eq["ip"]
            analisis = self.analizar_desconexiones_y_downtime(ip, periodo_horas=periodo_horas)
            analisis["equipo"] = eq

            downtime_total_acumulado += analisis["downtime_segundos"]
            microcortes_totales += analisis["microcortes_count"]
            cortes_mayores_totales += (analisis["cortes_medios_count"] + analisis["caidas_criticas_count"])
            uptimes.append(analisis["uptime_periodo"])
            if analisis["latencia_promedio"] > 0:
                latencias_avg.append(analisis["latencia_promedio"])

            if analisis["total_desconexiones"] > 0 or analisis["uptime_periodo"] < 99.0:
                equipos_con_fallas.append((eq.get("label", ip), analisis))

        uptime_promedio = sum(uptimes) / len(uptimes) if uptimes else 100.0
        lat_global = sum(latencias_avg) / len(latencias_avg) if latencias_avg else 0.0

        if uptime_promedio >= 99.5 and microcortes_totales == 0 and cortes_mayores_totales == 0:
            estado = "ESTABLE"
            badge = "OPERACIÓN ALTAMENTE ESTABLE - CERTIFICACIÓN DE DISPONIBILIDAD"
            color_hex = "#15803D"
            diagnostico = (
                f"La infraestructura monitoreada mantuvo una estabilidad sobresaliente durante el período "
                f"de {periodo_horas}h, con un SLA de disponibilidad promedio de {uptime_promedio:.2f}% y cero "
                f"eventos de microcorte o caída de enlaces. La latencia media global se situó en {lat_global:.1f} ms."
            )
            causa_raiz = "Operación nominal de enlaces y equipamiento de distribución bajo parámetros óptimos."
            recomendaciones = [
                "Mantener el programa preventivo de inspección de cableado y switches de distribución.",
                "Mantener respaldos periódicos de configuración en gateways y dispositivos críticos.",
                "Continuar con la política de monitoreo continuo en tiempo real con Argos Guard."
            ]
        elif uptime_promedio >= 96.0 or (microcortes_totales > 0 and cortes_mayores_totales == 0):
            estado = "DEGRADADA_INTERMITENTE"
            badge = "OPERACIÓN CON DEGRADACIÓN INTERMITENTE (MICROCORTES DETECTADOS)"
            color_hex = "#B45309"
            nombres_afectados = ", ".join([f"{nombre} ({a['microcortes_count']} microcortes, downtime {a['downtime_str']})" for nombre, a in equipos_con_fallas[:3]])
            diagnostico = (
                f"Se detectó inestabilidad intermitente con un total de {microcortes_totales} microcorte(s) "
                f"y un downtime acumulado de {self._formatear_duracion(downtime_total_acumulado)}. "
                f"Uptime promedio: {uptime_promedio:.1f}%. Dispositivos con mayor incidencia: {nombres_afectados}."
            )
            causa_raiz = (
                "Comportamiento típico de fluctuaciones en switches de borde, renegociación PoE en cámaras/sensores, "
                "o interferencia/ruido en tramos de cableado UTP expuestos."
            )
            recomendaciones = [
                "Verificar la estabilidad eléctrica e inyectores PoE que alimentan a los dispositivos afectados.",
                "Comprobar estado físico de conectores RJ45 y certificación de enlace en los puntos con intermitencias.",
                "Revisar logs de eventos en switch intermediario para descartar bucles STP o renegociación dúplex."
            ]
        else:
            estado = "CRITICA"
            badge = "CONDICIÓN CRÍTICA DE OPERACIÓN (CAÍDAS SIGNIFICATIVAS DE ENLACE)"
            color_hex = "#B91C1C"
            nombres_afectados = ", ".join([f"{nombre} (Downtime: {a['downtime_str']})" for nombre, a in equipos_con_fallas[:3]])
            diagnostico = (
                f"La red operó bajo condiciones críticas con {cortes_mayores_totales} caída(s) prolongada(s) y "
                f"un tiempo acumulado fuera de línea de {self._formatear_duracion(downtime_total_acumulado)}. "
                f"Uptime global degradado al {uptime_promedio:.1f}%. Equipos críticos afectados: {nombres_afectados}."
            )
            causa_raiz = (
                "Pérdida de suministro eléctrico prolongada, falla en switch de capa de acceso o corte físico en enlace troncal."
            )
            recomendaciones = [
                "Intervención técnica inmediata en los nodos fuera de servicio o con caídas recurrentes.",
                "Auditar el sistema de respaldo ininterrumpido de energía (UPS) en racks de comunicaciones.",
                "Realizar trazado de cableado de fibra/cobre y pruebas de atenuación en troncal."
            ]

        return {
            "estado": estado,
            "badge": badge,
            "color_hex": color_hex,
            "uptime_promedio": uptime_promedio,
            "latencia_promedio": lat_global,
            "downtime_total_segundos": downtime_total_acumulado,
            "downtime_total_str": self._formatear_duracion(downtime_total_acumulado),
            "microcortes_totales": microcortes_totales,
            "cortes_mayores_totales": cortes_mayores_totales,
            "equipos_con_fallas": equipos_con_fallas,
            "diagnostico": diagnostico,
            "causa_raiz": causa_raiz,
            "recomendaciones": recomendaciones,
        }

    @staticmethod
    def _formatear_duracion(segundos):
        """Convierte segundos a una representación legible (ej: 08m 42s, 1h 20m 10s)."""
        seg = int(round(segundos))
        if seg <= 0:
            return "0s"
        if seg < 60:
            return f"{seg}s"
        minutos = seg // 60
        seg_resto = seg % 60
        if minutos < 60:
            return f"{minutos:02d}m {seg_resto:02d}s"
        horas = minutos // 60
        min_resto = minutos % 60
        return f"{horas}h {min_resto:02d}m {seg_resto:02d}s"

    def __del__(self):
        """Asegura que la conexión a la base de datos se cierre al destruir el objeto."""
        try:
            self.conn.close()
        except Exception:
            pass