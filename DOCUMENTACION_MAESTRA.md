# DOCUMENTACIÓN MAESTRA — ARGOS GUARD ENTERPRISE V4.0
**Última Sincronización:** 2026-07-23 18:55 UTC-4
**Estado:** 🟢 **100% FUNCIONAL — PREPARADO PARA PRODUCCIÓN Y COMPILADO PRIMER USO VIRGEN**

---

## 1. Visión General y Filosofía de Diseño
Argos Guard Enterprise v4.0 es una plataforma monolítica modular de alta ciberseguridad, monitoreo táctico de nodos en tiempo real y suite de inteligencia OSINT, empaquetada como una aplicación nativa de escritorio Kiosko en **PyQt6 QWebEngineView** impulsada por un backend **Django 5.x** con base de datos local **SQLite / SQLCipher (AES-256)**.

---

## 2. Puntos Clave de la Arquitectura
- **Backend**: Django 5.x (`backend_v4/`) con 5 módulos desacoplados (`core`, `monitoring`, `osint`, `security`, `licensing`).
- **Entorno Virtual**: `.venv` limpio e independiente con `requirements.txt`.
- **UI/UX**: Identidad visual oficial (6 Tabs principales: Monitoreo Activo, Mapa Táctico, Historial Eventos, Video Vigilancia, OSINT, Configuración). Botón flotante ⚙ en esquina inferior derecha de la Tab Configuración para acceso directo al Panel de Administración Nativo Django (`/admin/`) restringido al rol `super_admin`.
- **Video Vigilancia Multi-Protocolo**: Reproductor real integrado (HTTP/MJPEG en preview live nativo `<img>`, HLS en `<video>`, y RTSP/RTMP con interfaz profesional de copiado de URL para VLC/ffplay).
- **Notificaciones Telegram de Red**: Daemon de telemetría ICMP/TCP con lock global anti-duplicados y despacho asíncrono no bloqueante.
- **Seguridad & Producción**: Hashing Argon2id, Dual-Token JWT, exterminador desatendido de procesos zombie, `DEBUG=False` controlado por variable de entorno `ARGOS_DEBUG`.
- **Descargas Nativas**: Interceptor de descargas PyQt6 WebEngine que redirige automáticamente plantillas JSON, reportes PDF y respaldos SQLite a la carpeta `Descargas` del sistema host Windows.
- **Packaging & DevOps**: Compilación Nuitka C++ Standalone ([build_v4.ps1](file:///e:/ProyectoMonitoreoMod_V2/build_v4.ps1)), Inno Setup 7 ([installer_v4.iss](file:///e:/ProyectoMonitoreoMod_V2/desktop/installer_v4.iss)) con EULA corporativo amplio y desinstalador Zero-Trace, e integración OTA Release vía GitHub Actions (`.github/workflows/release_ota.yml`).

---

## 3. Registro de Gobernanza y Archivos Clave
- 📄 [ancla.md](file:///e:/ProyectoMonitoreoMod_V2/ancla.md): Punto de retoma para la siguiente sesión.
- 📁 [estudio y mejoras/implementation_plan.md](file:///e:/ProyectoMonitoreoMod_V2/estudio%20y%20mejoras/implementation_plan.md): Plan técnico de implementación.
- 📁 [estudio y mejoras/walkthrough.md](file:///e:/ProyectoMonitoreoMod_V2/estudio%20y%20mejoras/walkthrough.md): Informe walkthrough con evidencias visuales E2E.
- 📁 [diagnosticos_y_pruebas/reporte_prod_prep.md](file:///e:/ProyectoMonitoreoMod_V2/diagnosticos_y_pruebas/reporte_prod_prep.md): Reporte de diagnóstico y suite de pruebas.
- 📄 [bitacora.md](file:///e:/ProyectoMonitoreoMod_V2/bitacora.md), [fases.md](file:///e:/ProyectoMonitoreoMod_V2/fases.md), [plan_trabajo.md](file:///e:/ProyectoMonitoreoMod_V2/plan_trabajo.md).

