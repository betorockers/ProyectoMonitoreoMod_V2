; Script de instalacion para Anvic Network Sentinel v2.2.3
; Inno Setup moderno, per-user y con enfoque de menor friccion operativa.

#ifndef MyAppName
  #define MyAppName "Anvic Network Sentinel"
#endif
#ifndef MyAppVersion
  #define MyAppVersion "2.2.3"
#endif
#ifndef MyAppPublisher
  #define MyAppPublisher "BetoGraf_inc"
#endif
#ifndef MyAppURL
  #define MyAppURL "https://betograf.cl/"
#endif
#ifndef MyAppSupportURL
  #define MyAppSupportURL "https://betograf.cl/#contacto"
#endif
#ifndef MyAppUpdatesURL
  #define MyAppUpdatesURL "https://betograf.cl/#contacto"
#endif
#ifndef MyAppExeName
  #define MyAppExeName "AnvicNetworkSentinel.exe"
#endif
#ifndef MyAppRegistryRoot
  #define MyAppRegistryRoot "Software\\ANVIC\\AnvicNetworkSentinel"
#endif
#ifndef MyOutputBaseFilename
  #define MyOutputBaseFilename "ANS_Setup_V2.2.3"
#endif
#ifndef MyAppId
  #define MyAppId "{{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}"
#endif
#ifndef EnableLicenseWizard
  #define EnableLicenseWizard "yes"
