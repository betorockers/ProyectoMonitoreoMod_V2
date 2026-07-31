# Vision de Producto: Anvic Network Sentinel

## Contexto real del producto

Anvic Network Sentinel no nace como software generico de monitoreo.
Nace desde una necesidad operativa concreta:

- monitorear instalaciones reales asociadas al ecosistema MeiPass
- validar disponibilidad de componentes criticos en terreno
- detectar fallas de conectividad, servicio y operacion antes de que se conviertan en incidentes mayores
- ofrecer visibilidad operacional para empresas que prestan servicios de seguridad y control de acceso

El caso de uso inicial descrito por Beto es claro:

- una instalacion con 2 camaras LPR
- 2 totems que comandan 2 barreras de acceso
- 1 kiosko informativo
- una segunda instalacion con el mismo set
- ambas asociadas a la misma empresa
- ambas dentro del mismo ecosistema operacional, aunque separadas fisicamente

Eso convierte al producto en algo mas interesante que un simple monitor de ping:

**es una plataforma de supervision tecnica para infraestructura de acceso, seguridad y monitoreo operacional.**

---

## Marco comercial

Este proyecto tiene potencial real de convertirse en una solucion vendible por ANVIC LTDA.

Segun la pagina de servicios de ANVIC, la empresa ofrece, entre otros:

- diseno y estructura de centrales de CCTV
- puesta en marcha y operacion
- estudios de seguridad
- implementacion de medidas tecnologicas
- reparacion y mantenimiento preventivo de alarmas y CCTV
- monitoreo de instalaciones en tiempo real

Fuente:
- https://www.anvic.cl/servicios/

Ese catalogo calza de forma natural con Anvic Network Sentinel.
No seria un producto ajeno al negocio: seria una extension directa de la oferta de seguridad tecnologica y monitoreo.

En paralelo, el contexto de MeiPass confirma que existe una plataforma real de acceso/operacion con login, soporte y postura de seguridad formal, lo que refuerza la necesidad de observabilidad operacional y soporte tecnico estructurado.

Fuentes:
- https://app.meipass.com/
- https://app.meipass.com/support
- https://app.meipass.com/policy

---

## Definicion de producto

### Que es Anvic Network Sentinel

Una plataforma de monitoreo operativo para instalaciones de seguridad y control de acceso, capaz de supervisar:

- disponibilidad de equipos IP
- servicios expuestos en red
- capacidad de respuesta de interfaces web
- puertos criticos
- dispositivos administrables por SNMP o SSH
- estado visual de camaras IP mediante snapshot o streaming

### Que NO debe ser

No debe intentar convertirse de inmediato en:

- un SIEM
- una NMS empresarial total estilo Zabbix/PRTG/Nagios
- un VMS completo de CCTV
- una consola de administracion remota sin limites

Su fuerza esta en otra parte:

**visibilidad operacional util, enfocada, comercializable y alineada al negocio de seguridad integral.**

---

## Propuesta de valor

Anvic Network Sentinel puede venderse como parte de una oferta de servicios que combine:

- monitoreo tecnico
- mantenimiento preventivo
- validacion de disponibilidad
- evidencia operacional
- supervision visual de CCTV
- diagnostico remoto para soporte

En simple:

No vende solo "ver si el ping responde".
Vende una capa de supervision que ayuda a ANVIC a:

- detectar caidas
- justificar mantenimientos
- demostrar servicio
- reducir tiempos de respuesta
- profesionalizar su oferta de monitoreo tecnologico

---

## Perfiles de equipos que debe cubrir

El producto debe evolucionar para trabajar bien con perfiles reales de instalacion:

### Perfil 1: Control de acceso
- totems
- barreras
- kioskos
- controladores
- terminales asociadas

### Perfil 2: CCTV
- camaras IP modernas
- camaras antiguas accesibles por IP
- NVR
- DVR

### Perfil 3: Infraestructura de red
- switches
- routers
- access points
- equipos PoE

### Perfil 4: Hosts administrables
- servidores Windows
- servidores Linux
- PCs tecnicos
- appliances

---

## Alcance funcional priorizado

Se mantiene la priorizacion ya conversada:

### Fase A: Monitoreo inteligente por protocolo
- chequeo HTTP/HTTPS
- escaneo de puertos controlado
- SNMP basico
- SSH orientado a consulta/diagnostico

### Fase B: Tab de camaras
- snapshot
- prueba de video
- streaming en vivo
- supervision visual operacional

---

## Requisitos funcionales clave

## 1. HTTP/HTTPS

Cada equipo debe poder definir opcionalmente:

