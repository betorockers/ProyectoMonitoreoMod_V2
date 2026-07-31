# 🚀 Plan de Mejoras Definitivo v2.0
## Sistema de Monitoreo de redes y equipos Argos Guard
### Adaptado al Contexto Operativo Real

---

## 📋 Resumen Ejecutivo del Contexto

### 🔒 **Restricciones Operativas**

> [!IMPORTANT]
> **Tu Situación Actual (Enero 2026)**
> 
> **Red:**
> - ✅ Monitoreo SOLO dentro de red local (LAN)
> - ❌ Sin acceso desde internet (políticas de seguridad)
> 
> **Operación:**
> - 💻 App corre en PC personal de Beto
> - ⏰ Monitoreo SOLO durante horario laboral
> - 🌙 SIN supervisión nocturna ni fines de semana
> 
> **Equipos Monitoreados:**
> - 🏢 Subcontratados (proveedor externo)
> - ✅ Solo tienes: Dirección IP de cada equipo
> - ❌ NO tienes: SSH, RDP, credenciales, APIs, SNMP
> - 🔐 Monitoreo "Black Box" (solo conectividad de red)
> 
> **Tu Responsabilidad:**
> - 🎯 Detectar equipos caídos/inalcanzables
> - 📞 Reportar al proveedor con evidencia
> - 📊 Tracking de SLA/uptime

---

## 🎯 Objetivos de las Mejoras

### **Corto Plazo (1-2 meses)**
1. ✅ Gráficos tipo Grafana en pestaña "Historial"
2. ✅ Métricas históricas (latencia, uptime, disponibilidad)
3. ✅ Mejor visualización y análisis de datos

### **Mediano Plazo (2-4 meses)**
1. ✅ Migración a servidor dedicado 24/7 (Raspberry Pi)
2. ✅ Bot de Telegram para alertas fuera de horario
3. ✅ Base de datos SQLite para histórico completo

### **Largo Plazo (4-6 meses)**
1. ✅ Dashboard web accesible desde LAN
2. ✅ Reportes automáticos al proveedor
3. ✅ Integración con backend Java (si aplica)

---

## 📊 Roadmap de Implementación

### 🟢 **FASE 1: Visualización y Métricas** (Semanas 1-3)
**Objetivo:** Mejorar la UI actual con gráficos tipo Grafana

#### **Mejora 1.1: Sistema de Pestañas**
**Prioridad:** 🔴 Alta | **Complejidad:** 🟢 Baja | **Tiempo:** 2-3 horas

**Implementación:**
```python
# Convertir la app de vista única a sistema de pestañas
self.tabview = customtkinter.CTkTabview(self)
self.tab_monitoreo = self.tabview.add("🔴 Monitoreo Activo")
self.tab_historial = self.tabview.add("📊 Historial de Eventos")
```

**Resultado:**
- ✅ Pestaña 1: Tarjetas actuales (sin cambios)
- ✅ Pestaña 2: Espacio para gráficos

**Beneficio:** Organización clara, UX profesional

---

#### **Mejora 1.2: Captura de Métricas Históricas**
**Prioridad:** 🔴 Alta | **Complejidad:** 🟡 Media | **Tiempo:** 2-3 horas

**¿Qué métricas capturar?**
- ✅ **Latencia** (ms) - extraída del output de ping
- ✅ **Estado** (conectado/desconectado)
- ✅ **Timestamp** de cada medición
- ✅ **Packet loss** (opcional)
- ✅ **HTTP response time** (si equipos exponen web)

**Implementación:**
```python
class MetricasHistoricas:
    def __init__(self, max_puntos=1440):  # 24h @ 1 minuto
        self.datos = {
            'ip': {
                'timestamps': deque(maxlen=max_puntos),
                'latencias': deque(maxlen=max_puntos),
                'estados': deque(maxlen=max_puntos)
            }
        }
```

**Almacenamiento:** Memoria (deque con límite)

**Beneficio:** Base para todos los gráficos

---

#### **Mejora 1.3: Gráfico de Latencia (Time Series)**
**Prioridad:** 🔴 Alta | **Complejidad:** 🟡 Media | **Tiempo:** 3-4 horas

**Tipo:** Line chart como en Grafana

**Características:**
- 📈 Últimas 24 horas de latencia
- 🎨 Una línea por equipo (colores diferenciados)
- 🔄 Auto-actualización cada 60 segundos
- 🎯 Zoom automático al rango de datos

**Librerías:** `matplotlib` + `FigureCanvasTkAgg`

