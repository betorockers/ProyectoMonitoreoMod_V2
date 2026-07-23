$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " INICIANDO ARGOS GUARD DEV DESKTOP MODE" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# ── [0/4] Matar procesos zombies que puedan bloquear puertos o la DB ─────────
Write-Host "[0/4] Limpiando procesos zombie (Python/Node)..." -ForegroundColor Magenta
Get-Process -Name "python"   -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process -Name "python3"  -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process -Name "node"     -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1   # Dar tiempo al SO para liberar handles de archivos

# ── [1/4] Limpiar base de datos ───────────────────────────────────────────────
Write-Host "[1/4] Limpiando base de datos para entorno limpio (Setup)..." -ForegroundColor Yellow
Remove-Item -Force "$PSScriptRoot\backend\argos_guard.db" -ErrorAction SilentlyContinue

# ── [2/4] Iniciar Next.js ─────────────────────────────────────────────────────
Write-Host "[2/4] Iniciando Next.js (Frontend)..." -ForegroundColor Yellow
$frontendProcess = Start-Process -FilePath "pnpm.cmd" `
    -ArgumentList "run dev" `
    -WorkingDirectory "$PSScriptRoot\frontend" `
    -PassThru -WindowStyle Hidden

# ── [3/4] Iniciar FastAPI ─────────────────────────────────────────────────────
Write-Host "[3/4] Iniciando FastAPI (Backend)..." -ForegroundColor Yellow
$backendProcess = Start-Process -FilePath "$PSScriptRoot\backend\ArgosEnv\Scripts\python.exe" `
    -ArgumentList "-m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" `
    -WorkingDirectory "$PSScriptRoot\backend" `
    -PassThru -WindowStyle Hidden

Start-Sleep -Seconds 5

# ── [4/4] Levantar ventana PyQt6 ──────────────────────────────────────────────
Write-Host "[4/4] Levantando Ventana Nativa (PyQt6)..." -ForegroundColor Green
Set-Location "$PSScriptRoot\backend"
& "$PSScriptRoot\backend\ArgosEnv\Scripts\python.exe" run_dev_desktop.py

# ── Apagado limpio ────────────────────────────────────────────────────────────
Write-Host "Cerrando servidores de desarrollo..." -ForegroundColor Yellow
Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
Stop-Process -Id $backendProcess.Id  -Force -ErrorAction SilentlyContinue

# Segunda pasada: asegurar que no queden procesos huerfanos
Get-Process -Name "python" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process -Name "node"   -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "Apagado completo." -ForegroundColor Green