- URL
- metodo
- timeout
- validacion de certificado
- codigo esperado
- texto esperado opcional

Esto permite saber si una interfaz esta realmente operativa y no solo si el equipo responde a ping.

## 2. Escaneo de puertos controlado

Debe existir un escaneo de puertos:

- por lista definida
- con timeout configurable
- con frecuencia configurable
- con limites de concurrencia
- con maximo de puertos por equipo

La condicion obligatoria es:

**no debe desbordarse ni saturar red, CPU o hilos.**

## 3. SNMP

Debe orientarse inicialmente a:

- lectura basica
- OIDs estandar
- uptime
- nombre
- descripcion
- interfaces
- trafico por interfaz cuando aplique

## 4. SSH

Debe comenzar como una capa segura de consulta controlada:

- lectura de datos
- comandos predefinidos
- diagnostico puntual

No como shell libre desde el dia 1.

## 5. Tab de camaras

Debe soportar, progresivamente:

- snapshot HTTP
- prueba RTSP
- MJPEG si existe
- streaming RTSP en vivo
- modo solo conectividad para camaras antiguas

---

## Requisito nuevo obligatorio: streams configurables por el host

Se incorpora como requisito formal:

### Maximo de streams simultaneos

El numero maximo de streams de camara activos en simultaneo:

- debe ser configurable desde una tab de administracion
- debe depender de la capacidad del equipo anfitrion
- debe poder fijarse al menos desde 1 stream en adelante
- debe limitar tanto la vista general como la vista ampliada si hace falta

### Motivo

El streaming en tiempo real puede:

- elevar consumo de CPU
- elevar RAM
- elevar trafico
- volver inestable la interfaz

Por eso no debe quedar hardcodeado.
Debe ser una politica administrable.

### Recomendacion de implementacion

Este parametro deberia vivir como ajuste global de sistema, por ejemplo:

- maximo de streams simultaneos
- calidad o perfil de stream preferido
- refresco de snapshots
- prioridad de stream seleccionado

---

## Requisitos no funcionales

## 1. Escalabilidad controlada

La app debe crecer sin perder estabilidad.

Eso implica:

- limitar concurrencia
- evitar hilos descontrolados
- no bloquear la UI
- desacoplar chequeos pesados del hilo principal

## 2. Seguridad

La expansion a SNMP/SSH/HTTP/camaras implica credenciales.

Por lo tanto:

- las credenciales deben almacenarse cifradas
- no deben quedar expuestas en texto plano
- deben asociarse a equipo o perfil
- deben poder rotarse

## 3. Perfilado por tipo de equipo

El usuario no deberia tener que configurar todo desde cero cada vez.

Deberian existir perfiles como:

- camara IP moderna
- camara IP basica
- NVR
- switch
- router
- host Linux
- host Windows
- totem / kiosko / controlador

## 4. Comercializacion

El producto debe permitir un modelo presentable a cliente.

Eso implica:

- branding consistente
- reportes claros
- configuracion exportable
- instalacion reproducible
- experiencia de uso entendible para soporte y operacion

---

## Vision de la Tab de Camaras

La nueva tab no debe pensarse como un VMS completo.
Debe pensarse como una capa de supervision visual operacional.

### Objetivos reales

- validar que la camara no solo esta en red
- validar que entrega imagen
- detectar rapidamente camaras caidas o congeladas
- ayudar al soporte tecnico y a la operacion

### Capas de implementacion sugeridas

#### Etapa 1
- alta de camaras
- snapshot HTTP
- prueba de RTSP
- estado por IP, web y puerto RTSP

#### Etapa 2
- stream RTSP individual en vivo
- vista ampliada
- seleccion de stream primario/secundario

#### Etapa 3
- mosaico controlado de multiples camaras
- uso del limite global de streams simultaneos
- pausa automatica o degradacion de preview segun carga

---

## Roadmap inmediato recomendado

## Paso 1
- HTTP/HTTPS
- puertos controlados

## Paso 2
- SNMP basico

## Paso 3
- modelo de perfiles por equipo

## Paso 4
- nueva tab de camaras

## Paso 5
- SSH

## Paso 6
- streaming RTSP controlado por capacidad del host

---

## Conclusión

Anvic Network Sentinel ya no debe verse solo como una herramienta personal de monitoreo.

Con el contexto de MeiPass y la oferta de servicios de ANVIC, el producto tiene una direccion clara:

**ser una plataforma de supervision tecnica y visual para instalaciones de seguridad, acceso y CCTV, comercializable como parte del servicio de la empresa.**

Ese es el marco correcto para seguir construyendo.
