# Propuesta Tecnico-Comercial Definitiva
## Anvic Network Sentinel

## 1. Resumen Ejecutivo

Anvic Network Sentinel es una plataforma de supervision tecnica y visual orientada a instalaciones de seguridad, control de acceso y CCTV. Su objetivo es entregar visibilidad operacional, diagnostico tecnico, evidencia de servicio y capacidad de reaccion temprana frente a fallas en terreno.

No nace como un monitor generico de red. Nace desde una necesidad real de operacion, soporte y continuidad de servicio en instalaciones donde conviven equipos criticos como camaras LPR, totems de acceso, barreras, kioskos informativos, NVR, switches, routers y otros activos IP asociados a servicios de seguridad.

Desde la perspectiva de negocio, Sentinel encaja de manera natural en la oferta de ANVIC porque transforma capacidades tecnicas ya existentes en la empresa en una propuesta mas estandarizable, visible y comercializable. En otras palabras: permite convertir monitoreo, soporte, mantenimiento y supervision en una experiencia de servicio mas profesional, medible y demostrable ante cliente.

## 2. Contexto y Oportunidad

El punto de partida real del producto es un caso de uso operativo vinculado a instalaciones del ecosistema MeiPass, donde una instalacion tipo puede incluir:

- 2 camaras LPR
- 2 totems que comandan 2 barreras de acceso
- 1 kiosko informativo
- infraestructura de red local asociada

Ese mismo set puede repetirse en otra instalacion de la misma empresa, bajo el mismo contexto operacional, pero en ubicaciones fisicas distintas. Esto genera una necesidad concreta:

- saber si los equipos estan disponibles
- detectar caidas antes de que escalen a incidentes
- validar si un servicio responde realmente o solo responde el ping
- disponer de evidencia historica y operacional
- reducir tiempos de diagnostico y soporte

En ese escenario, Anvic Network Sentinel resuelve un problema real de operacion y soporte que ANVIC ya enfrenta como parte de sus servicios.

## 2.1 Origen y criterio de desarrollo

Anvic Network Sentinel no surge como un desarrollo externo ni como una iniciativa desconectada de la realidad operacional de la empresa.

El software fue impulsado y desarrollado desde dentro del trabajo diario por un colaborador de ANVIC que conoce de primera mano:

- las exigencias del soporte tecnico
- los puntos ciegos habituales de la operacion
- las limitaciones de las herramientas disponibles
- la necesidad de contar con una plataforma mas integrada para monitoreo, diagnostico y supervision

Esto es relevante desde una perspectiva empresarial porque el producto no parte de supuestos teoricos sobre el negocio. Parte de experiencia directa en terreno, contacto con instalaciones reales y comprension practica de las brechas que afectan la continuidad operacional y el servicio al cliente.

Dicho de forma simple: Sentinel nace porque alguien dentro de la empresa detecto que existian capacidades operativas que no estaban suficientemente cubiertas por las herramientas disponibles, y decidio convertir esa necesidad en una solucion concreta.

Lejos de ser un detalle menor, ese origen le da al producto tres ventajas importantes:

- responde a necesidades reales y no hipoteticas
- prioriza funciones con utilidad operacional comprobable
- tiene un nivel de alineacion natural con la forma en que ANVIC presta sus servicios

En terminos institucionales, esto permite presentar Sentinel como una solucion desarrollada desde conocimiento interno del negocio, con foco practico y orientacion clara a fortalecer la operacion de la empresa.

## 3. Encaje con la Oferta de ANVIC

El producto conversa directamente con la linea de servicios que ANVIC presta hoy, especialmente en los siguientes frentes:

- diseno y estructura de centrales de CCTV
- puesta en marcha y operacion
- implementacion de medidas de seguridad tecnologicas
- reparacion y mantenimiento preventivo de alarmas y CCTV
- monitoreo de instalaciones en tiempo real

La oportunidad no esta solo en "usar una app interna", sino en integrar Sentinel como habilitador de servicio para:

- monitoreo tecnico de instalaciones
- soporte preventivo y correctivo
- supervision remota de continuidad operacional
- evidencia de cumplimiento y disponibilidad
- escalamiento tecnico con mejor informacion

## 4. Definicion del Producto

### Que es

Anvic Network Sentinel es una plataforma Windows-first de supervision operacional para instalaciones de seguridad y control de acceso, capaz de combinar:

- monitoreo de disponibilidad de equipos IP
- diagnostico tecnico de conectividad y servicios
- supervision visual de camaras IP
- historial de eventos y disponibilidad
- alertas y soporte tecnico operativo

### Que no es

No busca competir de entrada como:

- SIEM
- NMS empresarial tipo Zabbix o PRTG
- VMS de CCTV completo
- consola de administracion remota total

Su propuesta de valor esta en la especializacion operacional:

**visibilidad util, enfocada y alineada a servicios de seguridad integral.**

## 5. Problema que Resuelve

Sentinel responde a una necesidad que suele repetirse en contratos de seguridad tecnologica:

