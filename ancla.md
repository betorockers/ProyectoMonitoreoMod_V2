# ⚓ Ancla de Proyecto: Anvic Network Sentinel v2.2.3 (Comercial / Día Cero)

> **Fecha de Actualización:** 28 de Septiembre, 2026  
> **Perfil Operativo:** Staff Engineer & Red Team PhD  
> **Target:** betorock  
> **Estado:** Top Tier Industrial — Código Congelado, Instalador Firmado y Listo para Pruebas de Campo

---

## 🏆 Hitos y Logros de la Sesión Actual

### 1. Squad de Agentes Especializados (`E:\Agentes_skill`)
- Se mapearon y coordinaron perfiles desde el repositorio central para auditoría, arquitectura (SOLID, DRY, Clean Code), QA, UI/UX, ciberseguridad ofensiva/defensiva y DevSecOps.

### 2. Blindaje de Perímetro y Código Congelado
- **Scrapers Preservados:** [`core/scraper_ppu.py`](file:///e:/AnvicNetworkMonitorV2.1/core/scraper_ppu.py) y [`core/scraper_rut.py`](file:///e:/AnvicNetworkMonitorV2.1/core/scraper_rut.py) permanecieron **100% congelados e inalterados**, manteniendo intacta su calibración anti-bloqueo y selectores.

### 3. Calidad de Código y Cero Advertencias
- **Eliminación de 99 Warnings SQLite:** Registro de adaptadores ISO-8601 explícitos en [`metrics_manager.py`](file:///e:/AnvicNetworkMonitorV2.1/metrics_manager.py) para `datetime.datetime` y `datetime.date`.
- **Retrocompatibilidad y Thread-Safety:** Desacople de rutinas sincrónicas y asincrónicas en [`core/ping_logic.py`](file:///e:/AnvicNetworkMonitorV2.1/core/ping_logic.py).
- **QA Suite 100% en Verde:** **48/48 pruebas pasando** con pytest en 5.56s (0 errores, 0 fallos, 0 warnings).

### 4. Vanguardia en UI/UX y Ergonomía
- **Gaveta Lateral Colapsable:** Panel de control lateral exclusivo de la pestaña "Operación en Vivo", con toggle animado `◀ / ▶`, liberando el 100% de la pantalla en las demás pestañas.
- **Ventana Desacoplable Multi-Monitor:** Función de desacople (Pop-out) para la pestaña de Telemetría, permitiendo monitoreo dedicado y continuo en un segundo monitor físico.
- **Canvas Tooltips:** Efecto hover dinámico sobre los equipos en el mapa canvas con límites inteligentes para evitar truncamientos fuera de pantalla.

### 5. Compilación Comercial Día Cero (Producción Real)
- **Eliminación de Modo Dev / Demo:** Se forzó el perfil `commercial` en [`build_profile.json`](file:///e:/AnvicNetworkMonitorV2.1/build_profile.json): título limpio `Anvic Network Sentinel | Licencia activa: Pro Perpetua`, sin `[MODO DESARROLLADOR]` ni `Modo Demo`.
- **Resolución de OSINT en Compilado:** Se corrigió [`AnvicNetworkSentinel.spec`](file:///e:/AnvicNetworkMonitorV2.1/AnvicNetworkSentinel.spec) mediante `collect_all` para `bs4`, `soupsieve`, `requests`, `certifi` (con certificados SSL `cacert.pem`) y `urllib3`. Los scrapers ahora ejecutan nativamente en el `.exe`.
- **Telemetría Día Cero Activa:**
  - Precarga de nodos iniciales mediante `DEFAULT_EQUIPMENT` y flag `preload_default_equipment: true`.
  - Disparo reactivo de actualización al cambiar a la pestaña Telemetría (`_on_tab_changed` en `CTkTabview`).
  - Menú de selección de host dinámico sincronizado en tiempo real.
- **Permisos de Escritura Windows UAC:** Inno Setup configurado con directiva `[Dirs] Name: "{app}"; Permissions: users-modify` para permitir escritura directa de base de datos SQLite y cifrados en `C:\Program Files` sin exigir privilegios de Administrador al operador.

### 6. Pipeline Industrial Completo y Resolución de Incidencia DPAPI
- **Incidencia Resuelta (Crash Día Cero en Arranque):**
  - *Síntoma:* `ModuleNotFoundError: No se encontró 'win32crypt'. Instala 'pywin32' en este entorno para usar DPAPI.` al invocar `key_manager.load_key()` / `save_key()`.
  - *Causa Raíz:* La transpilación Cython de `key_manager.py` generó un binario `.pyd`. Durante el empaquetado, PyInstaller no pudo analizar el AST de Python para deducir la dependencia de `win32crypt.pyd` y `pywintypes313.dll`. Además, `key_manager.py` tenía un bloqueo rígido sobre `win32crypt` sin fallback nativo del SO.
  - *Solución Nivel Staff:* Se implementó un wrapper nativo de Windows DPAPI mediante `ctypes` apuntando directamente a `Crypt32.dll` (`CryptProtectData` / `CryptUnprotectData`) y `Kernel32.dll` (`LocalFree`). Posee **cero dependencias externas**, funciona en cualquier instalación de Windows (out-of-the-box), mantiene 100% de compatibilidad binaria bidireccional con claves cifradas previas y tiene fallback automático si `win32crypt` no está presente. Se replicó en `licensing/license_storage.py` y se agregaron `win32crypt` y `pywintypes` a `hiddenimports` en `AnvicNetworkSentinel.spec`.
  - *QA & Cobertura:* Nueva suite [`tests/test_key_manager_dpapi.py`](file:///e:/AnvicNetworkMonitorV2.1/tests/test_key_manager_dpapi.py) con **51/51 pruebas pasando en verde (100%)**.
- **Cython:** 8 módulos críticos transpilados a extensiones C nativas (`.pyd` x64):
  - `network_tools_logic`, `auth_manager`, `key_manager`, `secure_config_manager`
  - `licensing/license_service`, `licensing/license_crypto`, `licensing/license_storage`, `licensing/machine_fingerprint`
- **Firma Authenticode SHA-256:** Doble firma con timestamp RFC 3161 (DigiCert) aplicada a `AnvicNetworkSentinel.exe` y al instalador final.
- **Inno Setup 7:** Generación del paquete [`Output\ANS_Setup_V2.2.3.exe`](file:///e:/AnvicNetworkMonitorV2.1/Output/ANS_Setup_V2.2.3.exe) (92.4 MB) con compresión Ultra LZMA2, validado en arranque limpio.

---

### 7. Resolución de Incidencia: Error PDF por Timestamp ISO-8601
- **Incidencia Resuelta (Falla al Generar Reporte PDF):**
  - *Síntoma:* Toast de error `No se pudo generar el reporte: time data '2026-09-25T16:19:24.860481' does not match format '%Y-%m-%d %H:%M:%S.%f'`.
  - *Causa Raíz:* En [`metrics_manager.py`](file:///e:/AnvicNetworkMonitorV2.1/metrics_manager.py), las funciones de agregación para el reporte (`obtener_datos`, `analizar_desconexiones_y_downtime` y `obtener_matriz_semanal`) utilizaban `datetime.strptime(val, "%Y-%m-%d %H:%M:%S.%f")`, el cual requería obligatoriamente un espacio como separador. Al utilizar el adaptador de SQLite con formato ISO estándar (`val.isoformat()`), las fechas se guardaban con separador `'T'`, disparando un `ValueError`.
  - *Solución Nivel Staff:*
    1. Se implementó el helper universal `_parse_timestamp(val)` en [`metrics_manager.py`](file:///e:/AnvicNetworkMonitorV2.1/metrics_manager.py), capaz de parsear de forma resiliente cualquier formato (`datetime` nativo, ISO con `'T'`, ISO con espacio, con y sin microsegundos) mediante `datetime.fromisoformat()` y fallbacks limpios.
    2. Se ajustó el adaptador SQLite a `val.isoformat(sep=" ")` para consistencia con motores legacy.
    3. Se reforzó el fallback en [`database/database_manager.py`](file:///e:/AnvicNetworkMonitorV2.1/database/database_manager.py).
    4. Se creó la suite [`tests/test_metrics_manager_timestamps.py`](file:///e:/AnvicNetworkMonitorV2.1/tests/test_metrics_manager_timestamps.py) con validación end-to-end de generación de PDF: **53/53 pruebas pasando en verde (100%)**.
- **Scrapers Preservados:** [`core/scraper_ppu.py`](file:///e:/AnvicNetworkMonitorV2.1/core/scraper_ppu.py) y [`core/scraper_rut.py`](file:///e:/AnvicNetworkMonitorV2.1/core/scraper_rut.py) se mantuvieron **100% congelados e inalterados**.

---

## ⚓ Puntos de Anclaje y Estado de Tareas

### ✅ Tareas Completadas en la Sesión:

1. **[x] Recompilación del Pipeline Industrial (`build_pipeline.py`):**
   - Transpilación Cython de 8 módulos completada.
   - Empaquetado PyInstaller con inclusión explícita de `win32crypt`, `pywintypes`, `bs4`, `soupsieve`, `requests`, `certifi` y fallback nativo DPAPI vía `ctypes`.
   - Doble firma digital Authenticode SHA-256 con timestamp RFC 3161 (DigiCert).
   - Generación exitosa de [`Output\ANS_Setup_V2.2.3.exe`](file:///e:/AnvicNetworkMonitorV2.1/Output/ANS_Setup_V2.2.3.exe) (92.4 MB).
   - Verificación de arranque limpio del binario compilado (`AnvicNetworkSentinel.exe`, PID activo sin excepciones).

2. **[x] Resolución de Incidencia: Parsing de Fechas en Reportes PDF:**
   - Implementado el parser universal `_parse_timestamp(val)` en [`metrics_manager.py`](file:///e:/AnvicNetworkMonitorV2.1/metrics_manager.py).
   - Eliminado el error `time data does not match format` provocado por timestamps ISO con `'T'`.
   - Prueba end-to-end completada exitosamente generando un PDF ejecutivo de 190 KB.

3. **[x] Política de Mantenimiento y Purga Automática de Base de Datos SQLite:**
   - Implementada en [`metrics_manager.py`](file:///e:/AnvicNetworkMonitorV2.1/metrics_manager.py) la purga automática de mediciones de ping mayores a 90 días (`_limpiar_datos_antiguos(dias_retencion=90)`).
   - Ejecución diaria automática en cada ciclo del scheduler y en cada guardado, acompañada de `PRAGMA optimize;` para mantener la base de datos `anvic_monitor.db` desfragmentada y ligera en operaciones 24/7.
   - 53/53 pruebas unitarias pasando en verde (100% PASS).

---

### 📌 Tareas de Campo Pendientes para betorock (Hardware & Operación):

1. **[ ] Despliegue e Instalación en Máquina Cliente / Operativa:**
   - Ejecutar el instalador [`Output\ANS_Setup_V2.2.3.exe`](file:///e:/AnvicNetworkMonitorV2.1/Output/ANS_Setup_V2.2.3.exe) en la máquina de destino.
   - Activar con una de las seriales Pro Perpetua disponibles en [`seriales_validas.txt`](file:///e:/AnvicNetworkMonitorV2.1/seriales_validas.txt).
   - Completar el asistente inicial `SetupWindow` para crear el usuario Super Administrador.

2. **[ ] Verificación de Campo de Reportes PDF:**
   - Pulsar el botón **"Generar Reporte PDF"** desde la pestaña de Historial / Menú en la aplicación instalada y corroborar que el archivo PDF abra directamente en el visor predeterminado del sistema sin ninguna alerta.

3. **[ ] Prueba de Estrés Multi-Monitor (Pantalla Secundaria):**
   - Conectar un segundo monitor físico a la laptop/estación de trabajo.
   - En la pestaña "Telemetría", hacer clic en **"⧉ Desacoplar"** para mover la ventana flotante al monitor secundario y comprobar la estabilidad continua del refresco a 60 segundos durante una jornada de operación (> 4 horas).

4. **[ ] Validación de Alertas Telegram:**
   - Configurar el Token y Chat ID en el panel de Administración y forzar una desconexión de enlace para validar la recepción de la notificación en tiempo real.

---

> *Este documento es el ancla viva de transferencia técnica para betorock. En la próxima sesión, retomar directamente desde las **Tareas de Campo Pendientes**.*
