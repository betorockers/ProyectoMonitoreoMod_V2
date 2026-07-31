# Mapa Comercial de Tabs - Anvic Network Sentinel

## Jerarquia principal recomendada

- `Operacion en Vivo`
  - objetivo: monitoreo en tiempo real de equipos, estados y disponibilidad

- `Historial Operacional`
  - objetivo: eventos, desconexiones, disponibilidad y trazabilidad historica

- `Supervision Visual`
  - objetivo: gestion de camaras, snapshots, pruebas RTSP y streaming gradual

- `Centro de Soporte`
  - objetivo: diagnostico tecnico, soporte local y validacion de red/instalaciones

- `Administracion`
  - objetivo: usuarios, configuracion operativa y parametros globales del sistema

## Estructura interna de Centro de Soporte

### `Red e Instalaciones`
- `Resumen de Red`
  - ping, tracert, lookup, HTTP/HTTPS, puertos, SNMP, SSH
- `Auditoria Tecnica`
  - contenedor lateral para analisis complementario
- `Inventario ARP`
  - visibilidad de vecinos y resolucion IP/MAC
- `Sesiones de Red`
  - conexiones locales observadas desde el host Sentinel

### `Estado del Puesto`
- `Resumen del Host`
  - hostname, IP local, MAC, gateway y DNS
- `Recuperacion Tecnica`
  - flushdns, renew, release y acciones rapidas de recuperacion
- `Servicios del Sistema`
  - servicios criticos del host donde corre Sentinel

## Criterio de producto

- `Operacion en Vivo` y `Supervision Visual` son la cara operativa del producto.
- `Centro de Soporte` es un modulo tecnico de apoyo, muy valioso para soporte en terreno y NOC.
- `Administracion` concentra parametros globales y evita mezclar configuracion con monitoreo.
- `Estado del Puesto` siempre debe comunicar que se refiere al host local.
- `Red e Instalaciones` siempre debe comunicar que apunta al entorno remoto o a la red operativa.

## Regla de oro de UX

No mezclar en la misma zona acciones sobre el host local con chequeos remotos sin una separacion visual clara.
