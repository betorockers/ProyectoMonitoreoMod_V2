# DOCUMENTACIÓN MAESTRA — ARGOS GUARD ENTERPRISE V4.0
**Última Sincronización:** 2026-07-21 16:15 UTC-4

---

## 1. Visión General y Filosofía de Diseño
Argos Guard Enterprise v4.0 es una plataforma monolítica modular de alta ciberseguridad, monitoreo táctico de nodos en tiempo real y suite de inteligencia OSINT, empaquetada como una aplicación nativa de escritorio Kiosko en **PyQt6 QWebEngineView** impulsada por un backend **Django 5.x** con base de datos local cifrada **SQLCipher (AES-256)**.

---

## 2. Puntos Clave de la Arquitectura
- **Backend**: Django 5.x (`backend_v4/`) con 5 módulos desacoplados (`core`, `monitoring`, `osint`, `security`, `licensing`).
- **Entorno Virtual**: `.venv` limpio e independiente con `requirements.txt`.
- **UI/UX**: Identidad visual oficial idéntica al prototipo v3.6 (Navegación superior por pestañas, malla de nodos 5x2 en tarjetas HUD cian/oro/rojo, panel de control lateral derecho, punto pulsante de estado de red minimalista y estampa de tiempo inferior).
- **Red Team Security**: Hashing Argon2id (OWASP 64MB/3iter/4hilos), Dual-Token JWT y exterminador desatendido de procesos zombie.
- **Packaging & DevOps**: Compilación Nuitka C++ Standalone ([build_v4.ps1](file:///e:/ProyectoMonitoreoMod_V2/build_v4.ps1)) e Inno Setup 7 ([installer_v4.iss](file:///e:/ProyectoMonitoreoMod_V2/desktop/installer_v4.iss)) con desinstalador Zero-Trace.

---

## 3. Registro de Gobernanza y Archivos Clave
- 📄 [ancla.md](file:///e:/ProyectoMonitoreoMod_V2/ancla.md): Punto de retoma para la siguiente sesión.
- 📁 [estudio y mejoras/implementation_plan.md](file:///e:/ProyectoMonitoreoMod_V2/estudio%20y%20mejoras/implementation_plan.md): Plan técnico de implementación.
- 📁 [estudio y mejoras/walkthrough.md](file:///e:/ProyectoMonitoreoMod_V2/estudio%20y%20mejoras/walkthrough.md): Informe walkthrough con evidencias visuales E2E.
- 📄 [bitacora.md](file:///e:/ProyectoMonitoreoMod_V2/bitacora.md), [fases.md](file:///e:/ProyectoMonitoreoMod_V2/fases.md), [plan_trabajo.md](file:///e:/ProyectoMonitoreoMod_V2/plan_trabajo.md).
