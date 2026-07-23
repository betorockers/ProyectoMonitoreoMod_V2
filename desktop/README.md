# Desktop Shell

Argos Guard Enterprise v3.6.2 se distribuira como aplicacion de escritorio hibrida.

## Principio

- La UI Next.js es una consola embebida, no un sitio web publico.
- FastAPI corre como servicio local controlado por el proceso de escritorio.
- La comunicacion entre UI y backend debe usar loopback (`127.0.0.1`) y puertos internos.
- El empaquetado final debe iniciar, vigilar y cerrar el backend junto con la ventana principal.

## Wrapper recomendado

La Fase 1 mantiene la UI y API separadas para desarrollo rapido. En Fase 3/4 se debe elegir el shell:

- **Tauri:** preferido por peso bajo y binario nativo.
- **Electron:** opcion viable si se prioriza ecosistema Node y tooling amplio.
- **PyWebView:** opcion compatible si se quiere controlar la app desde Python/Nuitka.

Decision provisional: mantener compatibilidad con Tauri y PyWebView hasta validar integracion de video y mapas.
