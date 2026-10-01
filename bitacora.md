# Bitácora del Proyecto
## Anvic Network Sentinel v2.2.10 (Grado Industrial Fortune 500)

## Fecha de actualización
01 de Octubre de 2026

## Estado general
El proyecto se encuentra en **producción comercial industrial congelada (v2.2.10)**. Se completó la reingeniería del generador de reportes ejecutivos (3/4 páginas sin huérfanos), drag & drop fluido de tarjetas a 60 FPS con modal rápido, desbloqueo y sincronización del Super User, traslado de intervalo ping a administración y certificación automatizada (73/73 tests PASS).

---

## Resumen ejecutivo de avance (Cierre v2.2.10)

Durante esta sesión de trabajo de alto impacto (v2.2.10), se perfeccionaron los módulos operativos más sensibles solicitados por betorock:

1. **Reingeniería de Reporte Ejecutivo PDF (ReportLab / Matplotlib):**
   - Garantía de 3 páginas exactas (≤10 equipos o modo semanal) y 4 páginas dinámicas (>10 equipos) con salto inteligente sin páginas en blanco.
   - Espacio de aire visual (14pt) entre gráfica de latencia y matriz de disponibilidad (Heatmap).
   - Formateo jerárquico de tarjeta de Downtime Red (Opción A): Promedio en 13pt bold y Pico Máximo en 8pt rojo (`#DC2626`).
   - Bloques protegidos con `KeepTogether` y `keepWithNext=True` para eliminar para siempre títulos desprendidos.
   - Datos dinámicos de empresa-cliente y sitio/planta en cabecera y pie de página; toggle para ocultar supervisión CCTV cuando no aplique.
2. **Reorganización Interactiva de Tarjetas de Monitoreo:**
   - Reducción compacta de ~5.5 mm por tarjeta con mayor elegancia y densidad visual.
   - Micro-botones `[ ◀ ]` y `[ ▶ ]` para desplazamiento de slot instantáneo.
   - Drag & Drop a 60 FPS con cálculo euclidiano y glow ámbar/cyan en dropzones.
   - Guardado silencioso debounced (1.2s) para no congelar la UI con cifrado en disco.
   - Modal interactivo al pinchar la tarjeta (edición de Nombre, IP, Ubicación y posición rápida).
3. **Seguridad y Gestión de Usuarios:**
   - Corrección de signatura y permisos en `auth_manager.py:update_user` desbloqueando la edición de Super Usuario (`BetoDev`).
   - Sincronización en tiempo real de `current_user` en memoria para reflejar cambios de inmediato sin relogueo.
   - Migración del intervalo de ping a Configuración de Red en el Administrador.
4. **Certificación y Parches:**
   - 73/73 tests unitarios y de integración aprobados (100%).
   - Instalador diferencial `ANS_Patch_V2.2.10.exe`, instalador completo `ANS_Setup_V2.2.10.exe` y paquete portable desatendido.

Se trabajó sobre las siguientes áreas clave:

1. consolidación de branding e identidad del producto
2. ampliación funcional y reparación de UI (scroll, colores) en OSINT
3. implementación de roles estrictos (admin, user, super_admin)
4. automatización inteligente del módulo IPGeo y Escáner LAN
5. endurecimiento de seguridad, firma local y renombrado de uninstaller
6. creación y actualización del ancla de sesión para seguimiento continuo

---

## Hitos cerrados en esta versión

### 1. Identidad del producto

- Se consolidó el nombre oficial `Anvic Network Sentinel`.
- Se alinearon íconos, logos, ejecutable, instalador y textos visibles.
- Se dejó la autoría visible alineada a `Omar Toledo`.
- Se incorporó el título institucional de uso exclusivo para ANVIC en la ventana principal.

### 2. Monitoreo y diagnóstico ampliado

Se integraron a la app activa:

- chequeos `HTTP/HTTPS`
- escaneo de puertos controlado
- `SNMP` básico
- `SSH` de consulta
- mejoras en la pestaña de diagnóstico
- control de detención de pruebas activas

### 3. Supervisión visual

Se dejó incorporado el módulo `Supervisión Visual`, con:

