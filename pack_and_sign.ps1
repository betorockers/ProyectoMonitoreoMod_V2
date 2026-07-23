$ErrorActionPreference = "Stop"

$CertPath = "E:\Certificados\ArgosGuard_Cert.pfx"
$CertPass = "ArgosG@2026"
$TimestampServer = "http://timestamp.digicert.com"

# 1. Obtener el certificado desde el archivo PFX para usarlo con Set-AuthenticodeSignature
$SecurePass = ConvertTo-SecureString -String $CertPass -AsPlainText -Force
$Cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2
$Cert.Import($CertPath, $CertPass, [System.Security.Cryptography.X509Certificates.X509KeyStorageFlags]::DefaultKeySet)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Firma Digital y Empaquetado Argos Guard " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 2. Firmar el ejecutable principal de Nuitka
$ExePath = "E:\ProyectoMonitoreoMod_V2\backend\build\run_desktop.dist\ArgosGuard.exe"
if (Test-Path $ExePath) {
    Write-Host "[1/3] Firmando ejecutable principal (ArgosGuard.exe)..." -ForegroundColor Yellow
    Set-AuthenticodeSignature -FilePath $ExePath -Certificate $Cert -TimestampServer $TimestampServer
    Write-Host "-> ArgosGuard.exe firmado exitosamente." -ForegroundColor Green
} else {
    Write-Error "No se encontro $ExePath. Espera a que termine Nuitka."
}

# 3. Compilar el Instalador con Inno Setup
Write-Host "`n[2/3] Generando instalador con Inno Setup..." -ForegroundColor Yellow
# Buscar ISCC (Compilador de Inno Setup)
$IsccPath = "D:\Inno Setup 7\ISCC.exe"
if (-not (Test-Path $IsccPath)) {
    $IsccPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
}
if (-not (Test-Path $IsccPath)) {
    $IsccPath = "C:\Program Files\Inno Setup 6\ISCC.exe"
}

if (Test-Path $IsccPath) {
    $IssFile = "E:\ProyectoMonitoreoMod_V2\desktop\installer.iss"
    & $IsccPath $IssFile | Out-String
    Write-Host "-> Instalador generado en dist/ArgosGuard_Installer_v3.6.3.exe" -ForegroundColor Green
} else {
    Write-Error "No se encontro Inno Setup 6 instalado en el sistema."
}

# 4. Firmar el Instalador generado
$InstallerFile = Get-ChildItem -Path "E:\ProyectoMonitoreoMod_V2\dist\ArgosGuard_Installer_*.exe" | Sort-Object LastWriteTime -Descending | Select-Object -First 1

if ($InstallerFile) {
    $InstallerPath = $InstallerFile.FullName
    Write-Host "`n[3/3] Firmando el Instalador Final ($($InstallerFile.Name))..." -ForegroundColor Yellow
    Set-AuthenticodeSignature -FilePath $InstallerPath -Certificate $Cert -TimestampServer $TimestampServer
    Write-Host "-> Instalador ($($InstallerFile.Name)) firmado exitosamente." -ForegroundColor Green
}


Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " PROCESO COMPLETADO AL 100% " -ForegroundColor Green
Write-Host " Tu instalador esta listo en: $InstallerPath " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
