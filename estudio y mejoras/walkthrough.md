# Walkthrough: Mejoras del Sistema y Control de Accesos Basado en Roles (RBAC)

Este documento detalla todas las modificaciones, integraciones y pruebas realizadas en **Argos Guard Enterprise v4.0.0** para el cumplimiento de las restricciones operacionales y el rediseño del sistema.

---

## 1. Cambios de Base de Datos y RBAC Duras en el Backend
- Se extendió el modelo `UserProfile` en [security/models.py](file:///E:/ProyectoMonitoreoMod_V2/backend_v4/apps/security/models.py) agregando el campo `created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='created_profiles')`.
- Se generaron y aplicaron las migraciones de base de datos exitosamente en SQLite.
- Se implementó el middleware centralizado [RoleAccessMiddleware](file:///E:/ProyectoMonitoreoMod_V2/backend_v4/apps/security/middleware.py#L44-133) que intercepta todas las peticiones a nivel HTTP para hacer cumplir de manera estricta las reglas de negocio de los tres roles:
  - **Super Administrador (`super_admin`):** Acceso total y sin restricciones. Puede borrar cualquier cuenta (incluyendo administradores y otros super admins) sin importar quién las haya creado, controlando de forma tolerante la falta de perfiles en base de datos.
  - **Administrador (`admin`):**
    - SÍ puede crear usuarios únicamente del rol **Operador**.
    - SÍ puede eliminar únicamente usuarios operadores que **él mismo haya creado**.
    - NO puede eliminar equipos de red (`remove_node`), cámaras (`remove_camera`), ni descargar respaldos de base de datos (`backup_sqlite`).
    - NO puede modificar configuraciones globales del sistema (Telegram, API Keys, SLA, Webhooks, Parámetros).
  - **Operador (`operator`):**
    - Solo lectura.
    - NO puede agregar ni eliminar nodos ni cámaras.
    - En la pestaña OSINT, **únicamente** se le permite consultar **RUT** y **PPU**. El resto de módulos de red y geografía/clima están bloqueados.

- **Refresco Reactivo de la Tabla de Usuarios (HTMX):**
  - Se configuró el trigger `refreshUserTable` en el backend para forzar de forma asíncrona la recarga en caliente de la tabla en pantalla tan pronto como un usuario es registrado o eliminado exitosamente por el superadmin/admin. El contenedor principal en `user_management.html` escucha este evento en el `body`, evitando la necesidad de refrescar la pantalla manualmente.

---

## 2. Rediseño del Frontend y Estado Apagado (Disabled) Comercial
Con el fin de mantener un look corporativo comercial y no alterar negativamente la interfaz del usuario tirando errores explícitos, las opciones restringidas no se ocultan, sino que se muestran en **estado deshabilitado (grises/apagadas)**:
- **Navbar (`base.html`)**: Las pestañas "Mapa Táctico" y "Configuración" aparecen atenuadas al 30% de opacidad con cursor no-permitido e interacciones bloqueadas para Operadores.
- **Pie de página (`base.html`)**: Se inyectó de forma centrada el rol de la sesión actual: `SESIÓN: SUPER ADMINISTRADOR` / `ADMINISTRADOR` / `OPERADOR` en negritas con brillo cian cyberpunk.
- **Sidebar de Monitoreo (`dashboard.html`)**: Se atenuó por completo para Operadores. La opción "Eliminar Nodo" se muestra gris y deshabilitada para Administradores.
- **Sidebar de Cámaras (`video_surveillance.html`)**: Bloqueado y atenuado para Operadores. Formulario de eliminación bloqueado para Administradores.
- **OSINT Panel (`intel_panel.html`)**: Los módulos de Red e Inteligencia de Amenazas se muestran con un 35% de opacidad y campos inhabilitados para Operadores.
- **Gestión de Usuarios (`user_management.html`)**: Las sub-pestañas globales (Notificaciones, Webhooks, SLA, Parámetros) se muestran grises y no cliqueables para Administradores. Las opciones de rol superior en la creación se desactivaron. En la tabla, los botones "🗑 Eliminar" de usuarios ajenos se ven inhabilitados.

---

## 3. Rediseño Profesional del Reporte PDF (4 Páginas)
Se reconstruyó la lógica de `generate_pdf_report()` en [monitoring/views.py](file:///E:/ProyectoMonitoreoMod_V2/backend_v4/apps/monitoring/views.py#L315-625) para ajustarse exactamente al formato del archivo de referencia:
- **Página 1: Resumen Gerencial y Tabla OSINT:** Cajas de KPIs de Activos, Equipos Online, Cámaras y Uptime Global. Tabla OSINT con hosts e ISPs.
- **Página 2: Nivel Técnico y Telemetría:** KPI de latencia promedio global y caídas. Tabla detallada de telemetría de activos y tabla de cámaras IP.
- **Página 3: Anexo de Analítica Visual:** Simulación vectorial de curvas de latencia y gráficos de barras de disponibilidad.
- **Página 4: Notas de Ciberseguridad y Cierre:** Disclaimer formal y espacio para sello digital de integridad.

---

## 4. Estabilidad y Limpieza de Sesión
- Se implementó la purga automática de cookies y archivos temporales de QWebEngine en [run_kiosk.py](file:///E:/ProyectoMonitoreoMod_V2/backend_v4/run_kiosk.py) y de la tabla `Session` de Django en hilos secundarios seguros.
- Scraping con Selenium 4 + Stealth integrado y libre de WMIC inestable.
- **Canal de Alertas de Telegram Validado:** Se ejecutó con éxito un script de prueba interactivo (`test_telegram.py`) inyectando las credenciales formales del Bot de Telegram y Chat ID provistos. El mensaje de prueba cyberpunk (`ID 153`) fue entregado de manera instantánea y síncrona en el canal de soporte, validando la salida a internet y el bot.

---

## 5. Pruebas y Diagnóstico Operacional
- Se configuró el arranque condicional del demonio en `apps/monitoring/apps.py` para no interferir en las llamadas de `pytest`, solucionando los bloqueos accidentales de base de datos en testing.
- **Motor de Scraping OSINT Robusto (BeautifulSoup + Requests):**
  - Se eliminó Selenium y el Webdriver para evitar que las firmas de automatización de Chromium provoquen bloqueos del WAF Sucuri y el bypass de Cloudflare.
  - Se reescribieron los scrapers de RUT y PPU en [services.py](file:///E:/ProyectoMonitoreoMod_V2/backend_v4/apps/osint/services.py) para realizar peticiones HTTP POST directas simulando cabeceras ordinarias de navegador Windows y parseando las tablas HTML resultantes con `BeautifulSoup`.
  - Las consultas ahora se procesan de forma inmediata (en menos de 500 ms) sin consumo de RAM por navegadores en segundo plano.
  - La suite de pytest pasó de inmediato con éxito absoluto en 24 tests.
  - **Desplazamiento Dinámico y Scrollbar Cyberpunk:**
    - Se habilitó la regla `overflow: auto;` en los contenedores parciales de resultados de OSINT y escaneos de red para permitir scroll vertical y horizontal en tablas anchas.
    - Se aplicó una hoja de estilos de barra de scroll personalizada (`::-webkit-scrollbar`) en [argos_theme.css](file:///E:/ProyectoMonitoreoMod_V2/backend_v4/static/css/argos_theme.css) con un riel oscuro translúcido y deslizador cian brillante.
  - **Pruebas End-to-End (E2E) de Validación Visual:**
    - Se ejecutó un subagente de navegación Chrome DevTools MCP para verificar el flujo completo de Login con el usuario `BetoDev` y la suite de OSINT.
    - Se validó la carga de datos para PPU `tycc70` y RUT `16691169-9`.
    - Se comprobó la interactividad del scroll en el panel al reducir el tamaño de la ventana (`400px` de altura), respondiendo de forma adaptativa y permitiendo el desplazamiento de la información oculta sin cortes de pantalla.
  - **Arranque Recomendado en Windows:** Ejecutar el servidor usando el entorno virtual explícitamente:
    `.\.venv\Scripts\python.exe manage.py runserver`
    o bien activar el entorno antes:
    `.\.venv\Scripts\Activate.ps1; python manage.py runserver`

---

## 6. APIs Públicas y Conexión de Fallbacks Reales de OSINT (Sin Mocks)
Para garantizar que la suite OSINT sea operativa de inmediato ("out of the box") sin requerir configuraciones forzadas de API keys de pago, se implementó una arquitectura de fallbacks multi-capa de red 100% verídicos y libres de simulación (mocks):
- **Geolocalización IP (`query_ipgeo`):** Se securizó la consulta pasándola a **HTTPS** en `ip-api.com` para evadir bloqueos de proveedores. Adicionalmente, se encadenaron resolvedores redundantes en tiempo real (`ipwhois.app` e `ipapi.co`) con User-Agents de navegador legítimos para garantizar la geolocalización frente a caídas o caídas de conectividad.
- **Fugas de Datos (`query_fugas`):** Si no hay clave de HIBP, se consulta la API real de **EmailRep.io**. Si esta arroja tasa de límite (429), se ejecuta una auditoría de DNS real para verificar y listar los servidores MX del dominio del correo en lugar de inyectar datos ficticios.
- **Reputación IP (`query_reputacion`):** Se enlazó a un análisis de reputación real basado en el tipo de operador de la IP (detectando si es un Datacenter/Proxy malicioso como DigitalOcean, OVH, AWS, etc.) combinado con un chequeo de listas de spam real (DNSBL Spamhaus).
- **Infraestructura de Puertos (`query_infra`):** En ausencia de Shodan, se recurre a la API pública de **HackerTarget Nmap**. Si esta falla o da timeout, se ejecuta un escaneo TCP socket nativo local a los puertos críticos en paralelo, devolviendo puertos verdaderamente abiertos en tiempo real.
- **WHOIS (`query_whois`):** Se realiza el intento nativo, fallback a HackerTarget WHOIS real y, si el TLD no es soportado, se resuelve de forma real los Name Servers (NS) del dominio por DNS para generar la ficha técnica estructural del host.

---

## 7. Preparación de Producción y Cierre Final (2026-07-23)

Se completaron todas las tareas de preparación para empaquetado e instalación desatendida en equipos de producción limpios (primer uso virgen):

1. **📹 Video Vigilancia Multi-Protocolo Real ([video_surveillance.html](file:///E:/ProyectoMonitoreoMod_V2/backend_v4/templates/monitoring/partials/video_surveillance.html))**:
   - HTTP / MJPEG renderiza preview nativo en vivo mediante `<img>`.
   - HLS renderiza reproducción de video nativa con `<video>`.
   - RTSP / RTMP presenta interfaz táctica con botón de copiado de URL en un clic para VLC/ffplay.
   - Badge animado `⬤ REC`, distintivos por protocolo y atajo de teclado ESC para cerrar modal.

2. **🔔 Anti-Duplicado Telegram ([daemon.py](file:///E:/ProyectoMonitoreoMod_V2/backend_v4/apps/monitoring/daemon.py))**:
   - Incorporado lock a nivel de módulo `_daemon_started` para garantizar que la telemetría inicia exactamente una vez.
   - Eliminadas las notificaciones de caída/recuperación duplicadas.

3. **🔒 Seguridad de Producción ([config/settings.py](file:///E:/ProyectoMonitoreoMod_V2/backend_v4/config/settings.py))**:
   - `DEBUG = False` por defecto. Activable para desarrollo mediante `$env:ARGOS_DEBUG="1"`.
   - Secret Key dinámico configurable por variable de entorno.

4. **⚙ Acceso Nativo Admin Django ([user_management.html](file:///E:/ProyectoMonitoreoMod_V2/backend_v4/templates/security/partials/user_management.html))**:
   - Inyectado botón flotante de rueda dentada `⚙` en la esquina inferior derecha de la pestaña Configuración.
   - Enlace directo a `/admin/` habilitado únicamente para usuarios con rol `super_admin`.

5. **📜 EULA e Instalador Industrial ([installer_v4.iss](file:///E:/ProyectoMonitoreoMod_V2/desktop/installer_v4.iss) & [eula.txt](file:///E:/ProyectoMonitoreoMod_V2/desktop/eula.txt))**:
   - EULA corporativo ampliado con términos legales completos, licencias HWID y derechos de desinstalación.
   - Instalador Inno Setup 7 con AppId GUID, `UninstallDisplayIcon` para Panel de Control de Windows, banner visual `cyberpunk_side.bmp` y eliminación limpia Zero-Trace.

6. **🛠️ Build Script y CI/CD OTA ([build_v4.ps1](file:///E:/ProyectoMonitoreoMod_V2/build_v4.ps1) & [release_ota.yml](file:///E:/ProyectoMonitoreoMod_V2/.github/workflows/release_ota.yml))**:
   - Script `build_v4.ps1` con inyección explícita de todas las dependencias Python (`requests`, `bs4`, `whois`, `selenium_stealth`, `fpdf`, `pandas`, `matplotlib`, `seaborn`) y búsqueda dinámica de la carpeta de PyQt6.
   - Integrado flujo de trabajo de GitHub Actions para publicaciones automatizadas por aire (OTA) al pushear tags `v*.*.*`.


