# Manual de Usuario
## Anvic Network Sentinel v2.2.4 - Edición Pro (Industrial)

Este manual describe el uso operativo de **Anvic Network Sentinel** desde la instalación inicial hasta la utilización completa de sus funciones en la edición `Pro`.

---

## 1. Introducción

Anvic Network Sentinel es una plataforma de monitoreo técnico y visual orientada a instalaciones conectadas. Su objetivo es permitir a operadores, técnicos y administradores:

- supervisar equipos en red
- diagnosticar conectividad y servicios
- observar cámaras y fuentes visuales
- generar reportes ejecutivos
- administrar usuarios, licencias y parámetros operativos

La edición `Pro` concentra la experiencia completa del producto.

---

## 2. Antes de instalar

Antes de comenzar, asegúrese de contar con:

- un equipo Windows 64 bits compatible
- serial de activación entregado por ANVIC
- conexión de red hacia los activos que monitoreará
- permisos para instalar software en el equipo anfitrión

Si trabajará con cámaras, tenga disponibles:

- IP o hostname
- credenciales si aplica
- URL snapshot o RTSP

Si trabajará con diagnósticos avanzados, tenga disponibles:

- puertos relevantes
- comunidad SNMP si corresponde
- credenciales SSH si corresponde

---

## 3. Instalación

## 3.1 Ejecutar el instalador

1. Abra el instalador oficial de Anvic Network Sentinel.
2. Lea la bienvenida del wizard.
3. Ingrese el serial solicitado.
4. Seleccione la carpeta de instalación.
5. Finalice el proceso.

El instalador crea la estructura base y deja preparado el primer inicio de la aplicación.

## 3.2 Primer arranque

Al abrir la aplicación por primera vez:

1. se validará la licencia
2. se completará la activación local del equipo
3. se le pedirá crear el usuario administrador inicial si corresponde

Si la licencia no es válida o ha expirado, la aplicación mostrará la ventana de activación o bloqueo correspondiente.

---

## 4. Inicio de sesión y seguridad

La aplicación utiliza autenticación local con roles y almacenamiento seguro.

### Rol administrador

Puede:

- crear usuarios
- configurar parámetros globales
- administrar licencias
- definir políticas TLS y SSH
- configurar supervisión visual y límites operativos

### Rol operador

Puede:

- monitorear equipos
- revisar historial
- usar herramientas operativas habilitadas
- trabajar con cámaras según permisos visibles

---

## 5. Estructura general de la aplicación

La versión actual se organiza en cinco módulos principales:

- `Operación en Vivo`
- `Historial Operacional / Telemetría`
- `Supervisión Visual`
- `Centro de Soporte`
- `Administración`

---

## 6. Operación en Vivo

Este módulo es la vista principal de monitoreo.

### Qué permite hacer

- visualizar el estado actual de los equipos
- observar disponibilidad, latencia y cambios de estado
- cargar o actualizar inventario de activos monitoreados
- operar sobre el conjunto activo de equipos

### Flujo típico de uso

1. Agregue un equipo indicando IP o host, nombre y parámetros básicos.
2. Guarde la configuración.
3. Revise las tarjetas o bloques de estado.
4. Observe cambios de color, alertas o latencias.

### Recomendación

Utilice nombres descriptivos por instalación, por ejemplo:

- `Camara LPR Acceso Norte`
- `Totem Salida 01`
- `Kiosko Informativo Lobby`
- `Servidor MeiPass Local`

---

## 7. Historial Operacional y Telemetría Adaptativa

Este módulo concentra la trazabilidad, los gráficos históricos y la telemetría dinámica de rendimiento.

### Modos de Visualización Dinámica (Barra Superior)
En la parte superior de la vista de telemetría, el operador puede seleccionar instantáneamente entre 4 modalidades operativas:

1. **Semanal (7D x 24h):**
   - Análisis macroscópico de los últimos 7 días completos (matriz 7D × 24h).
   - KPIs de uptime, latencia media y percentil 95 consolidados en 168 horas continuas.
