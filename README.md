# 🛡️ Anvic Network Sentinel — v2.2.3

> **Plataforma de supervisión técnica y visual para instalaciones conectadas**  
> Desarrollado por **BetoGraf.inc** | Licencia Pro Perpetua  
> Arquitectura: Python 3.13 + CustomTkinter + Pygame-CE + Selenium

---

## 📋 Tabla de Contenidos

- [Descripción General](#descripción-general)
- [Módulos del Sistema](#módulos-del-sistema)
- [Servicios OSINT](#servicios-osint)
- [Arquitectura de Archivos](#arquitectura-de-archivos)
- [Configuración del Entorno](#configuración-del-entorno)
- [Compilación y Empaquetado v2.2.3](#compilación-y-empaquetado-v222)
- [Firma Digital](#firma-digital)
- [Credenciales por Defecto](#credenciales-por-defecto)
- [Changelog v2.2.3](#changelog-v222)

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

## Compilación y Empaquetado v2.2.3

El proceso de build está completamente automatizado en `compilar_v2.2.3.bat`:

```
PASO 0: Limpieza de BD y datos de usuario (release virgen)
PASO 1: Activar entorno virtual
PASO 2–4: build_pipeline.py
  ├── PASO 1: Transpilación Cython (protege código sensible)
  ├── PASO 2: Backup de .py originales
  ├── PASO 3: PyInstaller → dist/AnvicNetworkSentinel.exe
  ├── PASO 4: Restaurar .py originales
  ├── PASO 5: Inno Setup → Output/Instalador_Anvic_Network_Sentinel_v2.2.3.exe
  ├── PASO 6: Firma digital SHA-256 (signtool.exe + timestamp DigiCert)
  └── PASO 7: Verificación de firma
```

**Ejecutar build:**
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

## Changelog v2.2.3 (Industrial & Commercial Release)

### 🆕 Nuevas Funcionalidades y UI/UX Top Tier
- **Desacople Multi-Monitor de Telemetría**: Botón `⧉ Desacoplar` / `📥 Reacoplar` para proyectar el dashboard de latencia, SLA y mapa de calor de forma independiente y continua en una pantalla secundaria.
- **Gaveta Lateral Colapsable**: Panel de control con botón flecha `◀ / ▶` exclusivo de la pestaña "Operación en Vivo", liberando el 100% de la superficie visual en las demás pestañas.
- **Canvas Hover Tooltips**: Visualización flotante e inteligente de los nombres de los equipos sobre el mapa de monitoreo al pasar el cursor, evitando truncamientos por espacio.
- **Botones OSINT con Indicador Activo**: Resaltado visual en cian `#00b4d8` para el módulo seleccionado.
- **Suite de Pruebas Automatizadas**: 53 tests unitarios y de integración con `pytest` pasando al 100% con 0 errores y 0 warnings.

### 🛡️ Perímetro Blindado y Scrapers Calibrados
- **Scrapers Congelados**: `core/scraper_ppu.py` y `core/scraper_rut.py` mantenidos 100% intactos con su lógica anti-bloqueo y selectores originales.
- **Resolución Standalone OSINT**: Inclusión completa de `bs4`, `soupsieve`, `requests`, `urllib3` y certificados SSL CA de `certifi` en `AnvicNetworkSentinel.spec`, garantizando consultas sin interrupciones en la app compilada.

### ⚡ Rendimiento, Base de Datos y Reportes Ejecutivos
- **Mantenimiento y Purga Automática SQLite (90 días)**: Rutina periódica en `metrics_manager.py` con purga diaria automática de pings mayores a 90 días y ejecución de `PRAGMA optimize;` para mantener la base de datos ligera en operaciones 24/7.
- **Parser Universal de Timestamps ISO**: Implementación de `_parse_timestamp` resiliente a formatos ISO con `'T'` y espacios, garantizando la generación ininterrumpida de reportes ejecutivos en PDF (190 KB).
- **Sincronización Dinámica de Telemetría**: Evento `_on_tab_changed` en `CTkTabview` para refresco inmediato de KPIs y gráficos de latencia.
- **Permisos de Escritura UAC**: Inno Setup 7 configurado con directiva `[Dirs] Name: "{app}"; Permissions: users-modify` para permitir escritura local de BD y configs sin requerir elevación administrativa continua.

### 🔐 Seguridad & Compilación Industrial
- **DPAPI Nativo de Windows (Zero-Dependencies)**: Implementación de cifrado DPAPI mediante `ctypes` (`Crypt32.dll` / `Kernel32.dll`) en `key_manager.py` y `licensing/license_storage.py`, garantizando funcionamiento autónomo out-of-the-box sin requerir paquetes externos en la máquina del cliente.
- **Cython C-Extensions**: 8 módulos centrales (`network_tools_logic`, `auth_manager`, `key_manager`, `secure_config_manager` y todo el paquete `licensing`) compilados a binarios nativos C `.pyd` x64, protegiendo el código contra ingeniería inversa.
- **Modo Comercial Día Cero**: Forzado automático del perfil `commercial.json` (eliminadas las etiquetas `[MODO DESARROLLADOR]` y `Modo Demo`).
- **Firma Authenticode SHA-256**: Doble firma con timestamp RFC 3161 de DigiCert sobre el ejecutable principal y el instalador `Output\ANS_Setup_V2.2.3.exe` (92.4 MB) compilado con Inno Setup 7 en modo Ultra LZMA2.

---

*Anvic Network Sentinel © 2026 BetoGraf.inc — Todos los derechos reservados*
