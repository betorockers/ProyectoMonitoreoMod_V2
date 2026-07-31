# Plan de Mejoras y Transformación a Marca Blanca - Anvic Network Sentinel

Este documento consolida las tareas pendientes y la hoja de ruta para transformar la aplicación en un producto comercial licenciable (SaaS/On-Premise).

## 🚀 Objetivo 1: Transformación a Marca Blanca (White Label)
Permitir que la aplicación sea revendida o personalizada para diferentes clientes sin modificar el código fuente.

### Tareas:
1.  **Externalización de Recursos de Marca:**
    *   Crear un archivo `branding.json` que contenga:
        *   Nombre de la Aplicación.
        *   Nombre del Desarrollador/Empresa.
        *   URLs de soporte y contacto.
        *   Colores primarios de la interfaz (Tema).
    *   Hacer que `monitor.py` lea estos valores al iniciar.
2.  **Gestión Dinámica de Assets:**
    *   Cargar logos e iconos desde una carpeta externa `custom_assets/` si existen, o usar los default.
3.  **Instalador Genérico:**
    *   Parametrizar el script de Inno Setup (`installer.iss`) para leer el nombre de la app desde un archivo o variable externa durante la compilación.

## 🔑 Objetivo 2: Sistema de Licenciamiento
Implementar un mecanismo de protección para monetizar el software.

### Tareas:
1.  **Generador de Licencias (Admin):**
    *   Crear script para generar claves de producto (Product Keys) basadas en:
        *   Nombre del Cliente.
        *   Fecha de Expiración.
        *   Hardware ID (opcional, para anclar a una PC).
2.  **Validador de Licencias (App):**
    *   Al inicio (`auth_manager.py` o `main.py`), verificar si existe un archivo `license.key`.
    *   Validar firma criptográfica de la licencia.
    *   Si es inválida o expirada, mostrar pantalla de bloqueo solicitando activación.
3.  **Tipos de Licencia y Control:**
    *   **Trial:** 15 días de prueba.
    *   **Perpetua:** Sin vencimiento.
    *   **Suscripción:** Vencimiento anual/mensual.
    *   **Sistema de Llave Simple (Propuesta Beto):** Implementar un validador de "Product Key" al inicio para controlar periodos de validez (ej. 365 días) y bloquear la interfaz al expirar, invitando a la renovación.

## 🛠️ Objetivo 3: Mejoras Técnicas y Estructurales
(Basado en discusiones previas y roadmap general)

### Tareas:
1.  **Base de Datos Robusta:**
    *   Migrar de `metrics_historial.json` a **SQLite**.
    *   Permitir consultas históricas más rápidas y rangos de fecha personalizados.
2.  **Actualizaciones Automáticas (OTA):**
    *   Implementar un chequeo de versión contra un servidor remoto (GitHub Releases o servidor propio).
    *   Descarga y actualización automática del ejecutable.

## 📅 Plan de Trabajo Paso a Paso

1.  **Paso 1:** Crear estructura de `branding.json` y adaptar `monitor.py`.
2.  **Paso 2:** Implementar lógica de carga de assets dinámicos.
3.  **Paso 3:** Diseñar el esquema de licenciamiento (criptografía básica).
4.  **Paso 4:** Implementar pantalla de activación y bloqueo.
5.  **Paso 5:** Pruebas de generación de instaladores "Marca A" y "Marca B".

---
## 💾 Estado del Proyecto (Save Point)
**Última actualización:** Cierre de sesión v2.0
*   **Versión Actual:** v2.0 Stable (Instalador generado y funcional).
*   **Próxima Acción:** Comenzar con el **Objetivo 1 (Marca Blanca)**, específicamente la creación de `branding.json`.
*   **Notas:** El entorno virtual está limpio (Python 3.11) y las credenciales están aseguradas mediante `SetupWindow`.