- multiples equipos criticos repartidos por una o mas instalaciones
- dependencia de conectividad, web, puertos o video
- atencion reactiva por falta de visibilidad previa
- soporte tecnico basado en suposiciones y no en evidencia
- dificultad para demostrar servicio ante cliente

Con Sentinel, ANVIC puede pasar de una logica reactiva a una logica mas controlada:

- detectar
- diagnosticar
- documentar
- justificar
- intervenir

## 6. Propuesta de Valor para ANVIC

### Valor operacional

- deteccion temprana de indisponibilidades
- reduccion de tiempo de diagnostico
- mejor priorizacion de soporte
- menos dependencia de herramientas dispersas
- evidencia historica para seguimiento tecnico

### Valor comercial

- agrega una capa visible de monitoreo al servicio
- mejora la percepcion de profesionalismo
- habilita ofertas de monitoreo y mantenimiento con mas respaldo
- permite diferenciarse por capacidad de observabilidad
- facilita reportabilidad hacia cliente

### Valor estrategico

- transforma conocimiento tecnico interno en activo de empresa
- reduce dependencia de solucion artesanal no estandarizada
- abre camino a una linea propia de soporte y supervision
- fortalece la posicion de ANVIC en servicios de seguridad tecnologica

## 7. Capacidades Actuales con Valor Real

En su estado actual, Sentinel ya dispone de capacidades valiosas y alineadas a operacion real:

- monitoreo por IP y disponibilidad
- deteccion de conectado/desconectado
- historial de eventos y desconexiones
- medicion de latencia y disponibilidad
- reportes y evidencia operacional
- gestion de usuarios y control de acceso a la herramienta
- diagnostico de red desde interfaz integrada
- chequeos HTTP y HTTPS
- escaneo de puertos controlado
- SNMP basico
- SSH orientado a consulta
- configuracion de camaras
- snapshots y prueba de RTSP
- vista en vivo basada en snapshot controlado
- notificaciones Telegram opcionales configurables por instalacion

Esto ya ubica al producto por encima de un monitor basico de ping y lo acerca a una consola operativa especializada.

## 8. Arquitectura Funcional Recomendada del Producto

Para efectos de posicionamiento y usabilidad, la estructura comercial recomendada del producto queda asi:

- `Operacion en Vivo`
- `Historial Operacional`
- `Supervision Visual`
- `Centro de Soporte`
- `Administracion`

### Centro de Soporte

- `Red e Instalaciones`
  - `Resumen de Red`
  - `Auditoria Tecnica`
  - `Inventario ARP`
  - `Sesiones de Red`

- `Estado del Puesto`
  - `Resumen del Host`
  - `Recuperacion Tecnica`
  - `Servicios del Sistema`

Esta estructura separa correctamente:

- diagnostico remoto
- estado del host local
- acciones tecnicas de recuperacion

Y evita una mezcla confusa entre funciones de soporte local y monitoreo de instalaciones.

## 9. Casos de Uso Directos para ANVIC

### Caso 1: Instalaciones de control de acceso

Sentinel puede supervisar activos como:

- camaras LPR
- totems de acceso
- kioskos
- barreras
- controladores IP

Valor para ANVIC:

- verificar continuidad operacional
- detectar equipos caidos antes de una visita
- validar si el problema es red, servicio o interfaz
- documentar patrones de indisponibilidad
- escalar eventos por Telegram con identificacion clara de la instalacion afectada

### Caso 2: CCTV y supervision visual

Sentinel puede integrarse como apoyo a:

- camaras IP
- NVR
- DVR
- enlaces web de gestion
- puertos RTSP y servicios de video

Valor para ANVIC:

- validar que una camara no solo responda en red, sino que entregue imagen
- acelerar soporte tecnico
- aportar supervision visual a servicios de monitoreo

### Caso 4: Alertamiento operativo por Telegram

Sentinel puede complementar la operacion con notificaciones enviadas a Telegram cuando el administrador habilita este servicio desde la configuracion del sistema.

Valor para ANVIC:

- identificar de que instalacion proviene la alerta
- recibir aviso inmediato de caida o recuperacion
- elevar gravedad cuando un equipo supera 5 minutos desconectado
- fortalecer tiempos de reaccion en soporte y continuidad operacional

### Caso 3: Infraestructura de red y capa de soporte

Sentinel puede supervisar:

- switches
- routers
- access points
- enlaces internos

Valor para ANVIC:

- diagnostico rapido
- validacion de puertos y servicios
- lectura SNMP basica
- mejor aislamiento de incidentes

## 10. Formas de Integrarlo en los Servicios de ANVIC

### Modalidad A: Herramienta interna de operacion

Uso por equipos tecnicos y de soporte ANVIC para:

- monitoreo diario
- diagnostico remoto
- control preventivo
- soporte en terreno y postventa

Es la via de adopcion mas rapida y de menor friccion.

### Modalidad B: Componente de servicio gestionado

Incluir Sentinel como parte del servicio que ANVIC presta a clientes bajo un modelo como:

