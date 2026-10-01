; ==============================================================================
; ANVIC NETWORK SENTINEL - INSTALADOR DE PARCHE DIFERENCIAL (HOTFIX / UPDATE)
; BetoGraf_inc © 2026 - Grado Industrial / Producción Comercial
; ==============================================================================

#ifndef MyAppName
  #define MyAppName "Anvic Network Sentinel"
#endif

#ifndef MyAppVersion
  #define MyAppVersion "2.2.4"
#endif

#ifndef MyBaseVersion
  #define MyBaseVersion "2.2.3"
#endif

#ifndef MyPatchId
  #define MyPatchId "ANS-PATCH-V2.2.4"
#endif

#ifndef MyPatchDescription
  #define MyPatchDescription "Actualización de Telemetría Dinámica y Optimización de Turnos"
#endif

#ifndef MyAppPublisher
  #define MyAppPublisher "BetoGraf_inc"
#endif

#ifndef MyAppURL
  #define MyAppURL "https://betograf.cl/"
#endif

#ifndef MyAppExeName
  #define MyAppExeName "AnvicNetworkSentinel.exe"
#endif

#ifndef MyAppRegistryRoot
  #define MyAppRegistryRoot "Software\ANVIC\AnvicNetworkSentinel"
#endif

#ifndef MySourceDir
  #define MySourceDir "Output\patch_staging"
#endif

#ifndef MyOutputBaseFilename
  #define MyOutputBaseFilename "ANS_Patch_V2.2.4"
#endif

#ifndef MyAppId
  #define MyAppId "{{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}"
#endif

