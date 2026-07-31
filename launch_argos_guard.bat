@echo off
setlocal

set "BASE_DIR=%~dp0"
cd /d "%BASE_DIR%"

echo [INFO] Este lanzador se mantiene solo por compatibilidad.
echo [INFO] Redirigiendo a Anvic Network Sentinel...
call "%BASE_DIR%launch_anvic_network_sentinel.bat"
exit /b %ERRORLEVEL%
