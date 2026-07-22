param(
    [switch]$CleanOnly
)

$ErrorActionPreference = "Stop"

$BaseDir = (Get-Item .).FullName
$BackendV4Dir = Join-Path $BaseDir "backend_v4"
$BuildOut = Join-Path $BackendV4Dir "build"

function Clean-CompilationState {
    Write-Host "-> [Limpieza Total] Terminando subprocesos y purgando carpetas de compilación..." -ForegroundColor DarkGray
    Get-Process -Name zig, scons, chromedriver -ErrorAction SilentlyContinue | Stop-Process -Force
    if (Test-Path $BuildOut) {
        Remove-Item -Recurse -Force $BuildOut -ErrorAction SilentlyContinue
    }
}

if ($CleanOnly) {
    Clean-CompilationState
    Write-Host "-> Estado de compilación limpiado al 100%." -ForegroundColor Green
    exit 0
}

Clean-CompilationState

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Compilación Argos Guard v4.0 (Nuitka C++) " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

try {
    Set-Location $BackendV4Dir

    $NuitkaArgs = @(
        "--standalone",
        "--remove-output",
        "--windows-console-mode=disable",
        "--windows-icon-from-ico=static/icono_argos.ico",
        "--include-data-dir=templates=templates",
        "--include-data-dir=static=static",
        "--module-parameter=django-settings-module=config.settings",
        
        # Modulos de la App Monolito Modular
        "--include-package=config",
        "--include-package=apps",
        "--include-package=apps.core",
        "--include-package=apps.monitoring",
        "--include-package=apps.osint",
        "--include-package=apps.security",
        "--include-package=apps.licensing",

        # Framework Django y Servidor
        "--include-package=django",
        "--include-package=django.contrib.admin",
        "--include-package=django.contrib.auth",
        "--include-package=django.contrib.contenttypes",
        "--include-package=django.contrib.sessions",
        "--include-package=django.contrib.messages",
        "--include-package=django.contrib.staticfiles",

        # PyQt6 GUI & QWebEngine
        "--include-package=PyQt6",
        "--include-package=PyQt6.QtCore",
        "--include-package=PyQt6.QtWidgets",
        "--include-package=PyQt6.QtGui",
        "--include-package=PyQt6.QtWebEngineWidgets",
        "--include-package=PyQt6.QtWebEngineCore",
        "--include-package-data=PyQt6",

        # Automation, OSINT & Cryptography
        "--include-package=undetected_chromedriver",
        "--include-package=selenium",
        "--include-package=dns",
        "--include-package=cryptography",
        "--include-package=argon2",
        "--include-package=jwt",

        # Plugins Nuitka
        "--enable-plugin=pyqt6",
        "--enable-plugin=anti-bloat",

        "--no-deployment-flag=excluded-module-usage",
        "--assume-yes-for-downloads",
        "--output-dir=build",
        "--output-filename=ArgosGuardV4.exe",
        "run_kiosk.py"
    )

    Write-Host "-> Ejecutando: python -m nuitka $($NuitkaArgs -join ' ')" -ForegroundColor DarkGray
    python -m nuitka @NuitkaArgs

    # Inclusión post-compilación de DLLs gráficas críticas (Direct3D y Software OpenGL)
    $DistFolder = Join-Path $BuildOut "run_kiosk.dist"
    if (Test-Path $DistFolder) {
        $PyQt6Bin = "C:\Users\BetoRock Toledo\AppData\Local\Programs\Python\Python313\Lib\site-packages\PyQt6\Qt6\bin"
        $CriticalDlls = @("d3dcompiler_47.dll", "opengl32sw.dll", "msvcp140_1.dll", "msvcp140_2.dll")
        foreach ($dll in $CriticalDlls) {
            $src = Join-Path $PyQt6Bin $dll
            if (Test-Path $src) {
                Copy-Item -Path $src -Destination $DistFolder -Force
                Write-Host "-> DLL Copiada: $dll" -ForegroundColor DarkGray
            }
        }
    }

    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n========================================" -ForegroundColor Cyan
        Write-Host " Compilación Exitosa v4.0 en backend_v4/build/run_kiosk.dist " -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Cyan
    } else {
        Clean-CompilationState
        Write-Error "La compilación Nuitka falló."
    }
}
catch {
    Clean-CompilationState
    Write-Error "Fallo durante la compilación: $_"
}
finally {
    Set-Location $BaseDir
}
