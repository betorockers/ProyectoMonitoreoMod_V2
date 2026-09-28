# 🚶 Walkthrough Técnico: Anvic Network Sentinel v2.2.3 (Industrial & Comercial)

> **Perfil:** Staff Engineer & Red Team PhD  
> **Destinatario:** betorock  
> **Versión del Sistema:** v2.2.3 (Producción Comercial Día Cero)

---

## 🧭 Introducción

Este documento detalla la arquitectura, el flujo de compilación industrial, los componentes de seguridad y la guía de operación para despliegues de **primer uso día cero** de **Anvic Network Sentinel**.

---

## 🏗️ Arquitectura del Sistema

```
AnvicNetworkMonitorV2.1/
├── main.py                             # Inicializador y despachador de arranque
├── monitor.py                          # Controlador maestro de interfaz, pestañas y eventos
├── build_pipeline.py                   # Pipeline de compilación y firma digital en 7 fases
├── build_cython.py                     # Transpilador C/C++ Cython para módulos clave
├── AnvicNetworkSentinel.spec           # Especificación PyInstaller con recolección de dependencias
├── installer.iss                       # Script de instalación Inno Setup 7 (LZMA2 Ultra64)
├── seriales_validas.txt                # Registro de seriales criptográficas Pro Perpetua
├── build_profiles/
│   ├── commercial.json                 # Perfil comercial de producción día cero
│   └── demo.json                       # Perfil de demostración limitada
├── core/
│   ├── ping_logic.py                   # Motor ICMP asíncrono y sincrónico thread-safe
│   ├── scraper_ppu.py                  # Scraper PPU (congelado / calibración anti-bloqueo)
│   └── scraper_rut.py                  # Scraper RUT (congelado / formateo automático)
├── licensing/
│   ├── license_service.py              # Servicio de validación y ciclo de vida de licencia
│   ├── license_crypto.py               # Verificación de firma Ed25519 / HMAC
│   ├── license_storage.py              # Almacenamiento seguro en registro Windows / archivo
│   └── machine_fingerprint.py          # Huella digital de hardware inmutable
├── ui/
│   ├── views/                          # Vistas principales
│   ├── components/                     # Componentes visuales (Tarjetas, MapCanvas, Tooltips)
│   └── tabs/                           # Pestañas: Monitoreo, Telemetría, CCTV, OSINT, Admin
└── Output/
    └── ANS_Setup_V2.2.3.exe            # Instalador final firmado con Authenticode (92.4 MB)
```

---

## ⚙️ Pipeline de Compilación Industrial

Para generar un nuevo release comercial firmado:

```powershell
.\monitorEnv\Scripts\python.exe build_pipeline.py
```

### Fases del Pipeline:
1. **Paso 0 — Configuración Comercial Día Cero:** Copia obligatoria de `build_profiles/commercial.json` sobre `build_profile.json` eliminando cualquier rastro de modo dev o demo.
2. **Paso 1 — Transpilación Cython:** Compilación de 8 módulos a extensiones nativas C (`.pyd` x64):
   - `network_tools_logic`, `auth_manager`, `key_manager`, `secure_config_manager`
   - `licensing.license_service`, `licensing.license_crypto`, `licensing.license_storage`, `licensing.machine_fingerprint`
3. **Paso 2 — Aislamiento de Código Fuente:** Renombrado preventivo a `.py.bak`.
4. **Paso 3 — Empaquetado PyInstaller:** Construcción limpia de `dist\AnvicNetworkSentinel\` con recolección completa (`collect_all`) y dependencias explícitas:
   - `win32crypt` y `pywintypes` (más capa de fallback nativo `ctypes` DPAPI con `Crypt32.dll`)
   - `bs4` (BeautifulSoup4 HTML parser)
   - `soupsieve` (Selectores CSS)
   - `requests` y `urllib3`
   - `certifi` (Certificados CA raíz `cacert.pem` para SSL/TLS nativo)
5. **Paso 4 — Restauración:** Restauración automática de los archivos `.py` de desarrollo.
6. **Paso 5 — Firma Digital Authenticode:** Firma de `dist\AnvicNetworkSentinel\AnvicNetworkSentinel.exe` con certificado SHA-256 y timestamp RFC 3161 de DigiCert.
7. **Paso 6 — Compilación con Inno Setup 7:** Generación del setup con directiva de permisos `users-modify` en `{app}` y compresión Ultra LZMA2.
8. **Paso 7 — Firma del Instalador Final:** Firma de `Output\ANS_Setup_V2.2.3.exe` y verificación criptográfica.

---

## 🚀 Guía de Primer Uso (Día Cero)

1. **Instalación:**
   - Ejecutar [`Output\ANS_Setup_V2.2.3.exe`](file:///e:/AnvicNetworkMonitorV2.1/Output/ANS_Setup_V2.2.3.exe).
   - Opcionalmente ingresar el serial en el asistente o durante el primer inicio.
2. **Activación de Licencia:**
   - Utilizar cualquiera de los seriales Pro Perpetua de [`seriales_validas.txt`](file:///e:/AnvicNetworkMonitorV2.1/seriales_validas.txt).
   - La ventana de activación vincula la firma digital a la máquina y valida la vigencia.
3. **Creación del Super Administrador:**
   - La ventana de bienvenida `SetupWindow` solicitará nombre de usuario, nombre completo y contraseña robusta.
4. **Operación en Vivo:**
   - Los nodos iniciales se precargan y comienzan a emitir pings de inmediato.
   - Para ocultar o mostrar el panel de control lateral, pulsar la flecha `◀ / ▶`.
5. **Telemetría y Rendimiento:**
   - Cambiar a la pestaña "Telemetría": los gráficos de latencia, mapa de calor y gauges se dibujan de inmediato.
   - Para monitoreo en una segunda pantalla física, pulsar el botón `⧉ Desacoplar`. Para devolver la vista a la ventana principal, pulsar `📥 Reacoplar`.
6. **Consultas OSINT:**
   - Seleccionar PPU o RUT, ingresar la patente/RUT y consultar. Las dependencias SSL y de parsing embebidas operan de forma autónoma sin depender de Python instalado en el equipo del cliente.
7. **Generación de Reportes Ejecutivos PDF:**
   - En la pestaña Historial o desde el menú superior, presionar "Generar Reporte PDF".
   - El sistema procesa las métricas de telemetría mediante el parser universal ISO y compila un reporte corporativo de alta calidad con SLA, latencias p95 y matriz de disponibilidad.
8. **Mantenimiento Autónomo 24/7:**
   - La base de datos SQLite purga automáticamente registros con antigüedad mayor a 90 días en cada ciclo diario y optimiza sus índices mediante `PRAGMA optimize;`.

---

## 🧪 Validación y Pruebas Automatizadas

Para re-verificar la integridad completa de la suite:

```powershell
.\monitorEnv\Scripts\python.exe -m pytest tests/ -v
```

**Resultado Actual:** `53 passed in 16.74s (0 errors, 0 warnings)`.
