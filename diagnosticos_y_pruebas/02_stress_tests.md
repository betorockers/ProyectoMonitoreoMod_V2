# Reporte de Pruebas de Estrés (`k6`) - OSINT y Mapa Táctico

**Fecha:** 2026-07-22
**Módulo:** Endpoints OSINT y Mapa Táctico (HTMX/Django)
**Herramienta:** `k6`

## Resumen Ejecutivo
Se realizó una prueba de carga simulando hasta 20 usuarios concurrentes interactuando simultáneamente con los endpoints principales del sistema, incluyendo geolocalización, análisis web y la vista del Mapa Táctico.

## Configuración de la Carga (Ramp-up)
- **Subida (Ramp-up):** 0 a 20 Usuarios (VUs) en 5 segundos.
- **Sostenimiento (Plateau):** 20 Usuarios concurrentes por 10 segundos.
- **Bajada (Ramp-down):** 20 a 0 Usuarios en 5 segundos.

## Endpoints Evaluados
1. `GET /osint/geografia/?city=Santiago`
2. `GET /osint/web/?url=betograf.cl`
3. `GET /partial/map/` (Mapa Táctico)

## Resultados y Métricas (Ejecución Final)

- **Total Requests (`http_reqs`):** 213 (aprox. 9.38 req/s)
- **Tasa de Errores (`http_req_failed`):** 0.00% (213 requests exitosos, 0 fallos)
- **Verificaciones (Checks):** 100% (213/213 Pasaron)
  - Geografía 200: OK
  - Web 200: OK
  - Mapa Táctico 200: OK
- **Tiempos de Respuesta (`http_req_duration`):**
  - **Mediana:** 158.9 ms
  - **Promedio:** 1.3 s
  - **p(95):** 4.37 s (Se explica por el throttling y latencia inherente de las consultas OSINT reales que hace el backend).

## Diagnósticos y Resoluciones
- **Falla Inicial:** El script apuntó erróneamente a `/monitoring/tactical_map_partial/` resultando en error 404 (0/69 pasaron).
- **Resolución:** Se corrigió el path hacia `/partial/map/` conforme al enrutador en `config/urls.py` apuntando a `apps.monitoring.urls`. Tras la corrección, se obtuvo un 100% de éxito.

## Conclusión de Fase 2
**ESTADO:** Éxito (100% Passed)
El servidor Django (Modular Monolith) soporta adecuadamente peticiones asíncronas para OSINT y responde consistentemente a las actualizaciones del mapa táctico sin bloqueos a la carga probada.