2. **Semanal (7D x Turno):**
   - Análisis de los últimos 7 días acotado estrictamente a la franja horaria del turno configurado en Administración (ej: 07:00 a 18:00).
   - El mapa de calor (heatmap) y los gauges reflejan únicamente la disponibilidad durante la jornada laboral activa.
3. **Por Equipo (24h):**
   - Comparativa individualizada entre todos los equipos monitoreados durante las últimas 24 horas continuas.
   - Cada fila del mapa de calor representa un equipo en la red.
4. **Por Equipo (Turno):**
   - Comparativa individualizada por equipo focalizada exclusivamente en las horas del turno en curso.

### Rendimiento Multihilo y Refresco Continuo
- **Procesamiento Asíncrono:** Todas las consultas SQL y cálculos matemáticos se ejecutan en segundo plano, manteniendo la interfaz a 60 FPS estables sin tirones ni demoras.
- **Refresco Automático:** El sistema actualiza las métricas cada **15 segundos**, con renderizado no bloqueante (`draw_idle`).
- **Desacople Multi-Monitor:** Utilice el botón `⧉ Desacoplar` para proyectar el dashboard de telemetría de forma continua en una pantalla secundaria física.

---

## 8. Supervisión Visual

Este módulo se orienta a cámaras y validación visual de activos.

Se divide en dos áreas:

- `Perfiles y Pruebas`
- `Video en Vivo`

## 8.1 Perfiles y Pruebas

Aquí se registran y prueban perfiles de cámara.

### Datos habituales de un perfil

- nombre de cámara
- IP o hostname
- URL snapshot
- URL RTSP
- usuario
- contraseña
- observaciones si aplica

### Qué permite hacer

- guardar perfiles
- probar snapshot
- validar si la ruta RTSP responde
- enviar un perfil a la vista de video en vivo

## 8.2 Video en Vivo

Aquí se opera la visualización continua.

### Qué permite hacer

- iniciar vista en vivo
- operar con RTSP real si la fuente está disponible
- caer a snapshot si no hay stream continuo
- manejar mosaico operativo según límite de streams simultáneos

### Recomendaciones operativas

- use streams secundarios si las cámaras lo permiten
- no configure más streams simultáneos que los que el host soporte de forma estable
- si una cámara es legacy, pruebe primero snapshot antes de exigir RTSP

---

## 9. Centro de Soporte

Este módulo combina herramientas de diagnóstico remoto y soporte local del puesto Sentinel.

Se organiza en dos grandes áreas:

- `Red e Instalaciones`
- `Estado del Puesto`

## 9.1 Red e Instalaciones

Aquí se concentran las herramientas orientadas a la red o al activo remoto.

### Resumen de Red

Incluye:

- `Ping`
- `Tracert`
- `Lookup`
- `HTTP`
- `HTTPS`
- `Puertos`
- `SNMP`
- `SSH`

### Uso de las herramientas

#### Ping

- valida disponibilidad básica
- permite verificar si el objetivo responde por red
- puede detenerse mediante el control de prueba activa

#### Tracert

- permite revisar ruta de red
- útil para detectar saltos o pérdidas

#### Lookup

- resuelve DNS y ayuda a validar nombres de host

#### HTTP / HTTPS

- valida servicios web
- muestra respuesta y tiempos
- utiliza la política TLS configurada en administración

#### Puertos

- comprueba puertos específicos sin desbordar el host
- recomendado para `80`, `443`, `554`, `22`, `161` y puertos propios de NVR o fabricantes

#### SNMP

- consulta información estándar del equipo
- útil para switches, routers, impresoras, UPS y algunos equipos embebidos

#### SSH

- permite ejecutar un comando de consulta remota
- respeta la política de validación de host key configurada

### Otras áreas de Red e Instalaciones

- `Auditoría Técnica`
- `Inventario ARP`
- `Sesiones de Red`

