@echo off
title Compilacion Anvic Network Sentinel v2.2.3
color 0B
echo =========================================================
echo       ANVIC NETWORK SENTINEL - HERRAMIENTA DE BUILD
echo                     VERSION 2.2.3
echo =========================================================
echo.
echo Este proceso ejecutara los siguientes pasos:
echo   1. Limpieza de base de datos (BD virgen para release)
echo   2. Transpilacion con Cython para proteger el codigo
echo   3. Empaquetado de dependencias con PyInstaller
echo   4. Creacion de instalador final con Inno Setup
echo.
echo [ATENCION] Se eliminaran los siguientes archivos antes de compilar:
echo   - anvic_monitor.db          (base de datos operacional)
echo   - metricas_historial.json   (historial de metricas)
echo   - equipos_guardados.json.enc (configuracion de equipos)
echo   - users.json.enc            (usuarios registrados)
echo.
echo Presione cualquier tecla para comenzar o cierre esta ventana para cancelar.
pause >nul

echo.
echo [PASO 0] Limpiando datos de usuario para release limpio...
if exist "anvic_monitor.db" (
    del /f /q "anvic_monitor.db"
    echo   [OK] anvic_monitor.db eliminado.
) else (
    echo   [--] anvic_monitor.db no encontrado, omitiendo.
)
if exist "metricas_historial.json" (
    del /f /q "metricas_historial.json"
    echo   [OK] metricas_historial.json eliminado.
)
if exist "equipos_guardados.json.enc" (
    del /f /q "equipos_guardados.json.enc"
    echo   [OK] equipos_guardados.json.enc eliminado.
)
if exist "users.json.enc" (
    del /f /q "users.json.enc"
    echo   [OK] users.json.enc eliminado.
)

echo.
echo [PASO 1] Activando entorno virtual...
if exist "monitorEnv\Scripts\activate.bat" (
    call "monitorEnv\Scripts\activate.bat"
    echo   [OK] Entorno virtual activado.
) else (
    echo   [ADVERTENCIA] No se encontro monitorEnv. Usando Python global.
)

echo.
echo [PASO 2-4] Iniciando pipeline de compilacion...
python build_pipeline.py

echo.
echo =========================================================
if %errorlevel% neq 0 (
    color 0C
    echo  ERROR: El proceso de compilacion fallo.
    echo  Revise la salida anterior para mas detalles.
) else (
    color 0A
    echo  COMPILACION v2.2.3 FINALIZADA CON EXITO.
    echo  El instalador se encuentra en la carpeta: Output\
)
echo =========================================================
pause

