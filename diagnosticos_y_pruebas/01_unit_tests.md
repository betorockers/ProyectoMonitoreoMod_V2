# Reporte de Pruebas Unitarias - OSINT Services

**Fecha:** 2026-07-22
**Módulo:** `apps/osint/services.py`
**Herramienta:** `pytest`

## Resumen Ejecutivo
Se ejecutaron 14 pruebas unitarias para validar los 11 módulos OSINT y 3 módulos base utilizando datos de prueba y credenciales entregadas por el usuario.

## Casos de Prueba Ejecutados y Resultados

1. `test_scrape_rut`: **PASSED** - RUT: 16.691.169-9
2. `test_scrape_ppu`: **PASSED** - PPU: TYCC70
3. `test_query_fugas`: **PASSED** - Email: contacto@betograf.cl
4. `test_query_reputacion`: **PASSED**
5. `test_query_infra`: **PASSED** - Target: betograf.cl
6. `test_resolve_dns_records`: **PASSED** - Dominio: betograf.cl
7. `test_query_geografia`: **PASSED**
8. `test_query_whois`: **PASSED** - Dominio: app.meipass.com
9. `test_query_ipgeo`: **PASSED**
10. `test_query_web`: **PASSED** - URL: betograf.cl
11. `test_query_puertos`: **PASSED** - Target: betograf.cl
12. `test_query_subdominios`: **PASSED** - Dominio: betograf.cl
13. `test_query_email`: **PASSED** - Email: controlaccesos@anvic.cl
14. `test_query_traceroute`: **PASSED**

## Advertencias (Warnings)
- `undetected_chromedriver`: Deprecation warnings relacionados a `distutils.Version` y `locale.getdefaultlocale()`. Esto es un issue de compatibilidad de la librería con Python 3.13, pero no afecta la funcionalidad principal.
- `urllib3`: InsecureRequestWarning al consultar HTTPS sin validación estricta de SSL en `test_query_web`. Es un comportamiento esperado en módulos OSINT donde muchos hosts tienen certificados inválidos.

## Conclusión de Fase 1
**ESTADO:** Éxito (100% Passed)
Ninguna falla bloqueante.