Estas áreas ayudan a complementar análisis operativo desde el host Sentinel.

## 9.2 Estado del Puesto

Aquí se supervisa el equipo donde corre Sentinel.

### Resumen del Host

Permite revisar:

- hostname
- IP local
- MAC
- gateway
- DNS

### Recuperación Técnica

Incluye acciones como:

- limpiar DNS
- renovar IP
- liberar IP

Estas acciones afectan el equipo local, no el remoto.

### Servicios del Sistema

Permite revisar servicios locales relevantes para la operación del host Sentinel.

---

## 10. Administración

Este módulo centraliza la configuración global de la plataforma.

### Qué suele administrarse aquí

- usuarios y roles
- parámetros de operación
- comportamiento de cámaras
- políticas TLS
- geolocalización externa para traceroute
- modo SSH
- límite de streams simultáneos
- estado de licencia
- notificaciones Telegram opcionales

## 10.1 Usuarios

El administrador puede:

- crear usuarios
- definir roles
- bloquear o revisar acceso según política interna

## 10.2 Licencia

Aquí se puede revisar:

- edición
- tipo de licencia
- vigencia
- serial parcial o identificador
- estado general de activación

## 10.3 Seguridad de red

### Modo TLS estricto

Si está activo:

- Sentinel valida certificados HTTPS/TLS

Si está desactivado:

- permite conectarse a equipos con certificados autofirmados o legacy

Uso recomendado:

- `activo` en entornos corporativos
- `flexible` solo cuando la operación técnica lo necesite

### Geolocalización externa

Puede habilitarse o dejarse desactivada.

Recomendación:

- dejarla desactivada por defecto
- activarla solo si aporta valor operativo concreto

## 10.4 Configuración de Turnos Operacionales

El Administrador puede definir y ajustar en cualquier momento las franjas horarias de operación:

- **Hora Inicio del Turno:** Selector de `00:00` a `23:00`.
- **Hora Fin del Turno:** Selector de `00:00` a `23:00`.
- **Turnos Nocturnos:** Si la hora de inicio es mayor que la de fin (ejemplo: `20:00` a `06:00`), el sistema detecta automáticamente que el turno cruza la medianoche y adapta el análisis sin fallos de desbordamiento.
- **Persistencia y Reactividad:** Al presionar *"💾 Guardar Configuración de Turno"*, los valores se cifran en disco y se propagan inmediatamente a la pestaña de Telemetría sin reiniciar la aplicación.

## 10.5 Actualizaciones y Parches Industriales

Para actualizar la aplicación en máquinas donde ya se encuentra instalada:

