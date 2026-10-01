@echo off
title Generador de Parches Industriales - Anvic Network Sentinel
color 0B

echo ======================================================================
echo       ANVIC NETWORK SENTINEL - HERRAMIENTA INDUSTRIAL DE PARCHES
echo                   BetoGraf_inc (c) 2026 - Hotfix Builder
echo ======================================================================
echo.
echo Este proceso ejecutara los siguientes pasos de grado industrial:
echo   1. Certificacion de Integridad: Corre la suite completa de pruebas unitarias.
echo   2. Compilacion Diferencial: Reutiliza cache de PyInstaller (sin compilar librerias pesadas).
echo   3. Generacion de Manifiesto SHA-256 de integridad criptografica.
echo   4. Construccion de Instalador Ligero (.exe) con Inno Setup (3-8 MB).
echo   5. Empaquetado Portable Desatendido (.zip) con script de instalacion y Rollback.
echo   6. Firma digital Authenticode con Timestamp RFC 3161.
echo.
echo [GARANTIA SAGRADA DE DATOS]
echo   Este parche NO BORRA NI MODIFICA:
echo     - anvic_monitor.db (Historial y mediciones de la red)
echo     - equipos_guardados.json.enc (Equipos registrados)
echo     - users.json.enc (Usuarios y roles)
echo     - anvic_master.key ni licencias activas
echo.
echo Presione cualquier tecla para iniciar el generador o cierre esta ventana.
pause >nul

echo.
echo [PASO 0] Activando entorno de ejecucion...
if exist "monitorEnv\Scripts\activate.bat" (
    call "monitorEnv\Scripts\activate.bat"
    echo   [OK] Entorno virtual monitorEnv activado.
) else (
    echo   [ADVERTENCIA] No se encontro monitorEnv. Usando Python del sistema.
)

echo.
echo [PASO 1] Ejecutando script orquestador de parches...
python build_patch.py %*

echo.
echo ======================================================================
if %errorlevel% neq 0 (
    color 0C
    echo  [ERROR] La generacion del parche no pudo completarse.
    echo  Revise la salida anterior para corregir el incidente.
) else (
    color 0A
    echo  [EXITO] PARCHE GENERADO CORRECTAMENTE.
    echo  Los artefactos listos para desplegar estan en la carpeta: Output\
)
echo ======================================================================
echo.
pause
