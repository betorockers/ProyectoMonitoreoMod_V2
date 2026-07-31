# ⚓ Ancla de Sesión - Anvic Network Sentinel

Este archivo sirve como punto de control (ancla) para iniciar y finalizar cada sesión de desarrollo. Aquí se registran los avances recientes y los pendientes exactos para la siguiente sesión, asegurando continuidad.

---

## 📌 Estado Actual (Cierre de Sesión v2.2.2)

**Versión:** 2.2.2
**Fecha:** 31 de Julio de 2026

### ✅ Completado en la última sesión:
1. **OSINT APIs Fixes:** Se reemplazaron APIs caídas o con rate-limit por soluciones nativas/robustas (WHOIS por socket nativo, Puertos por socket local, Fugas por LeakCheck, Traceroute por CMD local, LAN por ICMP Ping Sweep).
2. **Mejoras UI OSINT:** Los botones de servicios ahora se iluminan en color cian (`#00b4d8`) para indicar claramente qué módulo está activo. Se corrigió el placeholder de la caja de búsqueda para que desaparezca al hacer clic. Los scrollbars ahora son transparentes oscuros, más elegantes.
3. **Scraper PPU Mejorado:** Ahora lee de forma dinámica las 8 columnas completas desde volanteomaleta (Tipo, Marca, Modelo, RUT, Nro. Motor, Año, Propietario).
4. **Independencia de Resultados:** Al cambiar de pestaña OSINT, la información del TreeView y la tabla se actualiza correctamente y es independiente por servicio.
5. **Certificados de Seguridad y SmartScreen:** Se implementaron los scripts PowerShell (`crear_certificado_anvic.ps1` y `firmar_anvic.ps1`) con encriptación RSA-4096 y SHA-256 (Root CA + Code Signing), agregando marca de tiempo DigiCert.
6. **Automatización Build:** `installer.iss` integrado con Inno Setup para autocompilar y `build_pipeline.py` automatiza la firma digital de ambos (el `.exe` y el instalador).
7. **Documentación:** Se generó el `README.md` maestro completo.

### ⏳ Pendientes para la siguiente sesión:
1. **Verificación de la Base de Datos "Virgen":** Validar exhaustivamente tras una instalación en limpio que la base de datos se genera sin registros previos (cero usuarios fantasma, logs vacíos).
2. **Pruebas E2E del módulo CCTV:** Realizar comprobaciones visuales E2E (usando Selenium/Chrome) del panel CCTV con credenciales en los sitios objetivo (anvic.cl, betograf.cl) para corroborar la integración web.
3. **Control de Procesos (Zombies):** Validar en entorno de producción post-instalación que al cerrar la app (`X` o cerrar sesión), todos los subprocesos de Python, Selenium, pingers, etc., se terminan de raíz y no queda nada residente en RAM.
4. **Pruebas de Firma Digital y Despliegue:** Probar ejecutar el instalador en otro equipo de red para confirmar que SmartScreen acepta o permite la instalación al tener el certificado instalado/válido.

---

*Nota para el Agente: Al iniciar una nueva sesión, lee este archivo primero para contextualizar el estado del proyecto.*