- monitoreo de instalaciones
- soporte preventivo
- continuidad operacional
- supervision remota de componentes criticos

Aqui Sentinel no se vende necesariamente como software suelto, sino como plataforma de soporte del servicio.

### Modalidad C: Valor agregado en proyectos de implementacion

Integrarlo en proyectos de:

- CCTV
- control de acceso
- seguridad tecnologica
- mantenimiento preventivo

Como componente adicional de:

- puesta en marcha
- recepcion tecnica
- monitoreo inicial
- soporte post implementacion

### Modalidad D: Linea premium o escalable de servicio

ANVIC podria estructurar niveles de servicio soportados por Sentinel, por ejemplo:

- nivel base: monitoreo de disponibilidad
- nivel medio: disponibilidad + diagnostico tecnico
- nivel avanzado: disponibilidad + diagnostico + supervision visual + reportabilidad

## 11. Diferenciadores Comerciales

Los diferenciales mas claros del producto no son solo tecnologicos, sino de enfoque:

- esta pensado desde el problema real del terreno
- combina monitoreo, soporte y supervision
- no depende de infraestructura pesada
- permite operar sobre entornos Windows y LAN sin complejidad excesiva
- puede adaptarse a instalaciones de seguridad reales
- ayuda a profesionalizar una oferta de servicio ya existente

Su mayor fuerza no es "tener muchas funciones", sino que las funciones tienen sentido juntas dentro del negocio de ANVIC.

## 12. Roadmap de Expansión con Potencial Comercial

La evolucion del producto ya acordada tiene una logica correcta:

### Capa 1: monitoreo tecnico inteligente

- HTTP/HTTPS
- puertos controlados
- SNMP basico
- SSH orientado a consulta

### Capa 2: supervision visual

- snapshot
- prueba RTSP
- video en vivo
- control de streams simultaneos

### Capa 3: madurez de producto

- perfiles por tipo de equipo
- politicas TLS configurables
- experiencia de uso mas refinada
- branding consistente
- empaquetado y despliegue estandar

### Capa 4: crecimiento futuro

- RTSP real embebido
- mosaico multi-camara
- perfiles por fabricante
- monitoreo mas profundo por tipo de equipo

## 13. Requisitos Tecnicos para Escalar con Seguridad

Si ANVIC decide adoptar Sentinel como activo serio de servicio, conviene avanzar sobre estos puntos:

- consolidar la arquitectura oficial del producto
- mantener una fuente unica de configuracion y persistencia
- fortalecer la seguridad en toda la base
- normalizar empaquetado e instalacion
- separar claramente runtime, datos y codigo fuente
- continuar con una base minima de pruebas automatizadas

Esto no contradice la estrategia comercial; al contrario, la hace viable.

## 14. Riesgos si no se Ordena Antes de Escalar

El software ya tiene valor real, pero escalarlo sin consolidacion puede generar:

- crecimiento de deuda tecnica
- comportamientos distintos entre ramas del proyecto
- dificultad de mantenimiento
- riesgos de regresion funcional
- imagen inconsistente de producto

La recomendacion no es frenar el avance, sino hacer crecer el producto con direccion y criterio.

## 15. Recomendacion Ejecutiva

La recomendacion general es avanzar con una estrategia en dos carriles:

### Carril 1: adopcion interna inmediata

Utilizar Sentinel como plataforma interna de monitoreo y soporte dentro de ANVIC, consolidando aprendizaje, casos de uso y validacion operacional.

### Carril 2: maduracion como activo comercial

Refinar posicionamiento, experiencia, arquitectura y despliegue para convertirlo en una herramienta estandar de soporte y monitoreo integrada a los servicios de la empresa.

## 16. Conclusión Final

Anvic Network Sentinel tiene condiciones reales para transformarse en un activo tecnico-comercial de ANVIC.

No parte desde una idea teorica. Parte desde una necesidad operativa concreta ya validada en terreno. Ese origen es una fortaleza enorme porque evita construir un producto vacio de negocio.

Su mejor posicion no es competir como plataforma universal de monitoreo, sino consolidarse como solucion especializada para:

- seguridad tecnologica
- control de acceso
- CCTV
- soporte tecnico operativo
- monitoreo de instalaciones en tiempo real

La oportunidad para ANVIC no es solo "tener un software propio".
La oportunidad es convertir ese software en una capa visible de valor, respaldo tecnico y diferenciacion comercial dentro de su oferta de servicios.

## 17. Decision Recomendada

Si el documento se adopta como marco oficial, la decision recomendada es:

- reconocer a Anvic Network Sentinel como linea valida de evolucion dentro del negocio
- utilizarlo primero como plataforma de soporte y monitoreo interno
- madurarlo progresivamente hasta transformarlo en componente formal de servicio comercializable

En ese escenario, Sentinel no seria solo una herramienta desarrollada para resolver un problema puntual.
Seria una pieza propia de ANVIC para fortalecer operacion, servicio, evidencia y posicionamiento.