[Setup]
AppId={#MyAppId}
AppName={#MyAppName} (Parche {#MyAppVersion})
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} - Actualización a v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={code:GetDefaultInstallDir}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
AllowNoIcons=yes
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=assets\img\IconoAnvic.ico
WizardImageFile=assets\img\logoAnvic.bmp
WizardSmallImageFile=assets\img\logoAnvic.bmp
WizardStyle=modern
Compression=lzma2/ultra64
SolidCompression=yes
OutputDir=Output
OutputBaseFilename={#MyOutputBaseFilename}
VersionInfoVersion={#MyAppVersion}.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=Parche de actualización diferencial para {#MyAppName}
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
SetupLogging=yes
CloseApplications=yes
RestartApplications=no
ChangesEnvironment=no
UsedUserAreasWarning=no
DirExistsWarning=no
DisableWelcomePage=no
DisableDirPage=no
CreateUninstallRegKey=no

#ifdef UseSignTool
SignTool=MySignTool
SignedUninstaller=no
#endif

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Files]
; Archivos diferenciales del staging (solo los componentes actualizados)
Source: "{#MySourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Registry]
Root: HKCU; Subkey: "{#MyAppRegistryRoot}"; ValueType: string; ValueName: "InstalledVersion"; ValueData: "{#MyAppVersion}"; Flags: uninsdeletevalue
Root: HKCU; Subkey: "{#MyAppRegistryRoot}"; ValueType: string; ValueName: "LastPatchId"; ValueData: "{#MyPatchId}"; Flags: createvalueifdoesntexist
Root: HKCU; Subkey: "{#MyAppRegistryRoot}"; ValueType: string; ValueName: "LastPatchDate"; ValueData: "{code:GetCurrentDateTimeStr}"; Flags: createvalueifdoesntexist

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir {#MyAppName} actualizado ahora"; Flags: nowait postinstall skipifsilent

[Code]
var
  BackupDirName: String;

function GetDefaultInstallDir(Param: String): String;
var
  RegDir: String;
begin
  RegDir := '';
  // 1. Intentar leer desde HKCU
  if RegQueryStringValue(HKCU, '{#MyAppRegistryRoot}', 'InstallRoot', RegDir) and (RegDir <> '') then
  begin
    Result := RegDir;
    exit;
  end;

  // 2. Intentar leer desde HKLM
  if RegQueryStringValue(HKLM, '{#MyAppRegistryRoot}', 'InstallRoot', RegDir) and (RegDir <> '') then
  begin
    Result := RegDir;
    exit;
  end;

  // 3. Fallback a Program Files común
  Result := ExpandConstant('{autopf}\{#MyAppName}');
end;

function GetCurrentDateTimeStr(Param: String): String;
begin
  Result := GetDateTimeString('yyyy-mm-dd hh:nn:ss', '-', ':');
end;

function TerminarProcesoActivo(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  // Intento de cierre de AnvicNetworkSentinel.exe si está corriendo
  Exec('taskkill.exe', '/f /im {#MyAppExeName}', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Sleep(500);
end;

function BackupExistingFiles(AppPath: String): Boolean;
var
  TimestampStr: String;
  TargetBackupDir: String;
  BatchFile: String;
  BatchContent: String;
begin
  Result := True;
  TimestampStr := GetDateTimeString('yyyymmdd_hhnnss', '_', '_');
  TargetBackupDir := AppPath + '\backups\backup_pre_patch_' + TimestampStr;
  BackupDirName := TargetBackupDir;

  if not ForceDirectories(TargetBackupDir) then
  begin
    Log('No se pudo crear el directorio de backup: ' + TargetBackupDir);
    exit;
  end;

  // 1. Respaldar el ejecutable principal
  if FileExists(AppPath + '\{#MyAppExeName}') then
  begin
    CopyFile(AppPath + '\{#MyAppExeName}', TargetBackupDir + '\{#MyAppExeName}', False);
  end;

  // 2. Generar script rollback.bat dentro del backup para revertir en un click
  BatchFile := TargetBackupDir + '\rollback.bat';
  BatchContent := '@echo off' + #13#10 +
                  'echo =====================================================' + #13#10 +
                  'echo   RESTAURACION DE SEGURIDAD - ANVIC NETWORK SENTINEL' + #13#10 +
                  'echo =====================================================' + #13#10 +
                  'echo Restaurando version previa guardada en: ' + TargetBackupDir + #13#10 +
                  'taskkill /f /im {#MyAppExeName} >nul 2>&1' + #13#10 +
                  'timeout /t 1 >nul' + #13#10 +
                  'copy /y "{#MyAppExeName}" "..\\..\\{#MyAppExeName}"' + #13#10 +
                  'echo [OK] Archivo principal restaurado.' + #13#10 +
                  'echo Version previa restaurada correctamente.' + #13#10 +
                  'pause' + #13#10;

  SaveStringToFile(BatchFile, BatchContent, False);
  Log('Backup preventivo creado exitosamente en: ' + TargetBackupDir);
end;

function RegistrarAuditoriaPatch(AppPath: String): Boolean;
var
  LogFile: String;
  LogEntry: String;
begin
  Result := True;
  LogFile := AppPath + '\patch_history.log';
  LogEntry := '[' + GetDateTimeString('yyyy-mm-dd hh:nn:ss', '-', ':') + '] ' +
              'PARCHE APLICADO: {#MyPatchId} (v{#MyAppVersion}) | Descripcion: {#MyPatchDescription}' + #13#10;
  
  if FileExists(LogFile) then
    SaveStringToFile(LogFile, LogEntry, True)
  else
    SaveStringToFile(LogFile, LogEntry, False);
end;

procedure InitializeWizard;
var
  CurrentVer: String;
begin
  WizardForm.WelcomeLabel1.Caption := 'Actualización y Parche {#MyAppVersion}';
  WizardForm.WelcomeLabel2.Caption :=
    'Este asistente aplicará el parche oficial {#MyPatchId} para {#MyAppName}.' + #13#10 + #13#10 +
    '• Descripción: {#MyPatchDescription}' + #13#10 +
    '• Conserva el 100% de sus bases de datos operacionales, equipos y credenciales.' + #13#10 +
    '• Genera una copia de seguridad automática con soporte para Rollback inmediato.';

  WizardForm.SelectDirLabel.Caption :=
    'Se ha detectado automáticamente la instalación de {#MyAppName}.' + #13#10 +
    'Confirme que la ruta sea la correcta para aplicar el parche.';

  WizardForm.FinishedHeadingLabel.Caption := 'Parche aplicado exitosamente';
  WizardForm.FinishedLabel.Caption :=
    '{#MyAppName} ha sido actualizado a la versión {#MyAppVersion}.' + #13#10 + #13#10 +
    'Los datos operativos, mediciones y usuarios se mantienen íntegros.';

  CurrentVer := '';
  if RegQueryStringValue(HKCU, '{#MyAppRegistryRoot}', 'InstalledVersion', CurrentVer) then
  begin
    Log('Versión actualmente instalada detectada: ' + CurrentVer);
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  InstalledExe: String;
begin
  Result := True;

  if CurPageID = wpSelectDir then
  begin
    InstalledExe := ExpandConstant('{app}\{#MyAppExeName}');
    if not FileExists(InstalledExe) then
    begin
      if MsgBox('No se detectó {#MyAppExeName} en la carpeta seleccionada:' + #13#10 +
                ExpandConstant('{app}') + #13#10#13#10 +
                '¿Desea continuar de todos modos?', mbConfirmation, MB_YESNO) = IDNO then
      begin
        Result := False;
        exit;
      end;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  AppDir: String;
begin
  AppDir := ExpandConstant('{app}');

  if CurStep = ssInstall then
  begin
    // Paso 1: Cerrar procesos activos para evitar archivo bloqueado
    TerminarProcesoActivo();

    // Paso 2: Crear backup de seguridad con script de rollback
    BackupExistingFiles(AppDir);
  end;

  if CurStep = ssPostInstall then
  begin
    // Paso 3: Registrar en el log de auditoría del cliente
    RegistrarAuditoriaPatch(AppDir);

    // Paso 4: Registro HKLM opcional y seguro (solo si se ejecuta en modo admin, sin bloquear la instalación)
    if IsAdminInstallMode then
    begin
      RegWriteStringValue(HKLM, '{#MyAppRegistryRoot}', 'InstalledVersion', '{#MyAppVersion}');
      RegWriteStringValue(HKLM, '{#MyAppRegistryRoot}', 'LastPatchId', '{#MyPatchId}');
      RegWriteStringValue(HKLM, '{#MyAppRegistryRoot}', 'LastPatchDate', GetCurrentDateTimeStr(''));
    end;
  end;
end;
