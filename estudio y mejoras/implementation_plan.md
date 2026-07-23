# Plan de Implementación: Control de Accesos Basado en Roles (RBAC)

Este plan describe el diseño y la implementación de restricciones de acceso por rol de usuario (Super Administrador, Administrador, Operador) en la consola de Argos Guard Enterprise v4.0.

## User Review Required

> [!IMPORTANT]
> **Modificación del Modelo de Perfil de Usuario (`UserProfile`):**
> Se agregará un campo `created_by` como clave foránea a `User` en `UserProfile` para rastrear quién creó a cada operador y poder aplicar la restricción de que los administradores solo puedan eliminar usuarios operadores creados por ellos mismos. Esto requiere correr una migración de base de datos (`makemigrations` y `migrate`).

## Proposed Changes

### 1. Base de Datos / Modelos

#### [MODIFY] [models.py](file:///E:/ProyectoMonitoreoMod_V2/backend_v4/apps/security/models.py)
*   Añadir el campo `created_by` a `UserProfile`:
    ```python
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='created_profiles')
    ```

---

### 2. Autenticación y Gestión de Usuarios (Backend)

#### [MODIFY] [views.py](file:///E:/ProyectoMonitoreoMod_V2/backend_v4/apps/security/views.py)
*   **`create_user`**:
    *   Validar que si el usuario autenticado (`request.user.profile.role`) es `admin`, el rol del nuevo usuario recibido en el formulario debe ser **estrictamente** `operator`. Si intenta crear un usuario con rol `admin` o `super_admin`, se retornará un mensaje de error.
    *   Asignar `created_by = request.user` en la creación del perfil.
*   **Crear Vista `delete_user`**:
    *   Crear endpoint `@require_POST def delete_user(request, user_id):`
    *   **Permisos de Eliminación**:
        *   Si el usuario logueado is `super_admin`: Permiso para eliminar cualquier usuario (excepto a sí mismo).
        *   Si el usuario logueado es `admin`: Permiso para eliminar únicamente a usuarios con rol `operator` cuyo perfil tenga `created_by == request.user`.
        *   Cualquier otra persona recibirá un error HTTP 403 Forbidden.
*   **Restringir Configuración Global**:
    *   Las vistas `save_telegram`, `save_api_key`, `save_webhook`, `save_sla`, y `save_system_params` deberán validar que el usuario logueado sea `super_admin`. Si un `admin` intenta llamarlas, el backend responderá con error.

#### [MODIFY] [urls.py](file:///E:/ProyectoMonitoreoMod_V2/backend_v4/apps/security/urls.py)
*   Registrar la ruta de eliminación de usuario: `path('config/user/delete/<int:user_id>/', views.delete_user, name='config_delete_user')`.

---

### 3. Restricciones en Monitoreo y Video Vigilancia (Backend)

#### [MODIFY] [views.py](file:///E:/ProyectoMonitoreoMod_V2/backend_v4/apps/monitoring/views.py)
*   **`add_node`** e **`import_nodes_json`**:
    *   Permitido para `super_admin` y `admin`.
    *   Rechazado (HTTP 403) para `operator`.
*   **`remove_node`**:
    *   Permitido **únicamente** para `super_admin`.
    *   Rechazado (HTTP 403) para `admin` y `operator`.
*   **`add_camera`**:
    *   Permitido para `super_admin` y `admin`.
    *   Rechazado (HTTP 403) para `operator`.
*   **`remove_camera`**:
    *   Permitido **únicamente** para `super_admin`.
    *   Rechazado (HTTP 403) para `admin` y `operator`.

---

### 4. Cambios Visuales e Interfaz (Frontend)

#### [MODIFY] [base.html](file:///E:/ProyectoMonitoreoMod_V2/backend_v4/templates/base.html)
*   **Navbar tabs**: Ocultar "Mapa Táctico", "OSINT" y "Configuración" si el usuario es `operator`.
*   **Footer**: Agregar la visualización centralizada del rol actual en negrita.
    ```html
    <div style="font-family: 'Rajdhani', sans-serif; font-size: 0.95rem; font-weight: bold; color: var(--cyan-glow);">
        ROL: {{ request.user.profile.role|upper }}
    </div>
    ```

#### [MODIFY] [dashboard.html](file:///E:/ProyectoMonitoreoMod_V2/backend_v4/templates/monitoring/dashboard.html)
*   **Operador**: Ocultar la barra lateral derecha de control completa (o los formularios de agregar/eliminar/JSON).
*   **Administrador**: Mostrar el formulario "Agregar Nodo" e importación de JSON. Ocultar por completo el formulario "Eliminar Nodo".

#### [MODIFY] [video_surveillance.html](file:///E:/ProyectoMonitoreoMod_V2/backend_v4/templates/monitoring/partials/video_surveillance.html)
*   **Operador**: Ocultar el panel lateral de Administración de Cámaras.
*   **Administrador**: Ocultar únicamente el formulario de "Eliminar Cámara".

#### [MODIFY] [user_management.html](file:///E:/ProyectoMonitoreoMod_V2/backend_v4/templates/security/partials/user_management.html)
*   **Select de Rol**: Si el usuario actual es `admin`, la opción de registrar un nuevo usuario solo tendrá disponible el rol `operator`.
*   **Panel de Configuración**: Si el usuario es `admin`, solo se mostrará la sub-pestaña "Gestión de Usuarios". Ocultar los botones de "Notificaciones", "Integraciones", "SLA" y "Parámetros" del menú lateral izquierdo.
*   **Tabla de Usuarios**: Agregar columna de "Acciones".
    *   Si es `super_admin`: Se muestra el botón de eliminar `🗑` para todos (excepto sí mismo).
    *   Si es `admin`: Se muestra el botón de eliminar `🗑` únicamente en los usuarios operadores que tienen `created_by == request.user`.
    *   Utilizar HTMX para hacer la eliminación asíncrona con el endpoint `config_delete_user`.

---

## Verification Plan

### Pruebas Unitarias
1. Ejecutar las pruebas unitarias existentes y añadir pruebas en `apps/security/test_security.py` para validar:
   - Que un usuario administrador no puede crear otro administrador.
   - Que un operador recibe 403 al intentar agregar o remover nodos.
   - Que un administrador recibe 403 al intentar remover nodos o cámaras.

### Pruebas Manuales
1. Crear un usuario Administrador y un Operador desde la interfaz de superadmin.
2. Iniciar sesión como **Operador**:
   - Verificar que no aparezcan las pestañas "Mapa Táctico", "OSINT", ni "Configuración".
   - Verificar que en "Monitoreo Activo" y "Video Vigilancia" no haya controles de adición/eliminación.
   - Validar que el rol "OPERADOR" se visualice centrado en el footer.
3. Iniciar sesión como **Administrador**:
   - Verificar que aparezcan los controles de adición pero no de eliminación de nodos y cámaras.
   - Ir a Configuración y comprobar que solo sea visible "Gestión de Usuarios".
   - Registrar un nuevo Operador y verificar que se pueda eliminar. Intentar ver otro operador/admin y comprobar que el botón de eliminar no exista.
   - Intentar descargar el reporte diario en PDF desde el historial.
