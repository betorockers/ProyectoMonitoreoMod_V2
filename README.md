# Argos Guard Enterprise v3.6.4 (Producción Congelada)


Monorepo inicial para una aplicacion de escritorio hibrida de monitoreo tactico.
No se proyecta como app web publica: la interfaz Next.js sera una consola embebida
que se comunica con un backend local FastAPI.

## Estructura

- `backend/`: API FastAPI con nucleo async y ejecucion de probes en pool de hilos.
- `frontend/`: Next.js App Router usado como UI local embebible, no como sitio web.
- `desktop/`: notas y futuro wrapper nativo de escritorio.
- `docs/`: notas tecnicas de arquitectura y decisiones de Fase 1.

## Marca

- Logo oficial: `frontend/src/img/LogoArgosGuard.png`.

## Mapas

- Motor: `maplibre-gl`.
- Tiles iniciales: OpenStreetMap raster gratuito (`https://tile.openstreetmap.org/{z}/{x}/{y}.png`).
- No se usan tiles CARTO ni proveedores con token/licencia comercial.
- El modo offline futuro requiere tiles propios o un proveedor que permita empaquetado local.

## Arranque local

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend de desarrollo:

```powershell
cd frontend
pnpm install
pnpm dev
```

La UI espera la API local en `http://127.0.0.1:8000`. En distribucion final,
el shell de escritorio debe levantar ambos procesos o servir la UI empaquetada.

## API local inicial

- `GET /api/v1/health`: estado del backend local.
- `GET /api/v1/snapshot`: targets y resultados de probes TCP.
- `GET /api/v1/streams`: catalogo inicial de camaras/streams.
- `WS /api/v1/ws/telemetry`: telemetria periodica para la consola embebida.
