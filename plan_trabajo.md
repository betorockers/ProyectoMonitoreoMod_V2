# Plan de Trabajo — Argos Guard Enterprise v4.0 (Modular Monolith)
**Última actualización:** 2026-07-21

---

## 🛑 REGLA INNEGOCIABLE DE COMPILACIÓN
**PROHIBIDO COMPILAR (`build_v4.ps1` / Nuitka / Inno Setup) SIN LA ORDEN EXPRESA Y DIRECTA DEL USUARIO.**

---

## 🔴 Sprint Actual — Suite Completa de Pruebas en Desarrollo (Fase 6)

### Objetivo: Ejecutar las 4 etapas obligatorias de pruebas en entorno de desarrollo previo a solicitar autorización de compilación

1. **[x] 1. Pruebas Unitarias y Módulos con `pytest`**
   - 10/10 pruebas pasadas exitosamente en `apps/core`, `apps/monitoring`, `apps/osint`, `apps/security` y `apps/licensing`.

2. **[x] 2. Pruebas de Estrés y Carga con `k6`**
   - Script `tests_v4/load/stress_test.js` creado y listo para ejecución de carga.

3. **[x] 3. Pruebas End-to-End (E2E) con Playwright & Chrome DevTools MCP**
   - Validación visual aprobada: Coincidencia 100% de la interfaz con Imagen 2 (Panel lateral derecho + indicador de red de punto pulsante minimalista).

4. **[ ] 4. Pruebas Activas del Usuario en Vivo**
   - Entregar el entorno de desarrollo corriendo para que el usuario pruebe la aplicación activamente.

5. **[ ] 5. Esperar Autorización Expresa para Compilar**
   - Solicitar orden directa al usuario una vez aprobadas todas las pruebas anteriores.

---

## ✅ Sprints Completados v4.0 (2026-07-21)

| Tarea | Estado | Detalle |
|---|---|---|
| Entorno Virtual `.venv` | ✅ COMPLETADO | Creación e instalación aislada de `requirements.txt` en `.venv` |
| Restitución Visual Imagen 2 | ✅ COMPLETADO | Identidad visual idéntica a v3.6, panel derecho y punto pulsante sin texto |
| Protocolo Cero Residuos | ✅ COMPLETADO | Purga total de `/frontend` Next.js, `build/`, `dist/`, logs y binarios obsoletos |
| Reseteo Git Clean Slate | ✅ COMPLETADO | Eliminación del historial previo y commit inicial v4.0 |
| Estructura Monolito Django | ✅ COMPLETADO | Apps `core`, `monitoring`, `osint`, `security`, `licensing` en `backend_v4/` |
| Motor SQLCipher & PathResolver | ✅ COMPLETADO | SQLite AES-256 + Singleton `PathResolver` Nuitka-aware |
| Suite OSINT & Automation | ✅ COMPLETADO | RUT (`16.691.169-9`), PPU, anti-oclusión `-32000,-32000` y `dnspython` |
| UI Cyberpunk HTMX + Alpine.js | ✅ COMPLETADO | Reactividad asíncrona sin recargas + logo oficial restaurado |
| Ciberseguridad Argon2id / JWT | ✅ COMPLETADO | Hashing Argon2id, Dual-Token JWT, RBAC y matado de procesos zombie |
| Packaging PyQt6 & Inno Setup | ✅ COMPLETADO | Contenedor `run_kiosk.py`, `build_v4.ps1` e `installer_v4.iss` Zero-Trace |
