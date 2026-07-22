# Arquitectura Fase 1

## Restriccion principal

Argos Guard Enterprise v3.6.2 es una aplicacion de escritorio hibrida. Next.js no se usara
como producto web publico ni como despliegue SaaS: sera la capa visual embebida
en una ventana nativa. FastAPI correra en local y sera controlado por el shell
de escritorio.

## Backend

El backend queda separado en capas:

- `domain`: entidades y contratos puros.
- `application`: casos de uso y orquestacion de monitoreo.
- `infrastructure`: probes de red y adaptadores concretos.
- `presentation`: API HTTP y WebSocket.

La concurrencia combina `AsyncIO` para orquestacion no bloqueante y `ThreadPoolExecutor`
para operaciones potencialmente bloqueantes como DNS, socket connect y resoluciones de red.

## Frontend

Next.js usa App Router bajo `src/app`. La primera pantalla es el panel operativo local,
no una landing ni una pagina web comercial:

- banda superior de estado tactico;
- panel principal de nodos/mapa;
- telemetria lateral;
- registro de eventos.

## Siguiente corte tecnico

1. Persistir configuracion de nodos.
2. Emitir snapshots por WebSocket.
3. Definir el proceso supervisor de escritorio que levanta/cierra FastAPI.
4. Normalizar assets MapCN a componentes React.

## Nota MapCN y tiles gratuitos

El repositorio `AnmolSaini16/mapcn` ofrece componentes React sobre MapLibre GL
con marcadores, rutas y controles. Antes de integrarlo por completo hay que definir
el proveedor de tiles: el README del proyecto indica que sus basemaps CARTO pueden
requerir licencia Enterprise para uso comercial.

Decision actual: usar `maplibre-gl` directamente con raster tiles gratuitos de
OpenStreetMap (`https://tile.openstreetmap.org/{z}/{x}/{y}.png`) y atribucion
visible. No se usan tiles CARTO ni proveedores con token/licencia comercial.

Restriccion: los tiles publicos de OpenStreetMap son para visualizacion interactiva
normal. No se debe implementar descarga masiva, prefetch de regiones ni modo offline
usando `tile.openstreetmap.org`. Para offline enterprise, el proyecto debe servir
tiles propios o un proveedor que lo permita explicitamente.
