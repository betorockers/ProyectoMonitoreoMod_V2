# 📚 Documentación Técnica: Anvic Network Sentinel (v2.0 - Distribución Local)

**Anvic Network Sentinel** es una solución avanzada de monitoreo de red local (LAN) diseñada para el control de accesos. Esta versión 2.0 ha sido optimizada para su **distribución masiva** y **operación en horario laboral (09:00 - 17:00)**, eliminando dependencias externas y reforzando la analítica visual.

---

## 1. Arquitectura y Requisitos

### 1.1. Módulos del Sistema
*   **`main.py`:** Punto de entrada de la aplicación.
*   **`monitor.py`:** Núcleo de la interfaz de usuario (CustomTkinter) y orquestación.
*   **`ping_logic.py`:** Motor de red optimizado para ejecución concurrente.
*   **`metrics_manager.py`:** Gestor de persistencia temporal, cálculo de estadísticas y **Log Mensual de Disponibilidad**.
*   **`auth_manager.py`:** Sistema de seguridad local, gestión de roles (RBAC) y **Log de Auditoría**.

### 1.2. Requisitos de Software
*   **Python:** 3.11 o superior.
*   **Permisos:** Ejecutar como **Administrador** (requerido para sockets ICMP y escritura en carpeta de instalación).
*   **Instalación:** Se distribuye mediante un instalador profesional (`.exe`) que gestiona permisos de escritura automáticamente.

---

## 2. Nuevas Funcionalidades (v2.0)

### 2.1. Gestión de Usuarios y Seguridad
*   **Flujo de Contraseñas Ágil:** 
    *   **Admin:** Puede crear usuarios con contraseñas temporales simples (ej. `1234`) para facilitar la entrega.
    *   **Usuario:** El sistema obliga al cambio de clave en el primer login, exigiendo el cumplimiento del protocolo estricto (8+ caracteres, Mayúscula, Número y Carácter Especial).
*   **Sistema de Auditoría:** Registro automático en `auditoria_usuarios.log` de todas las creaciones y cambios de clave.

### 2.2. Analítica Visual y Reportes
*   **Dashboard de 24 Horas:** Los relojes (Gauges) y gráficos de latencia ahora reflejan con precisión las últimas 24 horas de actividad.
*   **Reportes PDF Profesionales:** El botón "Generar Reporte" ahora genera un documento que incluye:
    *   Tabla detallada de equipos.
    *   **Gráfico de Latencia** de todos los equipos.
    *   **Mapa de Calor (Heatmap)** de disponibilidad horaria.
*   **Log de Disponibilidad Mensual:** Nuevo archivo `disponibilidad_mensual.json` que guarda el promedio diario de cada equipo durante los últimos 30 días.

### 2.3. Blindaje Visual
*   **Iconografía Personalizada:** Uso de `sentinel_icon.ico` en todas las ventanas y barra de tareas, eliminando los iconos por defecto de la librería gráfica.

---

## 3. Guía de Operación

### 3.1. Configuración Inicial (Setup)
Al ejecutar la aplicación por primera vez, se solicita la creación del **Administrador Maestro** con una contraseña segura obligatoria.

### 3.2. Operación Diaria
1.  **Monitoreo:** La app está diseñada para correr durante la jornada laboral (09:00 - 17:00).
2.  **Logs Automáticos:** Se generan reportes de estado a las 11:00 AM y 14:30 PM.
3.  **Cierre del Día:** Al guardar la configuración o al ejecutarse los logs automáticos, el sistema registra la disponibilidad del día.

---

## 4. Estructura de Proyecto (Compilado)
```
SentinelNetwork/ (Carpeta de Instalación)
├── Anvic_Sentinel_V2.exe       # Ejecutable Principal
├── users.json                  # Base de datos de usuarios
├── equipos_guardados.json      # Configuración de monitoreo
├── disponibilidad_mensual.json # Historial de 30 días
├── auditoria_usuarios.log      # Log de seguridad y claves
├── historial_log.txt           # Logs de estado automáticos
├── metricas_historial.json     # Datos para gráficos de 24h
└── assets/                     # Recursos (Audios e Imágenes)
```

---

## 5. Soporte y Créditos
**Anvic Network Sentinel v2.0**
*   **Desarrollado por:** Omar Toledo Castro | @Betograf_inc
*   **Copyright:** 2026. Uso exclusivo para Control de Acceso Anvic.


## Versión 2.2.1 - Master Release
* **Licenciamiento Criptográfico Fuerte (RSA):** Integración completa del sistema de licencias perpetuas en Inno Setup y PyInstaller.
* **Build Pipeline Industrial:** Ofuscación automática (Cython), protección de secretos y empaquetado seguro en dist/.
* **Resolución de Assets y Audio:** Corrección del colector de basura en Pygame para la reproducción de MP3s y sistema fallback en Windows (winsound).
