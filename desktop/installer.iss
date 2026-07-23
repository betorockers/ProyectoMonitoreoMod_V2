[Setup]
AppName=Argos Guard Enterprise
AppVersion=3.6.5
DefaultDirName={autopf}\ArgosGuardEnterprise
DefaultGroupName=Argos Guard Enterprise
OutputDir=..\dist
OutputBaseFilename=ArgosGuard_Installer_v3.6.5

PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=commandline

Compression=lzma
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

AppPublisher=Betograf
AppPublisherURL=https://betograf.cl
AppSupportURL=mailto:soporte@betograf.cl
LicenseFile=eula.txt
SetupIconFile=..\frontend\public\icono_argos.ico
WizardStyle=modern dark
WizardImageFile=cyberpunk_side.bmp
WizardSmallImageFile=..\frontend\public\icono_argos.bmp

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Files]
Source: "..\backend\build\run_desktop.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dependencies\vc_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall ignoreversion
Source: "dependencies\chrome_installer.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall ignoreversion
; Despliegue autocontenido de librerias C++ runtime en el directorio de la aplicacion
Source: "C:\Windows\System32\vcruntime140.dll"; DestDir: "{app}"; Flags: ignoreversion uninsneveruninstall
Source: "C:\Windows\System32\vcruntime140_1.dll"; DestDir: "{app}"; Flags: ignoreversion uninsneveruninstall
Source: "C:\Windows\System32\msvcp140.dll"; DestDir: "{app}"; Flags: ignoreversion uninsneveruninstall

[Icons]
Name: "{group}\Argos Guard Enterprise"; Filename: "{app}\ArgosGuard.exe"
Name: "{commondesktop}\Argos Guard Enterprise"; Filename: "{app}\ArgosGuard.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Run]
Filename: "{tmp}\vc_redist.x64.exe"; Parameters: "/passive /norestart"; Check: NeedVC; StatusMsg: "Instalando C++ Runtime 2015-2022..."
Filename: "{tmp}\chrome_installer.exe"; Parameters: "/silent /install"; Check: NeedChrome; StatusMsg: "Instalando Google Chrome Engine..."
Filename: "{app}\ArgosGuard.exe"; Description: "Ejecutar Argos Guard Enterprise"; Flags: nowait postinstall skipifsilent

[InstallDelete]
Type: filesandordirs; Name: "{app}"
Type: filesandordirs; Name: "{localappdata}\ArgosGuardEnterprise\*.log"

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
Type: filesandordirs; Name: "{localappdata}\ArgosGuardEnterprise"
Type: filesandordirs; Name: "{userappdata}\ArgosGuardEnterprise"
Type: filesandordirs; Name: "{localappdata}\Argos Guard Enterprise"
Type: filesandordirs; Name: "{localappdata}\QtWebEngine"
Type: filesandordirs; Name: "{localappdata}\Temp\argos_uc_*"
Type: filesandordirs; Name: "{localappdata}\Temp\uc_*"

[Code]
function NeedVC(): Boolean;
var
  RegKey: string;
  Installed: Cardinal;
begin
  RegKey := 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64';
  if RegQueryDWordValue(HKEY_LOCAL_MACHINE, RegKey, 'Installed', Installed) and (Installed = 1) then
  begin
    Result := False;
    Exit;
  end;

  // Verificación física estricta de DLLs en System32 como fallback
  Result := not (FileExists(ExpandConstant('{sys}\vcruntime140.dll')) and 
                 FileExists(ExpandConstant('{sys}\vcruntime140_1.dll')) and 
                 FileExists(ExpandConstant('{sys}\msvcp140.dll')));
end;

function NeedChrome(): Boolean;
var
  UninstallKey: string;
  ChromeInstalled: Boolean;
begin
  UninstallKey := 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Google Chrome';
  ChromeInstalled := RegKeyExists(HKEY_LOCAL_MACHINE, UninstallKey) or RegKeyExists(HKEY_CURRENT_USER, UninstallKey);
  
  if not ChromeInstalled then
  begin
    ChromeInstalled := FileExists(ExpandConstant('{pf}\Google\Chrome\Application\chrome.exe')) or
              FileExists(ExpandConstant('{pf32}\Google\Chrome\Application\chrome.exe')) or
              FileExists(ExpandConstant('{localappdata}\Google\Chrome\Application\chrome.exe')) or
              FileExists('C:\Program Files\Google\Chrome\Application\chrome.exe') or
              FileExists('C:\Program Files (x86)\Google\Chrome\Application\chrome.exe');
  end;
  
  Result := not ChromeInstalled;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    // Forzar el cierre de cualquier proceso activo antes de desinstalar
    Exec('taskkill.exe', '/F /IM ArgosGuard.exe /T', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    Exec('taskkill.exe', '/F /IM QtWebEngineProcess.exe /T', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    Exec('taskkill.exe', '/F /IM chromedriver.exe /T', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
  
  if CurUninstallStep = usPostUninstall then
  begin
    // 1. Purga completa de directorios de datos y cachés (Zero-Trace)
    DelTree(ExpandConstant('{app}'), True, True, True);
    DelTree(ExpandConstant('{localappdata}\ArgosGuardEnterprise'), True, True, True);
    DelTree(ExpandConstant('{userappdata}\ArgosGuardEnterprise'), True, True, True);
    DelTree(ExpandConstant('{localappdata}\Argos Guard Enterprise'), True, True, True);
    DelTree(ExpandConstant('{localappdata}\QtWebEngine'), True, True, True);
    
    // 2. Eliminación de claves de registro
    RegDeleteKeyIncludingSubkeys(HKEY_CURRENT_USER, 'Software\ArgosGuardEnterprise');
    RegDeleteKeyIncludingSubkeys(HKEY_LOCAL_MACHINE, 'SOFTWARE\ArgosGuardEnterprise');
    
    // 3. Purga desatendida de temporales OSINT y registros Prefetch en Windows Host
    Exec('powershell.exe', '-ExecutionPolicy Bypass -Command "Remove-Item -Path $env:TEMP\argos_uc_* -Recurse -Force -ErrorAction SilentlyContinue; Remove-Item -Path $env:WINDIR\Prefetch\ARGOSGUARD*.pf -Force -ErrorAction SilentlyContinue"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
end;

