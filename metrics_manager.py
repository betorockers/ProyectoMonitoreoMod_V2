# metrics_manager.py

import sqlite3
import datetime
import os
import numpy as np
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


def _parse_hora_str(hora_str: str) -> tuple[int, int]:
    """Convierte '07:00' o '7' a (7, 0)."""
    try:
        parts = str(hora_str).strip().split(":")
        h = int(parts[0])
        m = int(parts[1]) if len(parts) > 1 else 0
        return max(0, min(23, h)), max(0, min(59, m))
    except Exception:
        return 7, 0


def dentro_de_turno(ts, inicio_str: str = "07:00", fin_str: str = "18:00") -> bool:
    """
    Determina si un timestamp o time cae dentro de la franja horaria del turno.
    Soporta turnos diurnos estándar (ej: 07:00 a 18:00) y nocturnos/overnight (ej: 22:00 a 06:00).
    """
    if isinstance(ts, datetime.datetime):
        t = ts.time()
    elif isinstance(ts, datetime.time):
        t = ts
    else:
        return True

    h_ini, m_ini = _parse_hora_str(inicio_str)
    h_fin, m_fin = _parse_hora_str(fin_str)

    t_ini = datetime.time(h_ini, m_ini)
    t_fin = datetime.time(h_fin, m_fin)

    if t_ini <= t_fin:
        return t_ini <= t <= t_fin
    else:
        return t >= t_ini or t <= t_fin


def obtener_horas_turno(inicio_str: str = "07:00", fin_str: str = "18:00") -> list[int]:
    """Retorna la lista ordenada de horas enteras (0..23) correspondientes a la franja del turno."""
    h_ini, _ = _parse_hora_str(inicio_str)
    h_fin, _ = _parse_hora_str(fin_str)

    if h_ini <= h_fin:
        return list(range(h_ini, h_fin + 1))
    else:
        return list(range(h_ini, 24)) + list(range(0, h_fin + 1))


def obtener_rango_turno_reciente(
    inicio_str: str = "07:00",
    fin_str: str = "18:00",
    now: datetime.datetime | None = None,
) -> tuple[datetime.datetime, datetime.datetime]:
    """
    Calcula el rango temporal (datetime_inicio, datetime_fin) continuo del turno operacional más reciente o activo.
    Soporta turnos diurnos estándar (ej. 07:00 a 18:00) y nocturnos/overnight (ej. 22:00 a 06:00).
    """
    now = now or datetime.datetime.now()
    h_ini, m_ini = _parse_hora_str(inicio_str)
    h_fin, m_fin = _parse_hora_str(fin_str)

    today = now.date()
    yesterday = today - datetime.timedelta(days=1)
    tomorrow = today + datetime.timedelta(days=1)

    if h_ini <= h_fin:
        t_ini_today = datetime.datetime.combine(today, datetime.time(h_ini, m_ini))
        t_fin_today = datetime.datetime.combine(today, datetime.time(h_fin, m_fin))
        if now < t_ini_today:
            start = datetime.datetime.combine(yesterday, datetime.time(h_ini, m_ini))
            end = datetime.datetime.combine(yesterday, datetime.time(h_fin, m_fin))
        else:
            start = t_ini_today
            end = t_fin_today
    else:
        t_fin_today = datetime.datetime.combine(today, datetime.time(h_fin, m_fin))
        t_ini_today = datetime.datetime.combine(today, datetime.time(h_ini, m_ini))
        if now <= t_fin_today:
            start = datetime.datetime.combine(yesterday, datetime.time(h_ini, m_ini))
            end = t_fin_today
        elif now >= t_ini_today:
            start = t_ini_today
            end = datetime.datetime.combine(tomorrow, datetime.time(h_fin, m_fin))
        else:
            start = datetime.datetime.combine(yesterday, datetime.time(h_ini, m_ini))
            end = t_fin_today

    return start, end


