# 🛡️ Anvic Network Sentinel — v2.2.10

> **Plataforma de supervisión técnica y visual para instalaciones conectadas**  
> Desarrollado por **BetoGraf.inc** | Licencia Pro Perpetua  
> Arquitectura: Python 3.13 + CustomTkinter + Pygame-CE + Selenium + ReportLab Fortune 500

---

## 📋 Tabla de Contenidos

- [Descripción General](#descripción-general)
- [Módulos del Sistema](#módulos-del-sistema)
- [Servicios OSINT](#servicios-osint)
- [Arquitectura de Archivos](#arquitectura-de-archivos)
- [Configuración del Entorno](#configuración-del-entorno)
- [Compilación y Despliegue de Parches v2.2.10](#compilación-y-despliegue-de-parches-v2210)
- [Firma Digital](#firma-digital)
- [Credenciales por Defecto](#credenciales-por-defecto)
- [Changelog v2.2.10](#changelog-v2210)

---

## Descripción General

**Anvic Network Sentinel** es una suite de monitoreo de red y seguridad operacional diseñada para instalaciones industriales, empresas de seguridad y entornos CCTV. Permite:

- Monitorear en tiempo real el estado de equipos en red (ping continuo)
- Visualizar cámaras IP y streams RTSP
- Ejecutar consultas OSINT sobre dominios, IPs, vehículos (PPU), personas (RUT) y más
- Generar alertas sonoras y notificaciones Telegram
- Administrar usuarios con autenticación encriptada

---

## Módulos del Sistema

| Pestaña | Descripción |
|---------|------------|
| **Operación en Vivo** | Monitor de ping en tiempo real, alertas sonoras y toast, Telegram |
| **Historial Operacional** | Log de eventos con filtros y exportación |
| **Video Vigilancia** | Panel CCTV con streams RTSP/IP via Selenium/Chrome |
| **Servicios OSINT** | Suite de 15 herramientas de inteligencia de fuentes abiertas |
| **Administración** | Panel de control: equipos, intervalos, configuración |

---

## Servicios OSINT

### Inteligencia Local (Chile)
| Módulo | API | Descripción |
|--------|-----|-------------|
| **PPU** | volanteomaleta.com (scraping) | Consulta vehículo por patente — 8 campos: Patente, Tipo, Marca, Modelo, RUT, Nro. Motor, Año, Propietario |
| **RUT** | rutificador.com (scraping) | Búsqueda de persona por RUT con formato automático |
| **Geografía y Clima** | wttr.in (gratis) | Clima en español: temperatura, humedad, condición |

### Inteligencia de Red y Digital
| Módulo | API | Descripción |
|--------|-----|-------------|
| **WHOIS** | Socket TCP port 43 nativo | Consulta directa a whois.nic.cl, verisign, etc. según TLD |
| **IP Geo** | ipinfo.io (50k req/mes gratis) | Geolocalización de IP: ciudad, región, país, ASN, coordenadas |
| **DNS** | hackertarget.com (libre) | Registros A, MX, NS, TXT |
| **Analizador Web** | hackertarget.com (libre) | Headers HTTP del dominio objetivo |
| **Puertos** | Socket scan local | Escaneo de 17 puertos comunes con socket nativo |
| **Subdominios** | hackertarget.com (libre) | Enumeración de subdominios |
| **Email** | disify.com (libre) | Validación de email: formato, dominio, desechable, DNS |
| **Traceroute** | `tracert` local (OS) | Traza de ruta nativa de Windows |
| **Escáner LAN** | ICMP ping sweep local | Detecta hosts activos en la subred /24 |
| **Reputación IP** | hackertarget.com (libre) | Reverse IP lookup, dominios compartidos |
| **Infraestructura** | hackertarget.com (libre) | ASN / BGP lookup |
| **Fugas de Datos** | leakcheck.io (libre) | Búsqueda de email en brechas de seguridad |

---

## Arquitectura de Archivos

```
AnvicNetworkMonitorV2.1/
├── main.py                        # Punto de entrada principal
├── monitor.py                     # App principal (LoginWindow, App, SetupWindow)
├── build_pipeline.py              # Pipeline de compilación: Cython → PyInstaller → Inno → Firma
├── build_cython.py                # Transpilación Cython de archivos sensibles
├── compilar_v2.2.3.bat            # Script de build con limpieza de BD
├── AnvicNetworkSentinel.spec      # Spec de PyInstaller
├── installer.iss                  # Script Inno Setup con firma Authenticode
│
├── ui/
│   └── tabs/
│       ├── monitor_tab.py         # Pestaña Operación en Vivo
│       ├── history_tab.py         # Historial Operacional
│       ├── cctv_tab.py            # Video Vigilancia (Selenium/Chrome)
│       ├── osint_tab.py           # Suite OSINT completa (15 módulos)
│       └── admin_tab.py           # Panel de Administración
│
├── core/
│   ├── ping_logic.py              # Lógica de ping continuo en threads
│   ├── scraper_ppu.py             # Scraper PPU (8 campos reales)
│   ├── scraper_rut.py             # Scraper RUT
│   └── network_tools_logic.py    # Herramientas de red
│
├── auth/
│   └── auth_manager.py            # Autenticación encriptada
│
├── database/
│   └── key_manager.py             # Gestión de claves y BD SQLite
│
├── licensing/
│   ├── license_service.py         # Servicio de licencias
│   └── license_crypto.py          # Criptografía de licencias
│
├── assets/
│   ├── img/                       # Íconos, logos, bitmaps
│   └── sounds/                    # Archivos de audio para alertas
│
└── Output/                        # Instalador final generado aquí
```

---

## Configuración del Entorno

### Requisitos
- Python 3.13.x
- Windows 10/11 x64
- Chrome v150+ instalado (para módulo CCTV)
- Inno Setup 6.x (para generar instalador)
- Windows SDK 10 (para `signtool.exe`)

### Setup inicial
```powershell
# Crear entorno virtual
python -m venv monitorEnv
.\monitorEnv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar en desarrollo
python main.py
```

---

## Compilación y Despliegue de Parches v2.2.4

El proyecto soporta dos metodologías de empaquetado industrial:

### 1. Parches Diferenciales / Hotfixes (Recomendado para Actualizaciones)
Genera un instalador ligero de actualización (`Output\ANS_Patch_V2.2.4.exe`, ~15 MB) que actualiza la versión instalada sin requerir reinstalación completa y **conservando intactas todas las bases de datos de mediciones, usuarios y configuraciones**:

```cmd
crear_parche.bat
```
o mediante CLI parametrizado:
```cmd
.\monitorEnv\Scripts\python.exe build_patch.py -v 2.2.4 -d "Telemetria dinamica adaptativa por turnos y optimizacion multihilo"
```

### 2. Instalador Completo Día Cero (Nueva Instalación en Equipo Virgen)
Para despliegues limpios en máquinas nuevas sin instalación previa:
```cmd
compilar_v2.2.3.bat
```

> ⚠️ **IMPORTANTE**: Antes del primer build, ejecutar como Admin:  
> `E:\Certificados\crear_certificado_anvic.ps1`

---

## Firma Digital

El proyecto usa **Authenticode SHA-256** con cadena de confianza completa para minimizar las alertas de Windows SmartScreen.

### Arquitectura del certificado
```
Root CA (RSA-4096, SHA-256, 7 años)
  └── Code Signing (RSA-4096, SHA-256, 5 años)
        ├── Firmado en: Cert:\LocalMachine\My
        ├── Root CA en: Cert:\LocalMachine\Root (Trusted Root)
        └── Code Signing en: Cert:\LocalMachine\TrustedPublisher
```

### Scripts en `E:\Certificados\`
| Script | Propósito |
|--------|-----------|
| `crear_certificado_anvic.ps1` | Crea la cadena Root CA → Code Signing e instala en stores |
| `firmar_anvic.ps1` | Firma manual del instalador con reintentos en 4 servidores de timestamp |

### Servidores de Timestamp RFC 3161
1. `http://timestamp.digicert.com` (primario)
2. `http://timestamp.sectigo.com` (fallback)
3. `http://timestamp.globalsign.com` (fallback)
4. `http://tsa.starfieldtech.com` (fallback)

> El timestamp garantiza que la firma siga siendo válida **después** de que expire el certificado.

---

## Credenciales por Defecto

> 🔒 Cambiar inmediatamente en producción.

| Campo | Valor |
|-------|-------|
| Usuario | `BetoDev` |
| Contraseña | `@B3t0R0ck3rs` |

---

## Changelog v2.2.4 (Telemetría Adaptativa & Sistema de Parches)

### 🆕 Telemetría Dinámica Adaptativa (4 Modos en UI)
- **Selector de 4 Modos Operacionales**: Integrado en la barra superior de telemetría:
  - `Semanal (7D x 24h)`
  - `Semanal (7D x Turno)`
  - `Por Equipo (24h)`
  - `Por Equipo (Turno)`
- **Adaptabilidad Total**: Los KPIs de disponibilidad, percentil 95, gráfico de latencia temporal, gauges y heatmap calculan sus métricas respetando estrictamente los horarios del turno configurado.

### ⏰ Configuración de Turnos en Módulo Administrador
- **Selectores de Inicio y Fin**: Dropdowns de `00:00` a `23:00` en la pestaña de Administración.
- **Soporte de Turnos Nocturnos**: Cálculo automático de turnos que cruzan la medianoche (ej. `20:00` a `06:00`).
- **Persistencia Segura**: Guardado cifrado en `equipos_guardados.json.enc` y sincronización reactiva en tiempo real.

### ⚡ Optimización Multihilo y Reducción I/O SQLite (60 FPS)
- **Worker Asíncrono en Background**: Cálculos pesados y consultas SQL extraídos del hilo principal a un hilo daemon (`threading.Thread`).
- **Índices Compuestos SQLite**: `idx_mediciones_ip_ts` e `idx_mediciones_ts`, acelerando agregaciones a < 15ms.
- **Widget Pooling (Zero DOM Thrashing)**: Reutilización en memoria de canvas gauges y filas de tabla, eliminando más de 60 llamadas destructivas `destroy()` por ciclo.
- **Canvas draw_idle()**: Reemplazo de renderizado sincrónico e incremento de autorefresco de 60s a 15s estables.

### 📦 Sistema Industrial de Parches Diferenciales
- **`build_patch.py` / `crear_parche.bat`**: Generación de instaladores de actualización ligeros (`ANS_Patch_V2.2.4.exe`, 15.16 MB) y paquetes desatendidos (`ANS_Patch_V2.2.4_Portable.zip`, 13.20 MB).
- **Garantía Sagrada de Datos**: Cero borrado de bases de datos `anvic_monitor.db`, usuarios ni licencias.
- **Rollback Preventivo**: Copia de seguridad automática con script `rollback.bat` en `{app}\backups\`.
- **Firma Authenticode SHA-256**: Certificado con timestamp RFC 3161 de DigiCert.
- **Suite QA Certificada**: 62 pruebas unitarias pasando al 100% en pytest.

---

*Anvic Network Sentinel © 2026 BetoGraf.inc — Todos los derechos reservados*