**Ejemplo visual:**
```
Latencia - Últimas 24 Horas
┌────────────────────────────────────┐
│ 100ms ─╱╲─────────╱╲──────────    │
│  50ms ╱──╲───────╱──╲─────────    │
│   0ms ───────────────────────────  │
│       00:00  06:00  12:00  18:00   │
│  — LPR 1  — LPR 2  — Tótem 1      │
└────────────────────────────────────┘
```

**Valor:** Detectar patrones (ej: latencia sube siempre a las 14:00)

---

#### **Mejora 1.4: Gauges de Uptime**
**Prioridad:** 🔴 Alta | **Complejidad:** 🟡 Media | **Tiempo:** 2-3 horas

**Tipo:** Medidores circulares (gauges)

**Características:**
- 🎯 % de uptime últimos 7/30 días
- 🟢 Verde: >99% | 🟡 Amarillo: 95-99% | 🔴 Rojo: <95%
- 📊 Uno por equipo en grid horizontal

**Ejemplo visual:**
```
┌─────────┐  ┌─────────┐  ┌─────────┐
│  LPR 1  │  │  LPR 2  │  │ Tótem 1 │
│  99.8%  │  │  87.2%  │  │  100%   │
│   🟢    │  │   🟡    │  │   🟢    │
└─────────┘  └─────────┘  └─────────┘
```

**Valor:** Vista rápida de confiabilidad de cada equipo

---

#### **Mejora 1.5: Heatmap de Disponibilidad**
**Prioridad:** 🟡 Media | **Complejidad:** 🟡 Media | **Tiempo:** 3-4 horas

**Tipo:** Calendario de calor (heatmap)

**Características:**
- 🗓️ Última semana (7 días x 24 horas)
- 🟩 Verde: Online | 🟨 Amarillo: Latencia alta | 🟥 Rojo: Offline
- 📊 Identifica patrones temporales

**Ejemplo visual:**
```
Disponibilidad Semanal
      00  04  08  12  16  20  24
Lun   🟩  🟩  🟩  🟩  🟩  🟩  🟩  100%
Mar   🟩  🟩  🟥  🟥  🟩  🟩  🟩   71%
Mié   🟩  🟩  🟩  🟩  🟩  🟩  🟩  100%
```

**Valor:** "Siempre cae los martes de 8-12" → patrón de mantenimiento

---

#### **Mejora 1.6: Tabla de Eventos en Tiempo Real**
**Prioridad:** 🟡 Media | **Complejidad:** 🟢 Baja | **Tiempo:** 1-2 horas

**Tipo:** Tabla texto formateada

**Características:**
- 📋 Estado actual de todos los equipos
- ⏱️ Última actualización
- 📊 Latencia actual
- 🔴🟢 Iconos de estado

**Ejemplo:**
```
┌────────────┬─────────┬──────────┬────────┐
│ Equipo     │ Estado  │ Latencia │ Hora   │
├────────────┼─────────┼──────────┼────────┤
│ 🟢 LPR 1   │ Online  │  12ms    │ 10:45  │
│ 🔴 LPR 2   │ Offline │  ---     │ 09:32  │
│ 🟢 Tótem 1 │ Online  │   8ms    │ 10:45  │
└────────────┴─────────┴──────────┴────────┘
```

---

**📦 Resumen Fase 1:**
- ✅ Sistema de pestañas implementado
- ✅ 4 tipos de visualizaciones tipo Grafana
- ✅ Métricas históricas capturadas
- ✅ UX profesional y moderna

**Tiempo total:** 2-3 semanas (trabajo part-time)

---

### 🔴 **FASE 2: Servidor 24/7 y Alertas** (Semanas 4-6)
**Objetivo:** Monitoreo continuo sin depender de tu PC

#### **Mejora 2.1: Adquisición de Hardware**
**Prioridad:** 🔴 CRÍTICA | **Complejidad:** 🟢 Baja | **Inversión:** $120 USD

**Opción recomendada:** Raspberry Pi 5 (4GB)

**Comprar:**
```
🛒 Raspberry Pi 5 (4GB)           $80
🛒 Case con ventilación            $15
🛒 MicroSD 64GB (Clase 10)         $12
🛒 Fuente oficial 5V 3A            $12
🛒 Cable Ethernet Cat6 largo       $10
───────────────────────────────────────
TOTAL:                            ~$129
```

**Dónde comprar:**
- MercadoLibre Argentina
- Tiendas de electrónica locales
- Amazon (si envían)

**Consumo:** ~5W (costo eléctrico: $6.5/año)

---

#### **Mejora 2.2: Setup del Servidor**
**Prioridad:** 🔴 Alta | **Complejidad:** 🟡 Media | **Tiempo:** 1 día

**Sistema Operativo:** Raspberry Pi OS Lite (64-bit, sin GUI)