1. **Ejecutar el instalador de parche:** Ejecute `ANS_Patch_V2.2.4.exe` como Administrador.
2. **Detección Automática:** El asistente localiza la ruta de instalación en el Registro de Windows y verifica que el software esté instalado.
3. **Backup Preventivo:** Antes de sobreescribir cualquier archivo, el instalador crea una copia de seguridad en `{app}\backups\backup_pre_patch_[TIMESTAMP]\` y genera un script `rollback.bat` para revertir al estado anterior en un clic si fuese necesario.
4. **Protección Total de Datos:** El proceso **nunca toca ni reinicia** la base de datos de mediciones `anvic_monitor.db`, los usuarios registrados ni la clave de cifrado maestro.

### Política SSH

Puede operar en:

- `estricto`
- `TOFU`
- `sin validación`

Recomendación:

- usar `estricto` como estándar
- usar `TOFU` en despliegues controlados
- evitar `sin validación` salvo laboratorios o pruebas muy puntuales

### Límite de streams simultáneos

Este valor debe ajustarse según capacidad del host.

Recomendación:

- partir con valores bajos
- subir gradualmente según estabilidad real del equipo

---

## 11. Telegram y alertas

La edición comercial puede enviar notificaciones por Telegram si el administrador decide habilitar esta función desde `Administración`.

### Qué se configura

- `Token` del bot
- `Chat ID`
- nombre de la instalación
- título base de la notificación

### Qué envía Sentinel

- aviso cuando un equipo se cae
- aviso cuando un equipo se recupera
- alerta de gravedad cuando un equipo supera 5 minutos desconectado sin recuperarse

### Ejemplo de formato

`Notificación enviada desde CIAL`

Luego el detalle del evento:

- equipo afectado
- IP o host
- tipo de evento
- tiempo de caída si corresponde

### Buenas prácticas

- usar un bot dedicado para Sentinel
- ingresar credenciales solo desde la pestaña de administración
- no reutilizar el token en otros servicios ajenos
- realizar una prueba manual después de guardar la configuración

---

## 12. Generación de reportes PDF

Sentinel puede generar reportes formales con:

- branding corporativo
- resumen operacional
- tabla profesional de equipos
- gráficos históricos más grandes
- capacidades operativas actuales del producto

### Cuándo generarlos

- cierres periódicos
- revisión gerencial
- soporte a cliente
- evidencia operativa
- análisis posterior a incidentes

---

## 13. Buenas prácticas de operación

- use nombres consistentes por instalación
- documente comunidad SNMP, puertos y accesos de forma separada y segura
- no habilite funciones avanzadas sin necesidad real
- mantenga el host Sentinel con horario correcto
- controle el número de streams simultáneos
- mantenga actualizada la licencia y el inventario de equipos

---

## 14. Buenas prácticas de ciberseguridad

- mantener TLS estricto cuando sea posible
- evitar guardar credenciales fuera del sistema
- usar validación SSH estricta o TOFU
- no compartir seriales entre instalaciones
- proteger respaldos y reportes si contienen información sensible
- limitar el acceso al módulo de administración

---

## 15. Flujo recomendado de puesta en marcha

1. Instalar Sentinel con serial válido.
2. Activar y crear usuario administrador.
3. Definir política TLS y SSH.
4. Cargar equipos monitoreados.
5. Probar diagnóstico básico.
6. Configurar perfiles de cámaras.
7. Ajustar límite de streams.
8. Revisar historial.
9. Configurar Telegram si la instalación requiere alertamiento externo.
10. Generar reporte inicial.
11. Dejar operación estable y documentada.

---

## 16. Solución rápida de problemas

### El equipo responde ping, pero el servicio no

Use:

- `HTTP/HTTPS`
- `Puertos`
- `SNMP`
- `SSH`

### La cámara responde por IP, pero no muestra imagen

Revise:

- URL snapshot
- URL RTSP
- puerto `554`
- credenciales
- límite de streams

### El chequeo HTTPS falla

Revise:

- certificado
- política TLS configurada
- endpoint real

### El SSH no conecta

Revise:

- usuario y contraseña
- puerto
- host key
- modo `estricto` o `TOFU`

### El rendimiento visual cae

Revise:

- cantidad de cámaras activas
- cantidad de streams simultáneos
- perfil del host

---

## 17. Alcance de la edición Pro

La edición `Pro` representa la experiencia más completa del producto, integrando:

- monitoreo operativo
- historial
- diagnósticos avanzados
- soporte técnico
- supervisión visual
- reportes formales
- licenciamiento profesional

Es la edición recomendada para operación interna avanzada y para oferta comercial de mayor valor.

---

## 18. Cierre

Anvic Network Sentinel debe operarse como plataforma de monitoreo y soporte técnico con criterio profesional. La estabilidad final dependerá no solo del software, sino también de:

- la calidad del host
- la red disponible
- la configuración de cámaras y equipos
- la política de seguridad aplicada

Usado correctamente, permite supervisar instalaciones, acelerar diagnóstico y respaldar servicios de continuidad operacional.

---

**Producto:** Anvic Network Sentinel  
**Versión de referencia:** 2.2.1  
**Manual actualizado:** Marzo 2026
