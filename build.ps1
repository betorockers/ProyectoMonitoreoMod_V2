param(
    [switch]$SkipFrontend
)

$ErrorActionPreference = "Stop"

# Directorios
$BaseDir = (Get-Item .).FullName
$FrontendDir = Join-Path $BaseDir "frontend"
$BackendDir = Join-Path $BaseDir "backend"
$FrontendOut = Join-Path $FrontendDir "out"
$BackendOut = Join-Path $BackendDir "frontend_dist"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Compilación de Argos Guard (Fase 4)  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if (-not $SkipFrontend) {
    Write-Host "`n[1/3] Construyendo Frontend (Next.js)..." -ForegroundColor Yellow
    Set-Location $FrontendDir
    # Instalar dependencias si faltan
    npm install
    # Construir exportación estática
    npm run build
    
    if (-not (Test-Path $FrontendOut)) {
        Write-Error "Fallo en compilación de Frontend: carpeta 'out' no generada."
    }
} else {
    Write-Host "`n[1/3] Omitiendo construcción de Frontend por bandera -SkipFrontend" -ForegroundColor DarkGray
}

Write-Host "`n[2/3] Moviendo archivos al Backend..." -ForegroundColor Yellow
Set-Location $BaseDir
if (Test-Path $BackendOut) {
    Remove-Item -Recurse -Force $BackendOut
}
New-Item -ItemType Directory -Path $BackendOut | Out-Null
Copy-Item -Path "$FrontendOut\*" -Destination $BackendOut -Recurse -Force
Write-Host "-> Archivos front end copiados a: $BackendOut" -ForegroundColor Green

Write-Host "`n[3/3] Ejecutando Nuitka..." -ForegroundColor Yellow
Set-Location $BackendDir

# Variables de compilación Nuitka
$NuitkaArgs = @(
    "--standalone",
    "--onefile",
    "--windows-console-mode=disable",
    "--windows-icon-from-ico=../frontend/public/icono_argos.ico",
    "--include-data-dir=frontend_dist=frontend_dist",
    # Paquetes de la app
    "--include-package=app",
    "--include-package=app.infrastructure",
    "--include-package=app.application",
    "--include-package=app.presentation",
    "--include-package=app.domain",
    # Dependencias de OSINT / Selenium
    "--include-package=undetected_chromedriver",
    "--include-package=selenium",
    "--include-package=requests",
    # Dependencias de base de datos
    "--include-package=sqlcipher3",
    # Generación de PDF
    "--include-package=fpdf",
    # Dependencias de red y FastAPI
    "--include-package=httpx",
    "--include-package=fastapi",
    "--include-package=uvicorn",
    "--include-package=slowapi",
    # Datos de paquetes necesarios (limits, slow_api, etc.)
    "--include-package-data=limits",
    "--include-package-data=fpdf",
    # Plugins de Nuitka
    "--enable-plugin=pyqt6",
    "--no-deployment-flag=excluded-module-usage",
    "--disable-plugin=anti-bloat",
    "--assume-yes-for-downloads",
    "--output-dir=build",
    "--output-filename=ArgosGuard.exe",
    "run_desktop.py"
)

Write-Host "-> Comandos: python -m nuitka $($NuitkaArgs -join ' ')" -ForegroundColor DarkGray
python -m nuitka @NuitkaArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host " Compilación Exitosa. Binario en backend/build/ArgosGuard.exe " -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
} else {
    Write-Error "La compilación con Nuitka falló."
}

Set-Location $BaseDir