**Pasos de instalación:**
```bash
# 1. Flashear microSD con Raspberry Pi Imager
#    - OS: Raspberry Pi OS Lite (64-bit)
#    - Configurar WiFi/Ethernet
#    - Habilitar SSH

# 2. Primera conexión
ssh pi@192.168.1.100

# 3. Actualizar sistema
sudo apt update && sudo apt upgrade -y

# 4. Instalar Python y dependencias
sudo apt install python3 python3-pip python3-venv git -y

# 5. Copiar proyecto
scp -r ProyectoMonitoreoMod_V2/ pi@192.168.1.100:/home/pi/

# 6. Crear entorno virtual
cd /home/pi/ProyectoMonitoreoMod_V2
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

#### **Mejora 2.3: Modo Headless (Sin GUI)**
**Prioridad:** 🔴 Alta | **Complejidad:** 🟡 Media | **Tiempo:** 2-3 horas

**Problema:** CustomTkinter requiere display (GUI)

**Solución:** Crear modo headless que solo ejecute lógica de monitoreo

**Implementación:**
```python
# main.py - Modificado

import os

HEADLESS = os.getenv('HEADLESS', 'false').lower() == 'true'

if HEADLESS:
    # Modo servidor (sin GUI)
    print("Iniciando en modo headless (servidor)...")
    from monitor_daemon import MonitorDaemon
    daemon = MonitorDaemon(equipos_to_monitor)
    daemon.run()  # Loop infinito
else:
    # Modo desktop (con GUI)
    from monitor import App
    app = App(equipos_to_monitor)
    app.mainloop()
```

**Nuevo archivo:** `monitor_daemon.py`
```python
# monitor_daemon.py - Backend sin GUI

class MonitorDaemon:
    def __init__(self, equipos):
        self.equipos = equipos
        self.metricas = MetricasHistoricas()
        # Inicializar DB, Telegram, etc.
    
    def run(self):
        # Monitorear en threads
        for equipo in self.equipos:
            thread = threading.Thread(
                target=self.monitor_equipo,
                args=(equipo,),
                daemon=True
            )
            thread.start()
        
        # Mantener vivo
        while True:
            time.sleep(60)
            self.check_health()
```

---

#### **Mejora 2.4: Servicio Systemd (Auto-start)**
**Prioridad:** 🔴 Alta | **Complejidad:** 🟢 Baja | **Tiempo:** 30 min

**Crear servicio:**
```bash
sudo nano /etc/systemd/system/monitoreo.service
```

```ini
[Unit]
Description=Monitor Control de Accesos Anvic
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/ProyectoMonitoreoMod_V2
Environment="HEADLESS=true"
Environment="PATH=/home/pi/ProyectoMonitoreoMod_V2/venv/bin"
ExecStart=/home/pi/ProyectoMonitoreoMod_V2/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Habilitar y arrancar
sudo systemctl daemon-reload
sudo systemctl enable monitoreo.service
sudo systemctl start monitoreo.service

# Verificar
sudo systemctl status monitoreo.service
```

**Resultado:** App arranca automáticamente al encender Raspberry Pi

---

#### **Mejora 2.5: Bot de Telegram**
**Prioridad:** 🔴 CRÍTICA | **Complejidad:** 🟡 Media | **Tiempo:** 2-3 horas
**Estado:** ✅ COMPLETADO

**Implementación Realizada:**
- Integrado en `monitor.py` y `telegram_alerter.py`.
- Configurable desde la UI (Pestaña Gestión de Usuarios).
- Restricción de horario laboral (09:00 - 17:00) implementada.

---

#### **Mejora 2.6: Configuración de Red Estática**
**Prioridad:** 🟡 Media | **Complejidad:** 🟢 Baja | **Tiempo:** 15 min

**¿Por qué IP fija?**
- ✅ Siempre accedes con la misma IP
- ✅ No cambia después de reinicio
- ✅ Fácil de recordar

**Configuración:**
```bash
sudo nano /etc/dhcpcd.conf

# Agregar al final:
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8
```

**Reiniciar red:**
```bash
sudo systemctl restart dhcpcd
```

---

**📦 Resumen Fase 2:**
- ✅ Raspberry Pi configurado y corriendo 24/7
- ✅ Servicio systemd auto-start
- ✅ Telegram bot enviando alertas
- ✅ IP fija para acceso predecible
- ✅ Monitoreo continuo SIN interrupciones

**Tiempo total:** 2-3 semanas

**Inversión:** $120-150 USD (una vez)

---

### 🔵 **FASE 3: Base de Datos y Persistencia** (Semanas 7-9)
**Objetivo:** Historial completo y reportes confiables

#### **Mejora 3.1: Migración a SQLite**
**Prioridad:** 🔴 Alta | **Complejidad:** 🟡 Media | **Tiempo:** 1 semana

**¿Por qué SQLite?**
- ✅ Sin configuración (archivo .db)
- ✅ Incluido en Python
- ✅ Suficiente para tu caso de uso
- ✅ Consultas SQL para reportes

**Schema propuesto:**
```sql
-- equipos.sql

