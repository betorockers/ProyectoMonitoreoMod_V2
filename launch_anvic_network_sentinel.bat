@echo off
title Anvic Network Sentinel v2.2 - Lanzador
setlocal

set "BASE_DIR=%~dp0"
cd /d "%BASE_DIR%"

echo ======================================================
echo    Anvic Network Sentinel v2.2 - Iniciando...
echo ======================================================
echo Directorio: %BASE_DIR%
echo.

if not exist "monitorEnv\Scripts\activate" (
    echo [ERROR] No se encontro el entorno virtual en: %BASE_DIR%monitorEnv
    echo Por favor, asegurese de que la carpeta monitorEnv este presente.
    pause
    exit /b
)

echo [+] Activando entorno virtual...
call monitorEnv\Scripts\activate

echo [+] Ejecutando aplicacion...
python main.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [!] La aplicacion se cerro con un error (Codigo: %ERRORLEVEL%)
    pause
)

deactivate
exit
