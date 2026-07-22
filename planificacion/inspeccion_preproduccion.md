# 🔍 Informe de Inspección Pre-Producción
## Argos Guard Enterprise v3.6.2 — 2026-07-03

---

## Resumen Ejecutivo

> [!IMPORTANT]
> **SISTEMA APTO PARA PRUEBAS Y COMPILACIÓN**
> Se detectaron y corrigieron 2 dependencias faltantes (`argon2-cffi`, `python-jose`).
> La compilación del frontend (`pnpm build`) fue exitosa. El backend inicia y responde correctamente.

---

## ✅ Backend — Estado de Módulos Python

| Módulo | Estado | Versión |
|---|---|---|
| fastapi | ✅ OK | 0.138.0 |
| uvicorn | ✅ OK | 0.49.0 |
| undetected-chromedriver | ✅ OK | 3.5.5 |
| selenium | ✅ OK | 4.45.0 |
| beautifulsoup4 | ✅ OK | 4.15.0 |
| httpx | ✅ OK | 0.28.1 |
| pydantic | ✅ OK | 2.13.4 |
| sqlite3 | ✅ OK | 3.50.4 |
| argon2-cffi | ✅ INSTALADO | 25.1.0 ⚠️ faltaba |
| python-jose | ✅ INSTALADO | 3.5.0 ⚠️ faltaba |
| PyQt6 | ✅ OK | 6.11.0 |
| PyQt6-WebEngine | ✅ OK | 6.11.0 |
| sqlcipher3 | ✅ OK | 0.6.2 |
| slowapi | ✅ OK | 0.1.10 |
| fpdf2 | ✅ OK | 2.8.7 (import como `fpdf`) |
| matplotlib | ✅ OK | 3.11.0 |
| dnspython | ✅ OK | 2.8.0 |
| pyopenssl | ✅ OK | 26.3.0 |

### Imports de la App
| Módulo | Estado |
|---|---|
| app.main | ✅ Importa sin errores |
| app.application.osint_scraper | ✅ OK |
| app.application.osint_service | ✅ OK |

---

## ✅ Base de Datos (SQLCipher AES-256)

**Archivo:** `backend/argos_guard.db`
**Motor:** SQLCipher 3 — AES-256 — Key: `argos_enterprise_master_key_2026`

| Tabla | Columnas | Filas |
|---|---|---|
| targets | id, label, host, port, protocol, latitude, longitude, mac_address, isp, asn, threat_intel, country | 2 |
| events | id, target_id, status, latency_ms, detail, timestamp | 13 |
| users | username, full_name, password_hash, role | 1 |
| config | key, value | 5 |
| audit_logs | id, username, action, status, ip_address, timestamp | 14 |
| bug_reports | id, username, description, status, timestamp | 0 |
| valid_licenses | license_hash, tier | 0 |
| **streams** | **id, label, protocol, endpoint, status** | **✅ Existe** |

---

## ✅ Backend HTTP — Prueba de Arranque

- `/api/v1/system/status` → HTTP 200 ✅ — `{"setup_complete":false, "license_tier":"DEV", ...}`
- `/api/v1/snapshot` → HTTP 200 ✅ — Retorna targets con datos correctos
- `/api/v1/osint/ppu` → HTTP 200 ✅ — Endpoint responde (scraping tarda ~15s)
- `/api/v1/osint/rut` → HTTP 200 ✅ — Endpoint responde
- `/api/v1/streams` → HTTP 200 ✅ — 2 streams en DB

---

## ✅ Frontend — Compilación de Producción

**Resultado de `pnpm build`:**
```
▲ Next.js 16.2.9 (Turbopack)
✓ Compiled successfully in 5.8s
  Running TypeScript ... Finished in 6.5s
✓ Generating static pages (3/3) in 912ms

Route (app)
┌ ○ /
└ ○ /_not-found
○ (Static) prerendered as static content
```

**Archivos generados en `frontend/out/`:**
- `index.html` ✅ (7.7 KB)
- `404.html` ✅
- `icono_argos.ico` ✅
- `alerta.mp3` / `recuperado.mp3` ✅
- CSS y JS bundles ✅
- **Total: 50 archivos, 2.26 MB**

> [!TIP]
> La carpeta `frontend/out/` está lista para ser servida por FastAPI en producción (ya configurado en `main.py`).

---

## ⚠️ Correcciones Aplicadas en Esta Sesión

1. **`requirements.txt` actualizado** — Se agregaron las 2 dependencias que faltaban:
   ```
   argon2-cffi>=25.1.0
   python-jose[cryptography]>=3.5.0
   ```
   Estas dependencias son críticas para el sistema de autenticación JWT + Argon2id.

2. **`requirements_frozen.txt` generado** — Versión exacta de todos los paquetes instalados (snapshot punto de control).

---

## 🔒 Puntos NO Tocados (Congelados para Pruebas)

- `osint_scraper.py` — Sin cambios
- `argos_guard.db` — Sin cambios en schema
- `osint_service.py` — Sin cambios

---

## ⚠️ Advertencias para Compilación Nuitka (Fase 3)

| Ítem | Riesgo | Acción Recomendada |
|---|---|---|
| `undetected_chromedriver` | 🔴 ALTO | Requiere ChromeDriver externo en la carpeta del exe. No se puede compilar inline |
| `sqlcipher3` | 🟡 MEDIO | Requiere DLLs nativas de SQLCipher. Incluir en `--include-data-files` |
| `PyQt6-WebEngine` | 🟡 MEDIO | Los recursos Qt deben copiarse con `--include-qt-plugins` |
| `fpdf2` | 🟢 BAJO | Import correcto es `from fpdf import FPDF` (no `import fpdf2`) |

---

## 📋 Checklist Previo a Pruebas de Usuario

- [x] Backend importa todos los módulos sin errores
- [x] Base de datos cifrada con tabla `streams` presente
- [x] Endpoints HTTP respondiendo correctamente
- [x] Frontend compilado a producción en `frontend/out/`
- [x] `requirements.txt` completo y actualizado
- [x] `osint_scraper.py` congelado con fórmula probada
- [ ] Ejecutar `run_all_dev.ps1` y hacer prueba E2E de OSINT RUT/PPU en la interfaz
- [ ] Verificar Toast notifications sobre la barra inferior
- [ ] Verificar CRUD de cámaras en la vista "Cámaras"
