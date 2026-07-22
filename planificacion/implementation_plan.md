# Plan de Implementación: Módulos OSINT en Español + Semáforo de Criticidad

Integración de 4 nuevos módulos de inteligencia avanzada y un **Semáforo Táctico de Criticidad** (LEDs brillantes con clasificación de riesgo) en **Argos Guard Enterprise**.

---

## 🚦 Semáforo de Criticidad Táctica (Indicador Visual)

Clasificación dinámica del nivel de riesgo en los resultados de cada consulta OSINT utilizando el indicador de estado circular táctico (glow de color):

- 🟢 **Bajo / Seguro (`#2aa198` Verde Menta):**
  - Sin brechas encontradas, puntaje de abuso 0%, sin puertos de riesgo ni vulnerabilidades conocidas.
- 🟡 **Moderado / Advertencia (`#b58900` Amarillo Ámbar):**
  - 1 a 2 brechas leves, puntaje de riesgo de IP entre 1% y 49%, puertos expuestos sensibles (RDP/SSH), SSL próximo a vencer (<30 días).
- 🔴 **Crítico / Alto Riesgo (`#dc322f` Rojo Alerta):**
  - Brechas masivas de credenciales expuestas, IP marcada como servidor malicioso/botnet (Abuse Score >= 50%), vulnerabilidades graves (CVEs activos) o SSL expirado.

---

## 🏗️ Módulos a Integrar (Nombres en Español)

1. **🔍 Fugas de Datos & Filtraciones (`/api/v1/osint/breach`):**
   - Mapeo de datos expuestos: `Nombre de la Filtración`, `Dominio`, `Fecha de Exposición`, `Datos Comprometidos`, `Descripción del Incidente`.
2. **🛡️ Reputación de IP & Amenazas (`/api/v1/osint/threat`):**
   - Mapeo de datos: `Puntaje de Riesgo`, `Reportes de Abuso`, `Categorías de Ataque`, `Es Servidor de Malware`, `Última Actividad Sospechosa`.
3. **🌐 Infraestructura Expuesta (`/api/v1/osint/shodan`):**
   - Mapeo de datos: `Puertos Expuestos`, `Servidores Web/SSH`, `Servicios Detectados`, `Vulnerabilidades Conocidas (CVEs)`, `Sistema Operativo`.
4. **📜 Registro WHOIS de Dominios (`/api/v1/osint/whois`):**
   - Mapeo de datos: `Registrador del Dominio`, `Titular / Propietario`, `Fecha de Creación`, `Fecha de Expiración`, `Servidores DNS (NS)`, `Estado del Dominio`.

---

## Proposed Changes

### Backend (FastAPI / Python)

#### [MODIFY] [osint_service.py](file:///e:/ProyectoMonitoreoMod_V2/backend/app/application/osint_service.py)
- Añadir cálculo automático de `risk_level` (`LOW`, `MEDIUM`, `HIGH`) en las respuestas `OSINTResponse` de todos los módulos.
- Implementar los 4 nuevos métodos con normalización en español: `analyze_breach()`, `analyze_ip_reputation()`, `analyze_shodan_host()`, `get_whois_info()`.

#### [MODIFY] [api.py](file:///e:/ProyectoMonitoreoMod_V2/backend/app/presentation/api.py)
- Registrar las 4 nuevas rutas API y habilitar claves de configuración `abuseipdb_api_key`, `shodan_api_key` y `hibp_api_key` en `SYSTEM_CONFIG_KEYS`.

---

### Frontend (React / Next.js)

#### [MODIFY] [IntelPanel.tsx](file:///e:/ProyectoMonitoreoMod_V2/frontend/src/components/IntelPanel.tsx)
- Renderizar la cabecera con el **LED Semáforo Circuito (Glow Rojo / Amarillo / Verde)** según el nivel de criticidad.
- Agregar las 4 nuevas pestañas con nombres en español.

#### [MODIFY] [ConfigPanel.tsx](file:///e:/ProyectoMonitoreoMod_V2/frontend/src/components/ConfigPanel.tsx)
- Añadir campos de configuración para las claves de API de inteligencia OSINT.

---

## Plan de Verificación

1. **Verificación Visual de Semáforo:**
   - Validar que el indicador circular cambie dinámicamente entre **🟢 Verde**, **🟡 Amarillo** y **🔴 Rojo** dependiendo del riesgo detectado.
2. **Pruebas de Integración y Traducción:**
   - Confirmar respuestas 100% redactadas en español.
3. **Compilación de Producción:**
   - Ejecutar `./build.ps1` y `./pack_and_sign.ps1` para generar la versión v3.6.4.
