# Documentacion Tecnica
## Anvic Network Sentinel v2.2.1

## 1. Descripcion general

Anvic Network Sentinel es una plataforma Windows-first de monitoreo tecnico y visual orientada a instalaciones de seguridad, control de acceso, CCTV y soporte operativo.

La version `2.2.1` consolida una base funcional y comercial con:

- monitoreo operativo de activos IP
- historial y reportabilidad PDF
- diagnostico remoto por protocolos
- supervision visual de camaras
- licenciamiento profesional
- endurecimiento de ciberseguridad
- alertamiento opcional por Telegram administrado desde la UI

---

## 2. Arquitectura vigente

La ruta comercial activa del producto se ejecuta desde:

- `main.py`
- `monitor.py`

La base del proyecto se apoya en estos bloques:

1. `core/`
   - soporte de logica complementaria y componentes modulares
2. `ui/`
   - tabs, ventanas y componentes reutilizables
3. `services/`
   - integraciones como red, reportes, camaras y Telegram
4. `database/`
   - persistencia de eventos, disponibilidad y metricas
5. `auth/`
   - gestion de identidad y autenticacion
6. `config/`
   - branding, parametros y perfil de build
7. `licensing/`
   - validacion, almacenamiento y firma de licencias
8. `tools/`
   - utilidades auxiliares para soporte y emision

---

## 3. Capacidades tecnicas actuales

### Monitoreo operativo

- chequeo continuo de disponibilidad
- latencia y estados conectado/desconectado
- historial operacional
- trazabilidad de desconexiones

### Diagnostico remoto

- `Ping`
- `Tracert`
- `Lookup`
- `HTTP/HTTPS`
- puertos controlados
- `SNMP`
- `SSH`

### Supervision visual

- perfiles de camara
- snapshot
- prueba RTSP
- video en vivo
- mosaico controlado por capacidad del host

### Administracion

- usuarios y roles
- licencia activa
- modo TLS
- politica SSH
- limite de streams
- geolocalizacion externa opcional
- modulo Telegram configurable

---

## 4. Telegram administrable

La version comercial ya no incorpora credenciales Telegram precargadas.

El funcionamiento correcto es este:

- el administrador decide si usara o no Telegram
- si lo usara, ingresa manualmente:
  - `token`
  - `chat_id`
  - nombre de instalacion
  - titulo base de notificacion
- la configuracion se guarda en almacenamiento seguro de la aplicacion

Tipos de notificacion soportados:

- caida de equipo
- recuperacion de equipo
- alerta de gravedad al superar 5 minutos sin recuperacion

Formato esperado:

- encabezado con texto base definido por administracion
- identificacion de la instalacion
- detalle del equipo afectado y su estado

---

## 5. Postura de ciberseguridad aplicada

La `v2.2.1` incorpora medidas relevantes:

- sin tokens o chat IDs hardcodeados en codigo comercial
- TLS configurable con enfoque estricto
- geolocalizacion externa desactivable
- validacion SSH con host key y modo TOFU opcional
- configuracion sensible protegida
- licenciamiento firmado offline
- build endurecido sin `UPX`

La aplicacion no pretende ser indecompilable, pero si elevar de forma seria la barrera frente a manipulacion casual, fuga de secretos y uso comercial no autorizado.

---

## 6. Build y entrega

Artefactos comerciales de referencia:

- `dist/AnvicNetworkSentinel/AnvicNetworkSentinel.exe`
- `Output/Instalador_Anvic_Network_Sentinel_v2.2.1.exe`

La version comercial es la unica ruta de entrega vigente. La variante demo fue descartada como linea activa de distribucion.

---

## 7. Linea futura de backend de licencias

Como evolucion futura recomendada, Sentinel puede incorporar un backend de activacion y revocacion de licencias para evitar reutilizacion de una misma serial en distintos equipos.

La idea base es mantener el modelo actual `offline-first`, pero agregar validacion centralizada para:

- registrar activaciones por equipo
- vincular serial a huella de maquina
- controlar cantidad maxima de activaciones
- permitir reinstalacion del mismo host bajo politica definida
- revocar o renovar licencias anuales

Plataformas evaluadas conceptualmente:

- `Supabase` como opcion preferente por su modelo relacional, trazabilidad y facilidad para gestionar licencias, instalaciones y activaciones
- `Firebase` como alternativa viable, especialmente si en el futuro se privilegian eventos push o ecosistemas moviles/web

La recomendacion tecnica actual es:

- conservar la validacion local firmada ya implementada
- sumar a futuro un backend de activacion centralizado
- usar ese backend para controlar reutilizacion de seriales en equipos distintos

---

## 8. Estado tecnico

- suite automatizada estable
- build comercial compilado
- instalador comercial compilado
- licenciamiento emitido
- documentacion alineada al estado real del producto

---

## 9. Observacion final

La base actual ya es suficientemente solida para pilotos internos, presentacion gerencial, operacion controlada y evolucion comercial dentro del marco de servicios ANVIC.

---

**Producto:** Anvic Network Sentinel  
**Version:** 2.2.1  
**Estado:** Release candidate comercial