CREATE TABLE equipos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip TEXT UNIQUE NOT NULL,
    label TEXT NOT NULL,
    tipo TEXT,  -- 'LPR', 'Totem', 'Kiosko'
    instalacion TEXT,  -- 'Principal', 'Secundaria'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE metricas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipo_id INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    latencia_ms REAL,
    estado TEXT,  -- 'conectado', 'desconectado'
    packet_loss REAL,
    mac_address TEXT,
    FOREIGN KEY (equipo_id) REFERENCES equipos(id)
);

CREATE INDEX idx_metricas_timestamp ON metricas(equipo_id, timestamp);

CREATE TABLE desconexiones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipo_id INTEGER,
    inicio DATETIME NOT NULL,
    fin DATETIME,
    duracion_segundos INTEGER,
    FOREIGN KEY (equipo_id) REFERENCES equipos(id)
);

CREATE TABLE eventos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipo_id INTEGER,
    tipo TEXT,  -- 'caida', 'recuperacion', 'latencia_alta'
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    detalles TEXT,
    FOREIGN KEY (equipo_id) REFERENCES equipos(id)
);
```

**Consultas útiles:**
```sql
-- Uptime últimos 30 días
SELECT 
    e.label,
    (SUM(CASE WHEN m.estado = 'conectado' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as uptime_percent
FROM equipos e
JOIN metricas m ON e.id = m.equipo_id
WHERE m.timestamp > datetime('now', '-30 days')
GROUP BY e.id, e.label;

-- Latencia promedio por hora del día
SELECT 
    strftime('%H', timestamp) as hora,
    AVG(latencia_ms) as latencia_promedio
FROM metricas
WHERE equipo_id = 1
  AND timestamp > datetime('now', '-7 days')
GROUP BY hora
ORDER BY hora;

-- Desconexiones más largas
SELECT 
    e.label,
    d.inicio,
    d.fin,
    d.duracion_segundos,
    (d.duracion_segundos / 60) as duracion_minutos
FROM desconexiones d
JOIN equipos e ON d.equipo_id = e.id
WHERE d.duracion_segundos > 600  -- Más de 10 minutos
ORDER BY d.duracion_segundos DESC
LIMIT 10;
```

**Implementación:**
```python
# database.py

import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path='monitor.db'):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.crear_tablas()
    
    def crear_tablas(self):
        with open('schema.sql', 'r') as f:
            self.conn.executescript(f.read())
        self.conn.commit()
    
    def agregar_metrica(self, equipo_id, latencia, estado, mac=None):
        self.conn.execute("""
            INSERT INTO metricas (equipo_id, latencia_ms, estado, mac_address)
            VALUES (?, ?, ?, ?)
        """, (equipo_id, latencia, estado, mac))
        self.conn.commit()
    
    def obtener_latencia_historica(self, equipo_id, horas=24):
        cursor = self.conn.execute("""
            SELECT timestamp, latencia_ms 
            FROM metricas
            WHERE equipo_id = ?
              AND timestamp > datetime('now', ? || ' hours')
            ORDER BY timestamp
        """, (equipo_id, -horas))
        return cursor.fetchall()
    
    def calcular_uptime(self, equipo_id, dias=30):
        cursor = self.conn.execute("""
            SELECT 
                (SUM(CASE WHEN estado = 'conectado' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as uptime
            FROM metricas
            WHERE equipo_id = ?
              AND timestamp > datetime('now', ? || ' days')
        """, (equipo_id, -dias))
        
        result = cursor.fetchone()
        return result['uptime'] if result else 100.0
```

**Actualizar gráficos para usar DB:**
```python
# En actualizar_graficos()

for equipo in self.equipos_a_monitorear:
    equipo_id = equipo['id']
    
    # Obtener datos de DB en vez de memoria
    datos = db.obtener_latencia_historica(equipo_id, horas=24)
    
    timestamps = [row['timestamp'] for row in datos]
    latencias = [row['latencia_ms'] for row in datos]
    
    self.ax_latencia.plot(timestamps, latencias, label=equipo['label'])
```

---

#### **Mejora 3.2: Backup Automático**
**Prioridad:** 🔴 Alta | **Complejidad:** 🟢 Baja | **Tiempo:** 1-2 horas

**Estrategia:**
- 📅 Backup diario automático
- 🔄 Rotación (últimos 30 backups)
- ☁️ Upload opcional a cloud (Dropbox, Google Drive)

**Implementación:**
```python
# backup_manager.py

import shutil
import os
from datetime import datetime, timedelta
import schedule

class BackupManager:
    def __init__(self, db_path='monitor.db', backup_dir='backups'):
        self.db_path = db_path
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)
    
    def crear_backup(self):
        """Crea backup con timestamp"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(self.backup_dir, f'monitor_{timestamp}.db')
        
        shutil.copy2(self.db_path, backup_path)
        print(f"✅ Backup creado: {backup_path}")
        
        self.limpiar_backups_antiguos()
        return backup_path
    
    def limpiar_backups_antiguos(self, dias_mantener=30):
        """Eliminar backups más antiguos que X días"""
        limite = datetime.now() - timedelta(days=dias_mantener)
        
        for archivo in os.listdir(self.backup_dir):
            if archivo.endswith('.db'):
                ruta = os.path.join(self.backup_dir, archivo)
                timestamp_archivo = datetime.fromtimestamp(os.path.getmtime(ruta))
                
                if timestamp_archivo < limite:
                    os.remove(ruta)
                    print(f"🗑️ Backup antiguo eliminado: {archivo}")
    
    def programar_backups(self):
        """Backup diario a las 23:00"""
        schedule.every().day.at("23:00").do(self.crear_backup)
        
        # Loop en thread
        def run_schedule():
            while True:
                schedule.run_pending()
                time.sleep(60)
        
        thread = threading.Thread(target=run_schedule, daemon=True)
        thread.start()

# Uso
backup_manager = BackupManager()
backup_manager.programar_backups()
```

---

#### **Mejora 3.3: Reportes Automáticos**
**Prioridad:** 🟡 Media | **Complejidad:** 🟡 Media | **Tiempo:** 1 semana

**Tipos de reportes:**

**1. Reporte Diario (Email/Telegram)**
```
📊 REPORTE DIARIO - 14/01/2026

✅ Equipos Online: 4/5 (80%)
❌ Equipos Offline: 1/5

Incidencias:
• LPR Salida: Caído de 02:35 a 03:12 (37 minutos)

Latencia promedio:
• LPR Entrada: 12ms
• Tótem 1: 8ms
• Tótem 2: 10ms

Próximo reporte: 15/01/2026 09:00
```

**2. Reporte Semanal (PDF)**
- Gráfico de disponibilidad (7 días)
- Top 3 equipos más confiables
- Top 3 equipos con más problemas
- Total de horas caídas por equipo

**3. Reporte Mensual (Excel + PDF)**
- SLA compliance (% uptime)
- Comparativa mes actual vs anterior
- Heatmap de disponibilidad
- Recomendaciones

**Implementación:**
```python
# reporter.py

from fpdf import FPDF
import pandas as pd
from datetime import datetime, timedelta

class ReportGenerator:
    def __init__(self, db):
        self.db = db
    
    def generar_reporte_diario(self):
        """Reporte simple para Telegram"""
        # Consultar DB
        equipos_online = self.db.contar_equipos_online()
        equipos_total = self.db.contar_equipos_total()
        incidencias = self.db.obtener_incidencias_dia()
        
        reporte = f"""