- perfiles de cámara
- pruebas de snapshot
- prueba de RTSP
- vista `Video en Vivo`
- mosaico operacional controlado
- límite de streams simultáneos configurable

### 4. Reportes profesionales

- Se modernizó la salida PDF.
- Los gráficos se ampliaron para lectura real.
- El reporte ahora refleja mejor las capacidades actuales del producto.

### 5. Build e instalador

- Se modernizó `AnvicNetworkSentinel.spec`.
- Se modernizó `installer.iss`.
- Se dejó el instalador en español, con wizard moderno y mejor presentación.
- Se desactivó `UPX` para reducir falsos positivos antivirus.
- Se recompiló la app desde `monitorEnv`.

### 6. Licenciamiento

Se integró un subsistema de licencias offline firmadas, con:

- licencias `TRIAL`
- licencias `ANNUAL`
- licencias `PERPETUAL`
- ediciones `STANDARD`, `ADVANCED` y `PRO`
- serial en wizard de instalación
- validación de licencia al arranque
- lotes emitidos y resguardados

### 7. Ciberseguridad

Se realizó una ronda relevante de hardening:

- saneamiento de secretos locales
- eliminación de tokens hardcodeados
- política TLS configurable con modo estricto
- geolocalización externa desactivable
- validación SSH con host key real y modo TOFU opcional
- unificación de la rama modular hacia componentes más seguros
- mejor resguardo de configuración sensible
- eliminación completa de token y chat ID hardcodeados de Telegram

### 8. Notificaciones Telegram administrables

Se dejó integrada la capacidad de notificación por Telegram en la app comercial activa, con enfoque administrable y sin credenciales embebidas.

- el administrador puede ingresar `token` y `chat_id` desde `Administración`
- puede definir nombre de instalación y título base del mensaje
- se envían alertas por caída, recuperación y gravedad
- la alerta crítica se dispara cuando un equipo supera 5 minutos desconectado
- los mensajes identifican de qué instalación provienen
- Telegram queda desactivado por defecto si no se configura

### 9. Documentación

Se dejaron preparados o actualizados:

- análisis de software
- visión de producto
- propuesta técnico-comercial
- propuesta gerencial interna
- valoración comercial
- matriz de licenciamiento
- requerimientos del sistema
- manual de usuario Pro
- revisión de ciberseguridad
- inventario de licencias emitidas

---

## Estado técnico comprobado

- suite de pruebas: `39 passed`
- build final generado desde entorno correcto
- instalador final compilado
- seriales de laboratorio preparados
- lotes comerciales y trial emitidos

Artefactos principales:

- `dist/AnvicNetworkSentinel/AnvicNetworkSentinel.exe`
- `Output/Instalador_Anvic_Network_Sentinel_v2.2.1.exe`

---

## Deudas o tareas no bloqueantes

Aunque la versión está fuerte, todavía existen tareas que pueden abordarse en una nueva iteración:

- smoke final manual completo de instalación, activación y desinstalación
- firma digital del ejecutable y del instalador
- validación RTSP real con fuentes de laboratorio o cámaras productivas
- posible backend futuro de activación/revocación
- evaluación futura de compilación con Nuitka en rama separada

---

## Conclusión de bitácora

La `v2.2.1` representa un salto importante respecto a las versiones previas. El software ya no está en fase exploratoria: está en una etapa madura de producto interno profesional, con base suficiente para pilotos, operación real y presentación formal ante ANVIC.

---

**Producto:** Anvic Network Sentinel  
**Versión:** 2.2.1  
**Estado:** Release candidate técnico


### 30 de Julio 2026 - Cierre de Versión 2.2.1
Se finalizaron las integraciones del pipeline de compilación. El ejecutable ahora está fuertemente ofuscado con Cython, empaquetado con Pyinstaller, y sellado con Inno Setup pidiendo la validación criptográfica RSA antes y durante la instalación. Se parcheó el sistema de audio para corregir un bug de recolección de basura con Pygame. Se generó copia de seguridad del código completo.

---

## 🚀 Versión 2.2.4 — 30 de Septiembre 2026 (Telemetría Adaptativa & Sistema de Parches Industriales)

