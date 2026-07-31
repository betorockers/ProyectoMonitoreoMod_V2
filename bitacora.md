# Bitácora del Proyecto
## Anvic Network Sentinel v2.2.1

## Fecha de actualización
20 de marzo de 2026

## Estado general
El proyecto se encuentra en **etapa de cierre técnico y release candidate comercial**. La base funcional principal ya quedó implementada, el instalador fue modernizado, el licenciamiento está operativo y la plataforma fue endurecida con una ronda importante de ciberseguridad.

---

## Resumen ejecutivo de avance

Durante esta etapa de trabajo, Anvic Network Sentinel dejó de ser solo una evolución del monitor original de red y pasó a consolidarse como una plataforma de monitoreo técnico y visual con potencial comercial real para ANVIC.

Se trabajó sobre cinco frentes principales:

1. consolidación de branding e identidad del producto
2. ampliación funcional del monitoreo y diagnóstico
3. incorporación de supervisión visual de cámaras
4. endurecimiento de seguridad, build e instalador
5. creación de documentación técnica, comercial y operativa
6. integración final de notificaciones Telegram administrables

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