📊 *REPORTE DIARIO* - {datetime.now().strftime('%d/%m/%Y')}

✅ Equipos Online: {equipos_online}/{equipos_total} ({equipos_online/equipos_total*100:.0f}%)

"""
        
        if incidencias:
            reporte += "❌ Incidencias:\\n"
            for inc in incidencias:
                reporte += f"• {inc['equipo']}: {inc['descripcion']}\\n"
        else:
            reporte += "✅ Sin incidencias registradas\\n"
        
        return reporte
    
    def generar_reporte_pdf_mensual(self, mes, anio):
        """Reporte PDF completo"""
        pdf = FPDF()
        pdf.add_page()
        
        # Header
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, f"Reporte Mensual - {mes}/{anio}", ln=True)
        
        # Sección 1: Resumen
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, "1. Resumen Ejecutivo", ln=True)
        
        # Obtener datos de DB
        uptime_promedio = self.db.calcular_uptime_promedio_mes(mes, anio)
        pdf.cell(0, 10, f"Uptime promedio: {uptime_promedio:.2f}%", ln=True)
        
        # Sección 2: Por equipo
        pdf.cell(0, 10, "2. Detalle por Equipo", ln=True)
        
        equipos = self.db.obtener_equipos()
        for equipo in equipos:
            uptime = self.db.calcular_uptime(equipo['id'], dias=30)
            pdf.cell(0, 10, f"{equipo['label']}: {uptime:.1f}%", ln=True)
        
        # Guardar
        filename = f"reporte_{mes}_{anio}.pdf"
        pdf.output(filename)
        return filename
```

---

**📦 Resumen Fase 3:**
- ✅ Base de datos SQLite con schema completo
- ✅ Backups automáticos diarios
- ✅ Reportes automáticos (diario/semanal/mensual)
- ✅ Consultas SQL para análisis profundo
- ✅ Historial ilimitado (vs 24h en memoria)

**Tiempo total:** 2-3 semanas

---

### 🟣 **FASE 4: Dashboard Web y Acceso Remoto** (Semanas 10-14)
**Objetivo:** Acceso desde cualquier PC/tablet en la red local

#### **Mejora 4.1: Backend API (FastAPI)**
**Prioridad:** 🟡 Media | **Complejidad:** 🔴 Alta | **Tiempo:** 2 semanas

**Stack:**
- **FastAPI** - Framework web moderno y rápido
- **Uvicorn** - Servidor ASGI
- **SQLite** - DB (ya implementada)

**Estructura:**
```
ProyectoMonitoreoMod_V2/
├── backend/
│   ├── main.py              # Entry point FastAPI
│   ├── models.py            # Modelos Pydantic
│   ├── database.py          # Conexión DB
│   ├── routers/
│   │   ├── equipos.py       # /api/equipos
│   │   ├── metricas.py      # /api/metricas
│   │   └── reportes.py      # /api/reportes
│   └── websocket.py         # Real-time updates
├── frontend/                # React app (próxima fase)
└── monitor_daemon.py        # Daemon de monitoreo
```

**Endpoints principales:**
```python
# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Monitor Anvic API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En prod: solo IPs de red local
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Monitor Anvic API v2.0"}

@app.get("/api/equipos")
async def get_equipos():
    """Listar todos los equipos"""
    equipos = db.obtener_equipos()
    return {"equipos": equipos}

@app.get("/api/equipos/{equipo_id}/status")
async def get_equipo_status(equipo_id: int):
    """Estado actual de un equipo"""
    status = db.obtener_status_actual(equipo_id)
    return status

@app.get("/api/metricas/latencia")
async def get_latencia_historica(equipo_id: int, horas: int = 24):
    """Datos para gráfico de latencia"""
    datos = db.obtener_latencia_historica(equipo_id, horas)
    
    return {
        "equipo_id": equipo_id,
        "data": [
            {"timestamp": row['timestamp'], "latencia": row['latencia_ms']}
            for row in datos
        ]
    }

@app.get("/api/metricas/uptime")
async def get_uptime_summary():
    """Uptime de todos los equipos"""
    equipos = db.obtener_equipos()
    
    result = []
    for equipo in equipos:
        uptime = db.calcular_uptime(equipo['id'], dias=30)
        result.append({
            "id": equipo['id'],
            "label": equipo['label'],
            "uptime_30d": uptime
        })
    
    return {"equipos": result}

# WebSocket para updates en tiempo real
@app.websocket("/ws/updates")
async def websocket_updates(websocket: WebSocket):
    await websocket.accept()
    
    while True:
        # Enviar estado actual cada 5 segundos
        estado = obtener_estado_todos_equipos()
        await websocket.send_json(estado)
        await asyncio.sleep(5)
```

**Run server:**
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Acceso desde red local:**
```
http://192.168.1.100:8000/docs  # Swagger UI
http://192.168.1.100:8000/api/equipos
```

---

#### **Mejora 4.2: Frontend Dashboard (React)**
**Prioridad:** 🟡 Media | **Complejidad:** 🔴 Alta | **Tiempo:** 3-4 semanas

**Stack:**
- **React 18** + TypeScript
- **Vite** - Build tool
- **TanStack Query** - Data fetching
- **Recharts** - Gráficos
- **Tailwind CSS** - Estilos

**Componentes principales:**
```
src/
├── components/
│   ├── EquipoCard.tsx       # Tarjeta de equipo
│   ├── LatenciaChart.tsx    # Gráfico de latencia
│   ├── UptimeGauge.tsx      # Gauge circular
│   ├── HeatmapCalendar.tsx  # Heatmap disponibilidad
│   └── EventsTable.tsx      # Tabla de eventos
├── pages/
│   ├── Dashboard.tsx        # Página principal
│   ├── EquipoDetail.tsx     # Detalle de un equipo
│   └── Reports.tsx          # Reportes
├── hooks/
│   ├── useEquipos.ts        # Hook para equipos
│   └── useMetricas.ts       # Hook para métricas
└── App.tsx
```

**Ejemplo componente:**
```tsx
// src/components/LatenciaChart.tsx

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import { useMetricas } from '../hooks/useMetricas';

export function LatenciaChart({ equipoId }: { equipoId: number }) {
  const { data, isLoading } = useMetricas(equipoId, 24); // 24 horas
  
  if (isLoading) return <div>Cargando...</div>;
  
  return (
    <div className="bg-gray-800 p-6 rounded-lg">
      <h3 className="text-xl font-bold text-white mb-4">
        📈 Latencia - Últimas 24 Horas
      </h3>
      
      <LineChart width={800} height={400} data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#444" />
        <XAxis dataKey="timestamp" stroke="#fff" />
        <YAxis stroke="#fff" label={{ value: 'Latencia (ms)', angle: -90 }} />
        <Tooltip contentStyle={{ backgroundColor: '#333', border: 'none' }} />
        <Legend />
        <Line 
          type="monotone" 
          dataKey="latencia" 
          stroke="#00d9ff" 
          strokeWidth={2}
          dot={{ r: 3 }}
        />
      </LineChart>
    </div>
  );
}
```

**Deployment:**
```bash
# Build
npm run build

# Servir con nginx (Raspberry Pi)
sudo apt install nginx
sudo cp -r dist/* /var/www/html/

# Acceder desde red local
http://192.168.1.100
```

---

#### **Mejora 4.3: PWA (Progressive Web App)**
**Prioridad:** 🟢 Baja | **Complejidad:** 🟢 Baja | **Tiempo:** 1-2 horas

**¿Qué es PWA?**
Dashboard web que se puede "instalar" como app en móvil/tablet

**Beneficios:**
- ✅ Se siente como app nativa
- ✅ Icono en pantalla de inicio
- ✅ Funciona offline (cache)
- ✅ Sin App Store

**Implementación:**
```json
// public/manifest.json

{
  "name": "Monitor Anvic",
  "short_name": "Monitor",
  "description": "Sistema de Monitoreo Control de Accesos",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#1e1e1e",
  "theme_color": "#00d9ff",
  "icons": [
    {
      "src": "/logo192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/logo512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

**Resultado:** 
En tu móvil conectado a WiFi corporativa:
1. Abres `http://192.168.1.100`
2. Browser te ofrece "Agregar a pantalla de inicio"
3. Tienes icono como si fuera app nativa

---

**📦 Resumen Fase 4:**
- ✅ API REST con FastAPI (backend)
- ✅ Dashboard web con React (frontend)
- ✅ Gráficos interactivos en web
- ✅ Acceso desde cualquier PC/tablet en LAN
- ✅ PWA para móviles

**Tiempo total:** 4-5 semanas

---

## 📊 Matriz de Priorización Final

| # | Mejora | Impacto | Complejidad | Inversión | Tiempo | Prioridad |
|---|--------|---------|-------------|-----------|--------|-----------|
| 1 | **🎨 Sistema de Pestañas** | 🔴 Alto | 🟢 Baja | $0 | 2-3h | 🥇 **1** |
| 2 | **📈 Gráfico Latencia** | 🔴 Alto | 🟡 Media | $0 | 3-4h | 🥇 **2** |
| 3 | **🎯 Gauges Uptime** | 🔴 Alto | 🟡 Media | $0 | 2-3h | 🥇 **3** |
| 4 | **🎯 Servidor 24/7 (RPi)** | 🔴 **CRÍTICO** | 🟢 Baja | $120 | 1 día | 🥇 **4** |
| 5 | **📱 Bot Telegram** | 🔴 **CRÍTICO** | 🟡 Media | $0 | 2-3h | 🥇 **5** |
| 6 | **🗄️ SQLite Migración** | 🔴 Alto | 🟡 Media | $0 | 1 sem | 🥈 **6** |
| 7 | **🟩 Heatmap Disponibilidad** | 🟡 Medio | 🟡 Media | $0 | 3-4h | 🥈 **7** |
| 8 | **💾 Backup Automático** | 🔴 Alto | 🟢 Baja | $0 | 1-2h | 🥈 **8** |
| 9 | **📋 Tabla Eventos** | 🟡 Medio | 🟢 Baja | $0 | 1-2h | 🥈 **9** |
| 10 | **📊 Reportes Automáticos** | 🟡 Medio | 🟡 Media | $0 | 1 sem | 🥉 **10** |
| 11 | **🌐 API FastAPI** | 🟡 Medio | 🔴 Alta | $0 | 2 sem | 🥉 **11** |
| 12 | **⚛️ Dashboard React** | 🟡 Medio | 🔴 Alta | $0 | 3-4 sem | 🥉 **12** |
| 13 | **📱 PWA** | 🟢 Bajo | 🟢 Baja | $0 | 1-2h | ⏸️ **Futuro** |

---

## 💰 Inversión Total

```
Hardware:
├─ Raspberry Pi 5 (4GB)        $80
├─ Case + ventilación           $15
├─ MicroSD 64GB                 $12
├─ Fuente 5V 3A                 $12
└─ Cable Ethernet largo         $10
                              ─────
                              $129

Software:                       $0

Electricidad (año 1):          $6.5

TOTAL AÑO 1:                 ~$135
```

**ROI:** Una sola falla detectada fuera de horario paga todo el sistema.

---

## ⏱️ Timeline Completo

```
┌─ FASE 1 (Sem 1-3): Gráficos Desktop ─────────────────────┐
│  ✅ Pestañas + gráficos tipo Grafana                      │
│  Resultado: UX profesional, métricas visuales             │
└───────────────────────────────────────────────────────────┘

┌─ FASE 2 (Sem 4-6): Servidor 24/7 ────────────────────────┐
│  ✅ Raspberry Pi + Telegram + Modo headless               │
│  Resultado: Monitoreo continuo, alertas siempre           │
└───────────────────────────────────────────────────────────┘

┌─ FASE 3 (Sem 7-9): Base de Datos ────────────────────────┐
│  ✅ SQLite + Backups + Reportes automáticos               │
│  Resultado: Historial completo, evidencia para proveedor  │
└───────────────────────────────────────────────────────────┘

┌─ FASE 4 (Sem 10-14): Dashboard Web ──────────────────────┐
│  ✅ FastAPI + React + PWA                                 │
│  Resultado: Acceso desde cualquier PC en red              │
└───────────────────────────────────────────────────────────┘
```

**Total: 12-14 semanas para sistema completo**

---

## 🎯 Quick Wins (Empezar Mañana)

### **Sprint 0 (Esta Semana)**
1. [ ] Comprar Raspberry Pi + accesorios (~$130)
2. [ ] Crear bot de Telegram con @BotFather (10 min)
3. [ ] Instalar matplotlib: `pip install matplotlib` (5 min)

### **Sprint 1 (Próxima Semana)**
1. [ ] Implementar sistema de pestañas (2-3h)
2. [ ] Gráfico de latencia básico (3-4h)
3. [ ] Gauges de uptime (2-3h)

**Resultado Semana 1:** App con visualizaciones tipo Grafana ✅

---

## ✅ Checklist General

### **Desktop App (Actual)**
- [x] Tarjetas de monitoreo
- [x] Panel lateral de control
- [x] Alertas sonoras
- [x] Logs automáticos
- [ ] Sistema de pestañas
- [ ] Gráficos tipo Grafana
- [ ] Heatmap de disponibilidad
- [ ] Captura de métricas históricas
- [x] **Bot de Telegram (Alertas)**
- [x] **Branding Centralizado**

### **Servidor 24/7 (Futuro)**
- [ ] Raspberry Pi comprado y configurado
- [ ] Servicio systemd auto-start
- [ ] Modo headless implementado
- [ ] Bot de Telegram funcionando
- [ ] IP estática configurada
- [ ] Monitoreo 24/7 activo

### **Base de Datos**
- [ ] SQLite schema creado
- [ ] Migración de JSON a DB
- [ ] Backups automáticos
- [ ] Consultas SQL para gráficos

### **Dashboard Web**
- [ ] Backend FastAPI corriendo
- [ ] Frontend React deployado
- [ ] Acceso desde LAN funcionando
- [ ] PWA instalable

---

## 🎓 Conclusión

Este plan transforma tu sistema de monitoreo de una herramienta básica a una **plataforma enterprise-grade** adaptada perfectamente a tu contexto:

### **Ventajas de Tu Arquitectura:**
✅ **Seguridad:** Todo en red local (cumple políticas)  
✅ **Realismo:** Solo propone lo viable (monitoreo black-box)  
✅ **Progresivo:** Fases independientes, valor incremental  
✅ **Económico:** Inversión total ~$135 USD  
✅ **Profesional:** Gráficos tipo Grafana, reportes automáticos  

### **Tu Valor Agregado:**
🎯 Detección temprana de caídas (evidencia al proveedor)  
🎯 SLA tracking confiable  
🎯 Alertas 24/7 (Telegram)  
🎯 Reportes automáticos profesionales  

---

**¿Listo para empezar?** 🚀

---

*Sistema de Monitoreo Control de Accesos - Anvic*  
*Plan Definitivo v2.0 - Generado: 14/01/2026*  
*Adaptado al contexto: Red local, PC personal → Servidor 24/7, Equipos subcontratados*
