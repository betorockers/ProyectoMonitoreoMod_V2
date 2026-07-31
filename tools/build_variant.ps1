param(
    [ValidateSet("commercial", "demo")]
    [string]$Profile = "commercial"
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$profileSource = Join-Path $root "build_profiles\$Profile.json"
$profileTarget = Join-Path $root "build_profile.json"
$pythonExe = Join-Path $root "monitorEnv\Scripts\python.exe"
$iscc = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

if (-not (Test-Path $profileSource)) {
    throw "No se encontro el perfil de build: $profileSource"
}

if (-not (Test-Path $pythonExe)) {
    throw "No se encontro el interprete de build: $pythonExe"
}

$profile = Get-Content $profileSource -Raw | ConvertFrom-Json
$originalProfile = if (Test-Path $profileTarget) { Get-Content $profileTarget -Raw } else { $null }

try {
    Copy-Item $profileSource $profileTarget -Force

    & $pythonExe -m PyInstaller --noconfirm --clean .\AnvicNetworkSentinel.spec
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller finalizo con codigo $LASTEXITCODE"
    }

    $appName = if ($Profile -eq "demo") { "Anvic Network Sentinel Demo" } else { "Anvic Network Sentinel" }
    $outputBase = if ($Profile -eq "demo") { "Instalador_Anvic_Network_Sentinel_Demo_v2.2.1" } else { "Instalador_Anvic_Network_Sentinel_v2.2.1" }
    $registryRoot = if ($Profile -eq "demo") { "Software\\ANVIC\\AnvicNetworkSentinelDemo" } else { "Software\\ANVIC\\AnvicNetworkSentinel" }
    $appId = if ($Profile -eq "demo") { "{{B3C4D5E6-F7A8-9012-BCDE-F1234567890A}" } else { "{{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}" }
    $enableLicenseWizard = if ($profile.require_license_activation) { "yes" } else { "no" }

    $innoArgs = @(
        "/DMyAppName=$appName",
        "/DMyOutputBaseFilename=$outputBase",
        "/DMyAppRegistryRoot=$registryRoot",
        "/DMyAppId=$appId",
        "/DEnableLicenseWizard=$enableLicenseWizard",
        ".\installer.iss"
    )
    & $iscc @innoArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup finalizo con codigo $LASTEXITCODE"
    }
}
finally {
    if ($null -ne $originalProfile) {
        Set-Content -Path $profileTarget -Value $originalProfile -Encoding UTF8
    } else {
        Copy-Item (Join-Path $root "build_profiles\commercial.json") $profileTarget -Force
    }
}
