# 🗺️ Plan Maestro de Implementación: Argos Guard v2.5+

Este documento organiza el desarrollo de las nuevas funcionalidades y capas de seguridad, ordenadas desde la menor a la mayor complejidad técnica.

---

## 🟢 Fase 1: Infraestructura Base y Herramientas Locales (✅ Completado)
**Objetivo:** Establecer la estructura para las nuevas herramientas y permitir el diagnóstico de la propia máquina.

1.  **Crear `network_tools_logic.py`:**
    *   Archivo dedicado para encapsular llamadas a `subprocess` (`ipconfig`, `hostname`, etc.).
    *   Separación limpia de la lógica de UI.

2.  **Interfaz de Usuario (UI) - Pestaña Herramientas:**
    *   Modificar `monitor.py` para añadir la 3ra pestaña "Diagnóstico".
    *   Implementar restricción de visibilidad: Solo visible para `admin` y `super_admin`.

3.  **Módulo A: Información Local:**
    *   Implementar comandos: `hostname`, `getmac`, `ipconfig /all`.
    *   **Reto:** Parsear la salida de texto para mostrarla en tarjetas bonitas (no texto crudo).

4.  **Módulo B: Reparación Rápida:**
    *   Implementar botones: `Liberar IP`, `Renovar IP`, `Flush DNS`.
    *   **Seguridad Básica:** Añadir ventanas de confirmación ("¿Está seguro?") antes de ejecutar.

---

## 🟡 Fase 2: Diagnóstico Remoto Interactivo (✅ Completado)
**Objetivo:** Permitir la investigación de otros equipos en la red con feedback visual en tiempo real.

1.  **Consola Integrada en UI:**
    *   Crear un widget `CTkTextbox` que actúe como terminal de salida para las herramientas.

2.  **Módulo C: Herramientas Remotas:**
    *   **Ping Manual:** Input para IP -> Ejecución -> Mostrar resultado en consola.
    *   **NSLookup:** Consulta de DNS y visualización limpia.

3.  **Visualización de Tracert (Trace Route):**
    *   **Reto Técnico:** Ejecutar `tracert` (que tarda mucho) en un hilo separado para no congelar la app.
    *   Parsear cada línea de salida para ir llenando una tabla (Salto | IP | Latencia) en tiempo real.

---

## 🟠 Fase 3: Auditoría Avanzada y Gestión de Servicios (✅ Completado)
**Objetivo:** Herramientas de poder para administradores, requiriendo manejo cuidadoso de datos y permisos.

1.  **Módulo D: Auditoría de Red:**
    *   **Netstat:** Ejecutar `netstat -an`, parsear la gran cantidad de datos y mostrarlos en una tabla filtrable (Puerto, Estado, IP Remota).
    *   **Tabla ARP:** Visualizar `arp -a` de forma estructurada.

2.  **Gestor de Servicios (Lista Blanca):**
    *   Crear archivo de configuración `services_whitelist.json`.
    *   Implementar UI para ver estado y botones Start/Stop **solo** para esos servicios.
    *   **Seguridad:** Bloquear cualquier intento de gestionar servicios fuera de esta lista.

---

## 🛡️ Fase 4: Seguridad Interna "La Armadura" (Alta Complejidad)
**Objetivo:** Blindar la aplicación contra errores humanos y ataques de inyección.

1.  **Saneamiento de Entradas (Input Sanitization):**
    *   Implementar validadores con Regex en todos los campos de texto (Ping manual, Tracert).
    *   Rechazar caracteres peligrosos (`&`, `|`, `;`, `$`).
    *   Asegurar que `subprocess` siempre use listas de argumentos, nunca strings crudos.

2.  **Auditoría Forense (Logging):**
    *   Modificar `auth_manager.py` o crear `audit_logger.py`.
    *   Instrumentar todas las funciones de `network_tools_logic.py` para que registren cada uso en `auditoria_usuarios.log`.

3.  **Gestión de Secretos:**
    *   Refactorizar `branding.py` para eliminar tokens por defecto.
    *   Asegurar que el Token de Telegram solo viva en la configuración del usuario.

---

## 🔒 Fase 5: Protección de Datos y Distribución (Máxima Complejidad)
**Objetivo:** Proteger los datos en reposo y asegurar la integridad del binario final.

1.  **Cifrado de Configuración:**
    *   Integrar librería `cryptography`.
    *   Crear lógica para cifrar `equipos_guardados.json` al guardar y descifrar al cargar.
    *   Gestionar la clave de cifrado (generada localmente o derivada de credenciales).

2.  **Hardening de Base de Datos:**
    *   Asegurar permisos de archivo estrictos para `argos_guard.db`.
    *   (Opcional) Evaluar migración a SQLCipher si el cliente requiere encriptación de DB.

3.  **Implementar Exportación Segura de Configuración:**
    *   **UI:** Añadir botón "Exportar Configuración Maestra" en el panel de `super_admin`.
    *   **Seguridad:** La acción debe solicitar de nuevo la contraseña del `super_admin` y registrar el evento de forma crítica en el log de auditoría.
    *   **Lógica:** Crear una función que descifre `equipos_guardados.json` y `users.json` en memoria y use `ReportLab` para generar un PDF con formato corporativo (logo, tablas, etc.) que contenga toda la información legible.

4.  **Preparación para Distribución:**
    *   Configurar `pip-audit` en el entorno de desarrollo.
    *   Documentar proceso de compilación seguro con PyInstaller.
    *   (Si aplica) Adquisición y configuración de certificado para Code Signing.

---

## 📅 Resumen de Hitos Revisado

| Hito | Entregable Principal | Nivel de Riesgo |
| :--- | :--- | :--- |
| **Hito 1 (Fase 1)** | Pestaña Herramientas + Info Local | ✅ Completado |
| **Hito 2 (Fase 2)** | Ping/Tracert Visual + Hilos | ✅ Completado |
| **Hito 3 (Fase 3)** | Netstat + Servicios Controlados | ✅ Completado |
| **Hito 4 (Fase 4)** | Validación Inputs + Logs Completos | 🔄 Pendiente (Próximo) |
| **Hito 5 (Fase 5)** | Cifrado de Datos + Exportación Segura + Build Final | 📅 Futuro |