class MetricasHistoricas:
    """
    Gestiona la persistencia de métricas de red en una base de datos SQLite.
    Reemplaza el antiguo sistema basado en JSON.
    """

    def __init__(self, db_path: str | None = None):
        if db_path is None:
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
        """Crea las tablas necesarias si no existen y asegura los índices de alto rendimiento."""
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
        # Índices compuestos para acelerar búsquedas por ip y timestamp (100x speedup)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mediciones_ip_ts ON mediciones (ip, timestamp);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mediciones_ts ON mediciones (timestamp);")

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

    def analizar_desconexiones_y_downtime(
        self,
        ip,
        periodo_horas=24,
        rango_inicio: datetime.datetime | None = None,
        rango_fin: datetime.datetime | None = None,
    ):
        """
        Analiza detalladamente los eventos de desconexión, microcortes y tiempo offline acumulado.
        Permite acotar el análisis a una ventana específica (Turno, 24h, Semanal) calculando con
        exactitud tanto el impacto en el período evaluado como la duración total de la falla.
        """
        now_dt = datetime.datetime.now()
        if rango_inicio is not None:
            cutoff_time = rango_inicio
            end_time = rango_fin or now_dt
        else:
            cutoff_time = now_dt - datetime.timedelta(hours=periodo_horas)
            end_time = now_dt

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT timestamp, latencia, estado FROM mediciones
            WHERE ip = ? AND timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp ASC
        """, (ip, cutoff_time, end_time))
        rows = cursor.fetchall()

        if not rows:
            return {
                "total_desconexiones": 0,
                "downtime_segundos": 0.0,
                "downtime_str": "0s",
                "downtime_total_falla_segundos": 0.0,
                "downtime_total_falla_str": "0s",
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
                if i == 0:
                    # Rastrear hacia atrás en la base de datos el inicio real de la desconexión
                    # para que no se reinicie artificialmente en la hora de corte o apertura de turno
                    cursor.execute("""
                        SELECT timestamp FROM mediciones
                        WHERE ip = ? AND estado = 1 AND timestamp < ?
                        ORDER BY timestamp DESC LIMIT 1
                    """, (ip, ts))
                    prev_up = cursor.fetchone()
                    if prev_up:
                        cursor.execute("""
                            SELECT timestamp FROM mediciones
                            WHERE ip = ? AND estado = 0 AND timestamp > ?
                            ORDER BY timestamp ASC LIMIT 1
                        """, (ip, prev_up["timestamp"]))
                        primera_caida = cursor.fetchone()
                        inicio_caida = parse_ts(primera_caida["timestamp"]) if primera_caida else ts
                    else:
                        cursor.execute("""
                            SELECT timestamp FROM mediciones
                            WHERE ip = ? AND estado = 0
                            ORDER BY timestamp ASC LIMIT 1
                        """, (ip,))
                        primera_hist = cursor.fetchone()
                        inicio_caida = parse_ts(primera_hist["timestamp"]) if primera_hist else ts
                else:
                    inicio_caida = ts
            elif estado == 1 and en_caida:
                en_caida = False
                duracion_total = max(1.0, (ts - inicio_caida).total_seconds())
                # Duración circunscrita y fidedigna al período auditado
                impacto_ini = max(inicio_caida, cutoff_time)
                impacto_fin = min(ts, end_time)
                duracion_periodo = max(0.0, (impacto_fin - impacto_ini).total_seconds())

                desconexiones.append({
                    "inicio": inicio_caida,
                    "fin": ts,
                    "duracion_seg": duracion_total,
                    "duracion_periodo_seg": duracion_periodo,
                    "en_curso": False,
                })
                inicio_caida = None

        if en_caida and inicio_caida:
            duracion_total = max(1.0, (end_time - inicio_caida).total_seconds())
            impacto_ini = max(inicio_caida, cutoff_time)
            impacto_fin = end_time
            duracion_periodo = max(0.0, (impacto_fin - impacto_ini).total_seconds())

            desconexiones.append({
                "inicio": inicio_caida,
                "fin": end_time,
                "duracion_seg": duracion_total,
                "duracion_periodo_seg": duracion_periodo,
                "en_curso": True,
            })

        total_downtime_periodo = sum(d["duracion_periodo_seg"] for d in desconexiones)
        total_downtime_falla = sum(d["duracion_seg"] for d in desconexiones)

        microcortes = [d for d in desconexiones if d["duracion_seg"] < 30]
        cortes_medios = [d for d in desconexiones if 30 <= d["duracion_seg"] <= 300]
        caidas_criticas = [d for d in desconexiones if d["duracion_seg"] > 300]

        peor = max(desconexiones, key=lambda d: d["duracion_seg"]) if desconexiones else None
        peor_dict = None
        if peor:
            peor_dict = {
                "inicio": peor["inicio"].strftime("%d/%m %H:%M:%S") if hasattr(peor["inicio"], "strftime") else str(peor["inicio"]),
                "duracion_seg": peor["duracion_seg"],
                "duracion_str": self._formatear_duracion(peor["duracion_seg"]),
                "duracion_periodo_seg": peor.get("duracion_periodo_seg", peor["duracion_seg"]),
                "duracion_periodo_str": self._formatear_duracion(peor.get("duracion_periodo_seg", peor["duracion_seg"])),
                "en_curso": peor.get("en_curso", False),
            }

        total_samples = len(rows)
        up_samples = sum(1 for r in rows if r["estado"] == 1)
        uptime = (up_samples / total_samples * 100.0) if total_samples > 0 else 100.0

        latencias_sorted = sorted(latencias_validas)
        lat_avg = sum(latencias_validas) / len(latencias_validas) if latencias_validas else 0.0
        lat_p95 = latencias_sorted[int(len(latencias_sorted) * 0.95)] if latencias_sorted else lat_avg

        return {
            "total_desconexiones": len(desconexiones),
            "eventos_desconexion": desconexiones,
            "downtime_segundos": total_downtime_periodo,
            "downtime_str": self._formatear_duracion(total_downtime_periodo),
            "downtime_total_falla_segundos": total_downtime_falla,
            "downtime_total_falla_str": self._formatear_duracion(total_downtime_falla),
            "microcortes_count": len(microcortes),
            "cortes_medios_count": len(cortes_medios),
            "caidas_criticas_count": len(caidas_criticas),
            "peor_incidencia": peor_dict,
            "uptime_periodo": uptime,
            "latencia_promedio": lat_avg,
            "latencia_p95": lat_p95,
        }

    def obtener_timeline_incidencias(
        self,
        equipos,
        periodo_horas=24,
        modo="24h",
        turno_inicio="07:00",
        turno_fin="18:00",
    ):
        """
        Genera un timeline cronológico de incidencias mayores y caídas activas.
        Presenta fecha completa de inicio si la falla es previa y distingue entre el impacto
        dentro del período auditado y la duración total acumulada de la falla.
        """
        timeline = []
        now_dt = datetime.datetime.now()

        rango_ini = None
        rango_fin = None
        if "Turno" in modo:
            shift_start, shift_end = obtener_rango_turno_reciente(turno_inicio, turno_fin, now_dt)
            rango_ini = shift_start
            rango_fin = min(now_dt, shift_end)
        elif "Semanal" in modo:
            periodo_horas = 168

        for eq in equipos:
            ip = eq["ip"]
            analisis = self.analizar_desconexiones_y_downtime(
                ip,
                periodo_horas=periodo_horas,
                rango_inicio=rango_ini,
                rango_fin=rango_fin,
            )
            eventos = analisis.get("eventos_desconexion", [])
            for ev in eventos:
                dur_tot = ev.get("duracion_seg", 0.0)
                dur_per = ev.get("duracion_periodo_seg", dur_tot)

                if ev.get("en_curso") or dur_tot >= 20:
                    ini_dt = ev["inicio"]
                    fin_val = ev.get("fin")
                    en_curso = ev.get("en_curso", False)

                    # Formato de inicio: con fecha si es anterior a hoy
                    if hasattr(ini_dt, "date") and ini_dt.date() < now_dt.date():
                        ini_str = ini_dt.strftime("%d/%m %H:%M:%S")
                    elif hasattr(ini_dt, "strftime"):
                        ini_str = ini_dt.strftime("%H:%M:%S")
                    else:
                        ini_str = str(ini_dt)

                    # Formato de fin
                    if en_curso:
                        fin_str = "En curso (No recuperado)"
                        severidad = "🔴 Crítico (Offline)"
                    elif hasattr(fin_val, "strftime"):
                        if hasattr(fin_val, "date") and fin_val.date() < now_dt.date():
                            fin_str = fin_val.strftime("%d/%m %H:%M:%S")
                        else:
                            fin_str = fin_val.strftime("%H:%M:%S")
                        severidad = "🔴 Caída Mayor" if dur_tot >= 300 else "🟡 Intermitencia"
                    else:
                        fin_str = str(fin_val)
                        severidad = "🔴 Caída Mayor" if dur_tot >= 300 else "🟡 Intermitencia"

                    dur_per_str = self._formatear_duracion(dur_per)
                    dur_tot_str = self._formatear_duracion(dur_tot)

                    timeline.append({
                        "activo": eq.get("label", ip),
                        "ip": ip,
                        "inicio_dt": ini_dt,
                        "inicio_str": ini_str,
                        "fin_str": fin_str,
                        "duracion_seg": dur_tot,
                        "duracion_str": dur_tot_str,
                        "duracion_periodo_seg": dur_per,
                        "duracion_periodo_str": dur_per_str,
                        "severidad": severidad,
                        "en_curso": en_curso,
                    })

        timeline.sort(key=lambda x: (not x["en_curso"], -x["duracion_seg"]))
        return timeline

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
                    matriz_disponibilidad[d][h] = 0.0  # Sin muestras en la franja

        return {
            "disponibilidad": matriz_disponibilidad,
            "totales": matriz_total,
            "dias_etiquetas": ["L", "M", "X", "J", "V", "S", "D"],
            "horas_etiquetas": [f"{h:02d}h" for h in range(24)]
        }

    def obtener_matriz_semanal_turno(self, ip=None, turno_inicio="07:00", turno_fin="18:00", dias=7):
        """
        Calcula la matriz semanal (Lunes a Domingo) filtrada específicamente para las horas del turno configurado.
        """
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=dias)
        horas_turno = obtener_horas_turno(turno_inicio, turno_fin)
        ncols = len(horas_turno)
        matriz_up = [[0 for _ in range(ncols)] for _ in range(7)]
        matriz_total = [[0 for _ in range(ncols)] for _ in range(7)]

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
        parse_ts = _parse_timestamp
        hora_a_col = {h: idx for idx, h in enumerate(horas_turno)}

        for r in rows:
            ts = parse_ts(r["timestamp"])
            if ts.hour in hora_a_col:
                col = hora_a_col[ts.hour]
                dia = ts.weekday()
                matriz_total[dia][col] += 1
                if r["estado"] == 1:
                    matriz_up[dia][col] += 1

        matriz_disponibilidad = [[0.0 for _ in range(ncols)] for _ in range(7)]
        for d in range(7):
            for c in range(ncols):
                tot = matriz_total[d][c]
                matriz_disponibilidad[d][c] = (matriz_up[d][c] / tot) if tot > 0 else 0.0

        return {
            "disponibilidad": matriz_disponibilidad,
            "totales": matriz_total,
            "dias_etiquetas": ["L", "M", "X", "J", "V", "S", "D"],
            "horas_etiquetas": [f"{h:02d}h" for h in horas_turno],
            "horas_turno": horas_turno,
        }

    def obtener_telemetria_completa(
        self,
        equipos: list[dict],
        filtro_host: str = "Todos los Equipos",
        modo: str = "Semanal (7D x 24h)",
        turno_inicio: str = "07:00",
        turno_fin: str = "18:00",
        monitors_status: dict | None = None,
    ) -> dict:
        """
        Motor Industrial de Telemetría Unificada (Single-Pass Batch Pipeline).
        Ejecuta consultas agregadas en memoria en < 15ms eliminando bloqueos en el hilo UI.
        Toda la telemetría (KPIs, latencia, gauges, tabla y heatmap) se adapta automáticamente
        a la ventana de 24h o a la franja de Turno configurada según el modo seleccionado.
        """
        es_turno = "Turno" in modo
        monitors_status = monitors_status or {}
        horas_turno = obtener_horas_turno(turno_inicio, turno_fin)
        parse_ts = _parse_timestamp

        # 1. Determinar subconjunto de equipos a graficar según filtro
        if filtro_host != "Todos los Equipos":
            equipos_a_dibujar = [
                eq for eq in equipos
                if eq.get("label") == filtro_host or eq.get("ip") == filtro_host
            ]
            if not equipos_a_dibujar:
                equipos_a_dibujar = equipos
        else:
            equipos_a_dibujar = equipos

        # 2. Cargar mediciones acotadas a la ventana temporal (Turno o 24h)
        now_dt = datetime.datetime.now()
        if es_turno:
            shift_start, shift_end = obtener_rango_turno_reciente(turno_inicio, turno_fin, now_dt)
            query_start = shift_start
            query_end = min(now_dt, shift_end)
            latencia_min_x = shift_start
            latencia_max_x = shift_end
            latencia_title = f"📈 Comportamiento de Latencia Temporal (Turno {turno_inicio} a {turno_fin} │ Umbral SLA: 100 ms)"
            kpi_uptime_title = f"SLA Turno ({turno_inicio}-{turno_fin})"
        else:
            query_start = now_dt - datetime.timedelta(hours=24)
            query_end = now_dt
            latencia_min_x = query_start
            latencia_max_x = query_end
            latencia_title = "📈 Comportamiento de Latencia Temporal (Últimas 24 Horas │ Umbral SLA: 100 ms)"
            kpi_uptime_title = "SLA Global (24h)"

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT ip, timestamp, latencia, estado
            FROM mediciones
            WHERE timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp ASC
        """, (query_start, query_end))
        raw_rows = cursor.fetchall()

        # Agrupar por IP en memoria
        mediciones_periodo_por_ip = {eq["ip"]: [] for eq in equipos}
        for r in raw_rows:
            ip = r["ip"]
            if ip in mediciones_periodo_por_ip:
                ts = parse_ts(r["timestamp"])
                mediciones_periodo_por_ip[ip].append((ts, r["latencia"], r["estado"]))

        # 3. Calcular estadísticas consolidadas por equipo
        stats_por_equipo = {}
        total_downtime_sec = 0.0
        total_microcortes = 0
        uptimes_list = []
        latencias_actuales = []

        for eq in equipos:
            ip = eq["ip"]
            data_ip = mediciones_periodo_por_ip.get(ip, [])
            tot_samples = len(data_ip)
            up_samples = sum(1 for _, _, st in data_ip if st == 1)
            up_val = (up_samples / tot_samples * 100.0) if tot_samples > 0 else 100.0
            uptimes_list.append(up_val)

            # Algoritmo de desconexiones y microcortes
            desconexiones = []
            en_caida = False
            inicio_caida = None
            valid_lats = []

            for ts, lat, st in data_ip:
                if lat is not None and lat > 0:
                    valid_lats.append(lat)
                if st == 0 and not en_caida:
                    en_caida = True
                    inicio_caida = ts
                elif st == 1 and en_caida:
                    en_caida = False
                    dur = max(1.0, (ts - inicio_caida).total_seconds())
                    desconexiones.append(dur)
                    inicio_caida = None

            if en_caida and inicio_caida:
                dur = max(1.0, (datetime.datetime.now() - inicio_caida).total_seconds())
                desconexiones.append(dur)

            dt_sec = sum(desconexiones)
            micro_c = sum(1 for d in desconexiones if d < 30)
            total_downtime_sec += dt_sec
            total_microcortes += micro_c

            ult_lat = valid_lats[-1] if valid_lats else None
            if ult_lat is not None:
                latencias_actuales.append(ult_lat)

            stats_por_equipo[ip] = {
                "uptime": up_val,
                "downtime_sec": dt_sec,
                "downtime_str": self._formatear_duracion(dt_sec),
                "microcortes": micro_c,
                "ult_lat": ult_lat,
                "valid_lats": valid_lats,
            }

        # 4. KPIs Consolidados
        avg_uptime = sum(uptimes_list) / len(uptimes_list) if uptimes_list else 100.0
        avg_latencia = sum(latencias_actuales) / len(latencias_actuales) if latencias_actuales else 0.0
        downtime_str = self._formatear_duracion(total_downtime_sec)

        kpis = {
            "uptime": avg_uptime,
            "latencia": avg_latencia,
            "microcortes": total_microcortes,
            "downtime": downtime_str,
            "downtime_sec": total_downtime_sec,
        }

        # 5. Serie de Latencia para el Gráfico
        serie_latencia = []
        latencias_historicas = []
        for eq in equipos_a_dibujar:
            ip = eq["ip"]
            data_ip = mediciones_periodo_por_ip.get(ip, [])
            if data_ip:
                paso = max(1, len(data_ip) // 60)
                sampled = data_ip[::paso]
                x_vals = [pt[0] for pt in sampled]
                y_vals = [pt[1] if pt[1] is not None else 0 for pt in sampled]
                serie_latencia.append({
                    "label": eq["label"][:18],
                    "ip": ip,
                    "x_vals": x_vals,
                    "y_vals": y_vals,
                })
                latencias_historicas.extend([y for y in y_vals if y > 0])

        if latencias_historicas:
            min_l = min(latencias_historicas)
            avg_l = sum(latencias_historicas) / len(latencias_historicas)
            max_l = max(latencias_historicas)
            p95_l = float(np.percentile(latencias_historicas, 95))
            ult_l = latencias_actuales[-1] if latencias_actuales else avg_l
            ventana_txt = f"Turno {turno_inicio}-{turno_fin}" if es_turno else "24h"
            stats_text = (
                f"Métricas ({ventana_txt}):  Mín: {min_l:.1f}ms  │  Prom: {avg_l:.1f}ms  "
                f"│  P95: {p95_l:.1f}ms  │  Máx: {max_l:.1f}ms  │  Actual: {ult_l:.1f}ms"
            )
        else:
            ventana_txt = f"Turno {turno_inicio}-{turno_fin}" if es_turno else "24h"
            stats_text = f"Métricas ({ventana_txt}):  Sin registros de latencia disponibles para el período."

        # 6. Datos del Heatmap (Orden Natural 1:1 Canónico)
        if modo == "Semanal (7D x 24h)":
            target_ip = None if filtro_host == "Todos los Equipos" else next((eq["ip"] for eq in equipos if eq["label"] == filtro_host or eq["ip"] == filtro_host), None)
            matriz_res = self.obtener_matriz_semanal(ip=target_ip)
            heatmap_data = {
                "mode": "Semanal (7D x 24h)",
                "title": "🗓️ Matriz Semanal de Disponibilidad (Lunes a Domingo × 24 Horas)",
                "rango_subtitulo": "Últimos 7 Días",
                "ncols": 24,
                "nrows": 7,
                "col_labels": [f"{h:02d}h" for h in range(24)],
                "row_labels": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"],
                "matriz_disp": matriz_res["disponibilidad"],
                "horas_turno": list(range(24)),
            }
        elif modo == "Semanal (7D x Turno)":
            target_ip = None if filtro_host == "Todos los Equipos" else next((eq["ip"] for eq in equipos if eq["label"] == filtro_host or eq["ip"] == filtro_host), None)
            matriz_res = self.obtener_matriz_semanal_turno(ip=target_ip, turno_inicio=turno_inicio, turno_fin=turno_fin)
            heatmap_data = {
                "mode": "Semanal (7D x Turno)",
                "title": f"🗓️ Matriz Semanal de Disponibilidad en Turno ({turno_inicio} a {turno_fin})",
                "rango_subtitulo": f"Últimos 7 Días • Horario {turno_inicio} a {turno_fin}",
                "ncols": len(horas_turno),
                "nrows": 7,
                "col_labels": [f"{h:02d}h" for h in horas_turno],
                "row_labels": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"],
                "matriz_disp": matriz_res["disponibilidad"],
                "horas_turno": horas_turno,
            }
        elif modo == "Por Equipo (Turno)":
            hora_a_col = {h: idx for idx, h in enumerate(horas_turno)}
            ncols = len(horas_turno)
            nrows = len(equipos_a_dibujar)
            dispo_equipos = []

            for eq in equipos_a_dibujar:
                ip = eq["ip"]
                data_ip = mediciones_periodo_por_ip.get(ip, [])
                bloques_up = [0] * ncols
                bloques_tot = [0] * ncols
                for ts, _, st in data_ip:
                    if ts.hour in hora_a_col:
                        c = hora_a_col[ts.hour]
                        bloques_tot[c] += 1
                        if st == 1:
                            bloques_up[c] += 1
                disp_eq = [(bloques_up[c] / bloques_tot[c]) if bloques_tot[c] > 0 else 0.0 for c in range(ncols)]
                dispo_equipos.append(disp_eq)

            labels_hm = [eq["label"][:26] for eq in equipos_a_dibujar]
            heatmap_data = {
                "mode": "Por Equipo (Turno)",
                "title": f"🗓️ Matriz de Disponibilidad por Dispositivo en Turno ({turno_inicio} a {turno_fin})",
                "rango_subtitulo": f"Turno {turno_inicio} a {turno_fin} ({len(horas_turno)} horas)",
                "ncols": ncols,
                "nrows": nrows,
                "col_labels": [f"{h:02d}h" for h in horas_turno],
                "row_labels": labels_hm,
                "matriz_disp": dispo_equipos,
                "horas_turno": horas_turno,
                "equipos_lista": equipos_a_dibujar,
            }
        else: # "Por Equipo (24h)"
            ncols = 24
            nrows = len(equipos_a_dibujar)
            dispo_equipos = []

            for eq in equipos_a_dibujar:
                ip = eq["ip"]
                data_ip = mediciones_periodo_por_ip.get(ip, [])
                bloques_up = [0] * 24
                bloques_tot = [0] * 24
                for ts, _, st in data_ip:
                    h = ts.hour
                    if 0 <= h < 24:
                        bloques_tot[h] += 1
                        if st == 1:
                            bloques_up[h] += 1
                disp_eq = [(bloques_up[h] / bloques_tot[h]) if bloques_tot[h] > 0 else 0.0 for h in range(24)]
                dispo_equipos.append(disp_eq)

            labels_hm = [eq["label"][:26] for eq in equipos_a_dibujar]
            heatmap_data = {
                "mode": "Por Equipo (24h)",
                "title": "🗓️ Matriz de Disponibilidad por Dispositivo (Últimas 24 Horas)",
                "rango_subtitulo": "Últimas 24 Horas (00h a 23h)",
                "ncols": 24,
                "nrows": nrows,
                "col_labels": [f"{h:02d}h" for h in range(24)],
                "row_labels": labels_hm,
                "matriz_disp": dispo_equipos,
                "horas_turno": list(range(24)),
                "equipos_lista": equipos_a_dibujar,
            }

        # 7. Gauges Data
        gauges_data = []
        for eq in equipos_a_dibujar:
            st = stats_por_equipo.get(eq["ip"], {"uptime": 100.0})
            ubicacion = eq.get("ubicacion", "").strip()
            if not ubicacion:
                lbl_low = eq.get("label", "").lower()
                if "quilicura" in lbl_low:
                    ubicacion = "Quilicura"
                elif "renca" in lbl_low:
                    ubicacion = "Renca"
            gauges_data.append({
                "ip": eq["ip"],
                "label": eq["label"][:16],
                "ubicacion": ubicacion,
                "uptime": st["uptime"],
            })

        # 8. Tabla Detallada Data
        tabla_data = []
        for eq in equipos_a_dibujar:
            ip = eq["ip"]
            st = stats_por_equipo.get(ip, {"uptime": 100.0, "downtime_str": "0s", "microcortes": 0, "ult_lat": None})
            st_text = monitors_status.get(ip, "Desconectado")
            lat_str = f"{st['ult_lat']:.1f} ms" if st["ult_lat"] is not None else "---"
            tabla_data.append({
                "ip": ip,
                "label": eq["label"][:22],
                "status": st_text,
                "lat_str": lat_str,
                "uptime_val": st["uptime"],
                "micro_c": st["microcortes"],
                "down_str": st["downtime_str"],
            })

        return {
            "es_turno": es_turno,
            "turno_inicio": turno_inicio,
            "turno_fin": turno_fin,
            "equipos_a_dibujar": equipos_a_dibujar,
            "kpis": kpis,
            "kpi_uptime_title": kpi_uptime_title,
            "serie_latencia": serie_latencia,
            "stats_text": stats_text,
            "latencia_min_x": latencia_min_x,
            "latencia_max_x": latencia_max_x,
            "latencia_title": latencia_title,
            "heatmap_data": heatmap_data,
            "gauges_data": gauges_data,
            "tabla_data": tabla_data,
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
            if analisis["total_desconexiones"] > 0 or analisis["uptime_periodo"] < 99.0 or analisis["downtime_segundos"] > 0:
                equipos_con_fallas.append((eq.get("label", ip), analisis))

        uptime_promedio = sum(uptimes) / len(uptimes) if uptimes else 100.0
        lat_global = sum(latencias_avg) / len(latencias_avg) if latencias_avg else 0.0

        # Priorizar siempre los equipos con mayor caída/downtime en el diagnóstico ejecutivo
        equipos_con_fallas.sort(key=lambda item: item[1]["downtime_segundos"], reverse=True)

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

    def close(self):
        """Cierra explícitamente la conexión a la base de datos SQLite."""
        try:
            if hasattr(self, "conn") and self.conn:
                self.conn.close()
        except Exception:
            pass

    def cerrar(self):
        self.close()

    def __del__(self):
        """Asegura que la conexión a la base de datos se cierre al destruir el objeto."""
        self.close()