#endif

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppSupportURL}
AppUpdatesURL={#MyAppUpdatesURL}
DefaultDirName={autopf}\{#MyAppName}
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
#ifdef UseSignTool
SignTool=MySignTool
SignedUninstaller=yes
#endif
LZMANumBlockThreads=4
SolidCompression=yes
OutputDir=Output
OutputBaseFilename={#MyOutputBaseFilename}
VersionInfoVersion=2.2.3.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=Plataforma de supervision tecnica y visual para instalaciones conectadas
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

; ── FIRMA DIGITAL AUTHENTICODE ──────────────────────────────────────────────
; Inno Setup firmara automaticamente el instalador al compilar.
; El certificado debe estar instalado antes de compilar.
; Ejecutar primero: E:\Certificados\crear_certificado_anvic.ps1 (como Admin)
;
; signtool.exe debe estar en PATH (Windows SDK 10).
; Ruta tipica: C:\Program Files (x86)\Windows Kits\10\bin\10.0.XXXXX.0\x64\
; SignTool=anvicsign
; SignedUninstaller=yes

; [SigningTool]
; anvicsign=signtool.exe sign /fd SHA256 /td SHA256 /tr http://timestamp.digicert.com /n "Anvic Network Sentinel" /a $f

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos"; Flags: unchecked

[Dirs]
Name: "{app}"; Permissions: users-modify

[Files]
Source: "installer_prereqs\VC_redist.x64.exe"; DestDir: "{tmp}"; Flags: ignoreversion deleteafterinstall
Source: "dist\AnvicNetworkSentinel\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\AnvicNetworkSentinel\_internal\_tcl_data\*"; DestDir: "{app}\_internal\_tcl_data"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\AnvicNetworkSentinel\_internal\_tk_data\*"; DestDir: "{app}\_internal\_tk_data"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\AnvicNetworkSentinel\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[InstallDelete]
Type: filesandordirs; Name: "{app}\_internal\_tcl_data"
Type: filesandordirs; Name: "{app}\_internal\_tk_data"

[Registry]
Root: HKCU; Subkey: "{#MyAppRegistryRoot}"; ValueType: string; ValueName: "InstallRoot"; ValueData: "{app}"; Flags: uninsdeletevalue
Root: HKCU; Subkey: "{#MyAppRegistryRoot}"; ValueType: string; ValueName: "InstalledVersion"; ValueData: "{#MyAppVersion}"; Flags: uninsdeletevalue
Root: HKCU; Subkey: "{#MyAppRegistryRoot}"; Flags: uninsdeletekeyifempty
Root: HKCU; Subkey: "{#MyAppRegistryRoot}\Licensing"; ValueType: string; ValueName: "StorageMode"; ValueData: "Reserved"; Flags: createvalueifdoesntexist

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{tmp}\VC_redist.x64.exe"; Parameters: "/install /quiet /norestart"; StatusMsg: "Instalando Microsoft Visual C++ Redistributable (Necesario)..."; Flags: waituntilterminated
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall add rule name=""{#MyAppName}"" dir=in action=allow program=""{app}\{#MyAppExeName}"" enable=yes profile=any"; StatusMsg: "Configurando Firewall de Windows..."; Flags: runhidden waituntilterminated
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall add rule name=""{#MyAppName}"" dir=out action=allow program=""{app}\{#MyAppExeName}"" enable=yes profile=any"; StatusMsg: "Configurando Firewall de Windows..."; Flags: runhidden waituntilterminated
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall delete rule name=""{#MyAppName}"" program=""{app}\{#MyAppExeName}"""; RunOnceId: "RemoveFirewallRule"; Flags: runhidden waituntilterminated

[UninstallDelete]
Type: files; Name: "{app}\users.json"
Type: files; Name: "{app}\users.json.enc"
Type: files; Name: "{app}\equipos_guardados.json"
Type: files; Name: "{app}\equipos_guardados.json.enc"
Type: files; Name: "{app}\runtime_sensitive_settings.json"
Type: files; Name: "{app}\runtime_sensitive_settings.json.enc"
Type: files; Name: "{app}\ssh_known_hosts"
Type: files; Name: "{app}\anvic_master.key"
Type: files; Name: "{app}\anvic_monitor.db"
Type: files; Name: "{app}\anvic_monitor.db-shm"
Type: files; Name: "{app}\anvic_monitor.db-wal"
Type: files; Name: "{app}\auditoria_usuarios.log"
Type: files; Name: "{app}\historial_log.txt"
Type: files; Name: "{app}\metricas_historial.json"
Type: files; Name: "{app}\disponibilidad_mensual.json"
Type: files; Name: "{app}\*.pdf"
Type: files; Name: "{app}\*.corrupt.*"
Type: files; Name: "{app}\*.log"
Type: dirifempty; Name: "{app}"
Type: dirifempty; Name: "{localappdata}\Programs"

[Code]
var
  LicensePage: TInputQueryWizardPage;

procedure InitializeWizard;
begin
  WizardForm.WelcomeLabel1.Caption := 'Bienvenido a la instalacion de Anvic Network Sentinel';
  WizardForm.WelcomeLabel2.Caption :=
    'Esta instalacion desplegara la plataforma de supervision tecnica y visual para monitoreo de red, diagnostico operativo y soporte de instalaciones conectadas.';
  WizardForm.SelectDirLabel.Caption :=
    'Seleccione la carpeta donde desea instalar la aplicacion. Se recomienda mantener la ruta sugerida para una operacion estable y segura.';
  WizardForm.ReadyLabel.Caption := 'Listo para instalar';
  WizardForm.FinishedHeadingLabel.Caption := 'Instalacion completada';
  WizardForm.FinishedLabel.Caption :=
    'Anvic Network Sentinel se instalo correctamente. Puede iniciar la aplicacion ahora y completar la activacion o validacion final de la licencia.';

  #if EnableLicenseWizard == "yes"
  LicensePage := CreateInputQueryPage(
    wpWelcome,
    'Licencia y activacion',
    'Ingrese su serial de activacion',
    'El serial sera entregado al primer inicio de la aplicacion para su validacion criptografica. Use el codigo completo tal como fue emitido por ANVIC.'
  );
  LicensePage.Add('Serial firmado:', False);
  #endif
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  #if EnableLicenseWizard == "yes"
  if CurPageID = LicensePage.ID then
  begin
    if Trim(LicensePage.Values[0]) = '' then
    begin
      MsgBox('Debe ingresar un serial valido para continuar con la instalacion.', mbError, MB_OK);
      Result := False;
      exit;
    end;

    if Pos('ANS1.', Trim(LicensePage.Values[0])) <> 1 then
    begin
      MsgBox('El serial no tiene el formato esperado para Anvic Network Sentinel.', mbError, MB_OK);
      Result := False;
      exit;
    end;
  end;
  #endif
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  #if EnableLicenseWizard == "yes"
  if CurStep = ssInstall then
  begin
    RegWriteStringValue(HKCU, '{#MyAppRegistryRoot}\Licensing', 'PendingSerial', Trim(LicensePage.Values[0]));
  end;
  #endif
  if CurStep = ssPostInstall then
  begin
    if FileExists(ExpandConstant('{app}\unins000.exe')) then
    begin
      CopyFile(ExpandConstant('{app}\unins000.exe'), ExpandConstant('{app}\uninstaller.exe'), False);
      CopyFile(ExpandConstant('{app}\unins000.dat'), ExpandConstant('{app}\uninstaller.dat'), False);
    end;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    if DirExists(ExpandConstant('{app}')) then
    begin
      DelTree(ExpandConstant('{app}'), False, True, True);
    end;
  end;
end;