### Hitos y Logros de la Versión 2.2.4:
1. **Telemetría Dinámica Adaptativa:**
   - Implementado selector en barra superior con 4 modos operativos: `Semanal (7D x 24h)`, `Semanal (7D x Turno)`, `Por Equipo (24h)` y `Por Equipo (Turno)`.
   - Adaptación completa de KPIs, percentil 95, gráfico de latencia temporal, gauges y heatmap según la franja horaria.
2. **Configuración de Turnos en Módulo Administrador:**
   - Selectores de `Hora Inicio Turno` y `Hora Fin Turno` (00:00 a 23:00) con persistencia cifrada en `equipos_guardados.json.enc`.
   - Soporte matemático completo para turnos que cruzan la medianoche (ej. 20:00 a 06:00).
3. **Optimización Multihilo y Reducción de I/O SQLite:**
   - Desacople total de la UI: consultas SQLite y cálculos matemáticos movidos a hilo secundario daemon con entrega reactiva thread-safe vía `app.after()`.
   - Creación de índices compuestos `idx_mediciones_ip_ts` e `idx_mediciones_ts`, reduciendo las consultas a < 15ms.
   - Implementación de **Widget Pooling** en gauges y filas de tabla, eliminando el DOM thrashing y llamadas destructivas `destroy()`.
   - Reemplazo de `fig.canvas.draw()` por `draw_idle()` e incremento del refresco automático de 60s a 15s estables.
4. **Sistema Industrial de Parches Diferenciales:**
   - Construcción de `build_patch.py`, `crear_parche.bat` y `patch_installer.iss`.
   - Garantía de protección de datos: `anvic_monitor.db`, `users.json.enc` y licencias quedan 100% intactas.
   - Generación del instalador ligero `Output/ANS_Patch_V2.2.4.exe` (15.16 MB) y paquete portable `Output/ANS_Patch_V2.2.4_Portable.zip` (13.20 MB).
   - Doble firma digital Authenticode SHA-256 con timestamp RFC 3161 de DigiCert.
5. **Certificación QA:**
   - 62 de 62 pruebas unitarias pasando al 100% en pytest (0 fallos, 0 errores).

---

## 🚀 Versión 2.2.5 — 01 de Octubre 2026 (Hotfix UI: Selectores Desplegables de Telemetría)

### Hitos y Logros de la Versión 2.2.5:
1. **Rediseño UI de Modos de Telemetría (Estilo Dropdown / CTkOptionMenu):**
   - Reemplazo del botón segmentado horizontal (`CTkSegmentedButton`) por dos selectores desplegables modernos (`CTkOptionMenu`):
     - `Semanal`: Desplegable con opciones `Semanal (7D x 24h)` y `Semanal (7D x Turno)`.
     - `Por Equipo`: Desplegable con opciones `Por Equipo (24h)` y `Por Equipo (Turno)`.
   - Idéntica estética visual que el selector de equipos (`Todos los Equipos`): fondo `#334155` y botón de flecha `#475569`.
   - **Indicador Dinámico Activo:** El menú de la modalidad actualmente activa se resalta en azul `#0284C7` (Argos Blue) mientras que el inactivo permanece en dark slate `#334155`, ofreciendo claridad visual instantánea.
2. **Compatibilidad Total y Reactividad:**
   - Mantenimiento estricto de compatibilidad regresiva con `_on_heatmap_mode_change`.
   - Sincronización bidireccional entre la ventana desacoplada (popout multimonitor) y la pestaña original integrada.
3. **Certificación y Empaquetado de Parche Diferencial:**
   - Suite de pruebas ejecutada: **63 de 63 tests pasando al 100% (PASS)**.
   - Generados artefactos listos para producción en `Output/`:
     - `Output/ANS_Patch_V2.2.5.exe` (15.16 MB) con firma Authenticode SHA-256 y timestamp RFC 3161.
     - `Output/ANS_Patch_V2.2.5_Portable.zip` (13.20 MB) con scripts de instalación y rollback desatendido.
     - `Output/patch_staging/patch_manifest.json` con hashes criptográficos.

