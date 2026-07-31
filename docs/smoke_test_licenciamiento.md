# Smoke Test de Licenciamiento

## Archivos de laboratorio

- Clave privada local de emision:
  - `g:\Proyectos\AnvicNetworkMonitorV2.1\.secrets\licensing\anvic_license_signing_private.key`
- Serial de prueba perpetua:
  - `g:\Proyectos\AnvicNetworkMonitorV2.1\.secrets\license_labs\serial_pro_perpetua.csv`
- Serial de prueba anual:
  - `g:\Proyectos\AnvicNetworkMonitorV2.1\.secrets\license_labs\serial_pro_anual.csv`
- Instalador actual:
  - `g:\Proyectos\AnvicNetworkMonitorV2.1\Output\Instalador_Anvic_Network_Sentinel_v2.2.exe`

## Prueba 1: Instalacion con licencia perpetua

1. Ejecutar el instalador.
2. En la pagina `Licencia y activacion`, copiar el serial desde el CSV `serial_pro_perpetua.csv`.
3. Completar instalacion.
4. Abrir la aplicacion.
5. Verificar que no quede bloqueada en la ventana de activacion.
6. Iniciar sesion y revisar en `Administracion > Licenciamiento`:
   - `Estado`: `valid`
   - `Edicion`: `PRO`
   - `Tipo`: `PERPETUAL`
   - `Vence`: vacio o `-`

## Prueba 2: Instalacion con licencia anual

1. Ejecutar el instalador.
2. Usar el serial desde `serial_pro_anual.csv`.
3. Completar instalacion y abrir la app.
4. Revisar en `Administracion > Licenciamiento`:
   - `Estado`: `valid`
   - `Edicion`: `PRO`
   - `Tipo`: `ANNUAL`
   - `Vence`: fecha ISO cargada en el serial

## Prueba 3: Reapertura posterior

1. Cerrar la app.
2. Abrir nuevamente.
3. Confirmar que entra directo al flujo normal sin pedir serial otra vez.

## Prueba 4: Desinstalacion y persistencia minima

1. Desinstalar la app.
2. Confirmar que se eliminan ejecutable, base de datos, configuraciones y logs.
3. Revisar que el subarbol de licenciamiento en registro siga presente:
   - `HKCU\Software\ANVIC\AnvicNetworkSentinel\Licensing`
4. Reinstalar.
5. Confirmar que el estado de licencia sigue siendo coherente con el historial local.

## Prueba 5: Serial invalido

1. Ejecutar el instalador.
2. Ingresar un serial con prefijo correcto pero alterado manualmente.
3. Completar instalacion.
4. Abrir la app.
5. Confirmar que la ventana de activacion rechaza el serial y no deja avanzar.

## Observaciones esperadas

- El instalador valida formato basico.
- La aplicacion valida firma criptografica real.
- La vinculacion al equipo se refleja en `Huella equipo`.
- La licencia se guarda localmente y sobrevive a reinicios.
- La clave privada de emision no forma parte del build ni del instalador.
