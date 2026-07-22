# Fases del Proyecto: Argos Guard Enterprise v4.0 (Modular Monolith)

- [x] **Fase 0: Protocolo Cero Residuos & Limpieza Radical**
  - [x] Purga física de `/frontend` (Next.js, `node_modules`, `.next`, `out/`).
  - [x] Eliminación de carpetas `build/`, `dist/`, dumps, logs temporales y scripts obsoletos.
  - [x] Preservación de archivos de gobernanza (`bitacora.md`, `fases.md`, `plan_trabajo.md`) y secretos (`credenciales.txt`).

- [x] **Fase 1: Agente 1 — Backend & Core Architect (Django 5.x Modular Monolith)**
  - [x] Estructura modular estricta (`config/`, `apps/core`, `apps/monitoring`, `apps/osint`, `apps/security`, `apps/licensing`).
  - [x] Capa de persistencia cifrada local con **SQLCipher (AES-256 de grado militar)**.
  - [x] Singleton `PathResolver` para resolución dinámica de rutas Nuitka-aware (`sys.executable`).
  - [x] Motor AsyncIO para probes de red (ICMP/TCP) y health-checks de infraestructura.

- [x] **Fase 2: Agente 2 — OSINT & Automation Engineer**
  - [x] Reconstrucción e integración limpia de la suite OSINT (15 módulos).
  - [x] Scraper de RUT (`nombrerutyfirma.com` con `format_rut_with_dots`).
  - [x] Scraper de PPU (`volanteomaleta.com` / `patentechile.com`).
  - [x] Técnicas anti-oclusión Chromium (`--window-position=-32000,-32000`, `HWND_BOTTOM`), bypass Cloudflare y `dnspython` v2.8.0.

- [x] **Fase 3: Agente 3 — Frontend & UI/UX Master (Django Templates + HTMX + Alpine.js)**
  - [x] Reconstrucción idéntica al prototipo v3.6 (Navbar superior, malla de nodos 5x2, panel de control lateral derecho).
  - [x] Indicador pulsante de estado de red minimalista sin texto sobrante.
  - [x] HTMX para reactividad asíncrona de datos de telemetría y consultas OSINT por pestañas sin recarga.
  - [x] Alpine.js para la gestión de estados visuales locales del HUD táctico, modales y acordeones.
  - [x] Logo e Icono oficial restaurados y vinculados en la barra superior.

- [x] **Fase 4: Agente 4 — Cybersecurity & RedTeam Auditor**
  - [x] Hashing Argon2id (parámetros OWASP), JWT dual-token y RBAC (`super_admin`, `admin`, `operator`, `reader`).
  - [x] Sanitización Pydantic y control riguroso de procesos zombie Chrome/Driver.

- [x] **Fase 5: Agente 5 — DevOps & Packaging Specialist (PyQt6 / Nuitka / Inno Setup)**
  - [x] Contenedor PyQt6 `QWebEngineView` en Kiosk Mode Full-Screen apuntando al servidor Django interno.
  - [x] Script de compilación Nuitka Standalone C++ preparado con DLLs de respaldo Direct3D/OpenGL.
  - [x] Script Inno Setup Enterprise con purga Zero-Trace desatendida al desinstalar.

- [/] **Fase 6: PROTOCOLO OBLIGATORIO DE SUITE DE PRUEBAS EN DESARROLLO**
  - [x] **Pruebas 6.1 (pytest)**: Cobertura 10/10 aprobada en `backend_v4`.
  - [x] **Pruebas 6.2 (k6)**: Script `stress_test.js` preparado para pruebas de carga.
  - [x] **Pruebas 6.3 (Playwright / Chrome DevTools MCP)**: Validación E2E visual de interacción UI/UX aprobada al 100%.
  - [ ] **Pruebas 6.4 (Revisión Activa del Usuario)**: Evaluación en vivo del usuario sobre la aplicación en desarrollo.
  - [ ] **Autorización Expresa del Usuario para Compilar**: Esperar orden directa e inequívoca del usuario.
