[Setup]
AppId={{C4A9F210-9E1D-4B8A-A734-5821F23A8C74}
AppName=Argos Guard Enterprise v4.0
AppVersion=4.0.0
AppVerName=Argos Guard Enterprise v4.0.0
DefaultDirName={autopf}\ArgosGuardEnterpriseV4
DefaultGroupName=Argos Guard Enterprise v4.0
OutputDir=..\dist
OutputBaseFilename=ArgosGuard_Installer_v4.0.0

PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=commandline

Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

AppPublisher=Betograf.cl
AppPublisherURL=https://betograf.cl
AppSupportURL=mailto:soporte@betograf.cl
AppUpdatesURL=https://github.com/betorockers/ProyectoMonitoreoMod_V2/releases
LicenseFile=eula.txt
SetupIconFile=icono_argos.ico
UninstallDisplayIcon={app}\ArgosGuardV4.exe
WizardImageFile=cyberpunk_side.bmp
WizardSmallImageFile=icono_argos.bmp
WizardStyle=modern dark

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Files]
Source: "..\backend_v4\build\run_kiosk.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "C:\Windows\System32\vcruntime140.dll"; DestDir: "{app}"; Flags: ignoreversion uninsneveruninstall
Source: "C:\Windows\System32\vcruntime140_1.dll"; DestDir: "{app}"; Flags: ignoreversion uninsneveruninstall
Source: "C:\Windows\System32\msvcp140.dll"; DestDir: "{app}"; Flags: ignoreversion uninsneveruninstall

[Icons]
Name: "{group}\Argos Guard Enterprise v4.0"; Filename: "{app}\ArgosGuardV4.exe"
Name: "{commondesktop}\Argos Guard Enterprise v4.0"; Filename: "{app}\ArgosGuardV4.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Run]
Filename: "{app}\ArgosGuardV4.exe"; Description: "Ejecutar Argos Guard Enterprise v4.0"; Flags: nowait postinstall skipifsilent

[InstallDelete]
Type: filesandordirs; Name: "{app}"
Type: filesandordirs; Name: "{localappdata}\ArgosGuardEnterpriseV4\*.log"

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
Type: filesandordirs; Name: "{localappdata}\ArgosGuardEnterpriseV4"
Type: filesandordirs; Name: "{userappdata}\ArgosGuardEnterpriseV4"
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
              FileExists(ExpandConstant('{localappdata}\Google\Chrome\Application\chrome.exe'));
  end;
  Result := not ChromeInstalled;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    Exec('taskkill.exe', '/F /IM ArgosGuardV4.exe /T', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    Exec('taskkill.exe', '/F /IM QtWebEngineProcess.exe /T', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    Exec('taskkill.exe', '/F /IM chromedriver.exe /T', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
  
  if CurUninstallStep = usPostUninstall then
  begin
    DelTree(ExpandConstant('{app}'), True, True, True);
    DelTree(ExpandConstant('{localappdata}\ArgosGuardEnterpriseV4'), True, True, True);
    DelTree(ExpandConstant('{userappdata}\ArgosGuardEnterpriseV4'), True, True, True);
    DelTree(ExpandConstant('{localappdata}\QtWebEngine'), True, True, True);
    
    RegDeleteKeyIncludingSubkeys(HKEY_CURRENT_USER, 'Software\ArgosGuardEnterpriseV4');
    RegDeleteKeyIncludingSubkeys(HKEY_LOCAL_MACHINE, 'SOFTWARE\ArgosGuardEnterpriseV4');
    
    Exec('powershell.exe', '-ExecutionPolicy Bypass -Command "Remove-Item -Path $env:TEMP\argos_uc_* -Recurse -Force -ErrorAction SilentlyContinue; Remove-Item -Path $env:WINDIR\Prefetch\ARGOSGUARD*.pf -Force -ErrorAction SilentlyContinue"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
end;
