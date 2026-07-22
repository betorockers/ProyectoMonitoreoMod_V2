# Habilitación Completa de Módulos OSINT (11 Servicios Adicionales)

El objetivo es encender al 100% la Suite de Inteligencia OSINT del Kiosko Táctico. 
Actualmente operan **PPU, RUT y DNS**. Faltan 11 servicios que reemplazarán el placeholder "PRÓXIMAMENTE" con verdaderas llamadas al backend de Django utilizando HTMX.

## User Review Required
> [!IMPORTANT]
> Revisa este plan de implementación para habilitar todos los módulos OSINT. Si apruebas, instalaré las dependencias, construiré el backend de cada módulo y los conectaré a la interfaz.

## Dependencias a Instalar
Para lograr esta recolección de inteligencia, ejecutaremos comandos de terminal para instalar:
- `pip install python-whois` (Para Registro WHOIS)
- `pip install requests` (Para APIs HTTP como HIBP, AbuseIPDB, ip-api)
- `pip install beautifulsoup4 lxml` (Para raspado pasivo ligero de páginas web)

## Proposed Changes

### 1. Servicios y APIs a Integrar (Backend)
En `apps/osint/services.py` crearemos las siguientes funciones:

- **Geografía y Clima (`query_geografia`)**: Consumirá una API libre de meteorología (Open-Meteo) y geocodificación para retornar clima en tiempo real de una ciudad/comuna de Chile.
- **Fugas de Datos (`query_fugas`)**: Utilizará HaveIBeenPwned (HIBP) o en su defecto `https://api.proxynova.com/` si HIBP exige API Key de pago, buscando brechas asociadas a un email.
- **Reputación IP (`query_reputacion`)**: Utilizará la API de AbuseIPDB (usando la API key guardada en la base de datos de Configuración, o una validación básica si no hay key).
- **Infraestructura (`query_infra`)**: Realizará un escaneo pasivo o consultará Shodan.
- **Registro WHOIS (`query_whois`)**: Utilizará la librería `python-whois` para extraer registrante, fechas de expiración y servidores DNS de un dominio.
- **IP Geo (`query_ipgeo`)**: Consultará `ip-api.com` para geolocalizar IPs (ISP, Lat/Lon, Organización).
- **Analizador Web (`query_web`)**: Extraerá encabezados HTTP (Headers) y tecnologías expuestas (Server, X-Powered-By) de una URL.
- **Puertos (`query_puertos`)**: Implementará un escáner de puertos Python nativo (socket) a los puertos más críticos (21, 22, 80, 443, 3389, 8080) sin depender de Nmap externo.
- **Subdominios (`query_subdominios`)**: Consultará crt.sh (Certificate Transparency) para listar subdominios conocidos asociados a un dominio raíz.
- **Email (`query_email`)**: Verificará registros MX de un dominio y la validez sintáctica.
- **Traceroute (`query_traceroute`)**: Ejecutará el comando de sistema `tracert` (Windows) y parseará los saltos.

### 2. Controladores (Views)
En `apps/osint/views.py`:
- Crear una función para cada módulo (ej. `query_whois_partial(request)`).
- Todas capturarán el parámetro GET/POST, ejecutarán el servicio y retornarán a `osint/partials/result_card.html`.
- Se registrará cada consulta en `OsintQueryLog`.

### 3. Rutas (URLs)
En `apps/osint/urls.py`:
- Mapear cada nueva función (`path('query/whois/', ...)`).

### 4. Interfaz (HTMX)
En `templates/osint/intel_panel.html`:
- Sustituir el bucle `<template x-for="tab in [...]">` por bloques HTML `<div x-show="osintSubTab === 'whois'" x-cloak>` individualizados.
- Cada bloque tendrá su formulario `hx-get` apuntando a su respectivo endpoint, con su propio spinner de carga (`hx-indicator`).

## Verification Plan
1. Ejecutar instalación de dependencias en el entorno virtual.
2. Comprobar que Django inicie correctamente.
3. Testear IP Geo con `8.8.8.8`.
4. Testear WHOIS con `google.com`.
5. Testear Puertos con un dominio local o público.
6. Testear Traceroute.
