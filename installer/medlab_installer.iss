; ============================================================================
; Medical Laboratory Management System — Inno Setup installer script
;
; Produces:  MedicalLaboratorySetup.exe
;
; Build with Inno Setup 6 (https://jrsoftware.org/isinfo.php):
;     ISCC.exe installer\medlab_installer.iss
;
; Prerequisite: run `pyinstaller medical_lab.spec` first, so that
; dist\MedicalLaboratory\ contains MedicalLaboratory.exe and its
; supporting files.
; ============================================================================

#define MyAppName "Medical Laboratory Management System"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Your Company Name"
#define MyAppExeName "MedicalLaboratory.exe"
#define MyAppIcon "..\assets\medical_lab.ico"
#define MyBuildDir "..\dist\MedicalLaboratory"

[Setup]
AppId={{7B7C6C6E-9F5A-4C2E-8B3E-MEDLAB0000001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist\installer
OutputBaseFilename=MedicalLaboratorySetup
SetupIconFile={#MyAppIcon}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; Standard desktop-software install flow: Next, Next, Install, Finish
; (Part 88) — no custom pages needed beyond the optional shortcut choice.
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: checkedonce

[Files]
; Entire PyInstaller onedir output — .exe, its DLLs, and bundled
; templates/static/assets — copied into the install directory.
Source: "{#MyBuildDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu shortcut (Part 79, 85)
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
; Uninstaller entry in the Start Menu group (Part 85)
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
; Desktop shortcut (Part 79, 85), only if the user kept the task checked
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Offer to launch the app immediately after Finish (Part 88, step 5-8)
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Application files are removed by the uninstaller; user data under
; %PROGRAMDATA%\MedicalLaboratoryManagementSystem is deliberately left
; in place (database, backups, reports, license) so an uninstall/
; reinstall or upgrade never destroys the lab's records. To fully wipe
; user data too, uncomment the line below.
; Type: filesandordirs; Name: "{commonappdata}\MedicalLaboratoryManagementSystem"

[Code]
// ----------------------------------------------------------------------
// WebView2 Runtime detection (Part 89).
//
// pywebview's edgechromium backend requires the Microsoft Edge WebView2
// Runtime. Most Windows 10/11 machines already have it (it ships with
// Windows Update / Office / Edge), but this check catches the machines
// that don't, and offers to fetch the official installer rather than
// silently failing when the customer first opens the app.
// ----------------------------------------------------------------------
function IsWebView2Installed(): Boolean;
var
  Version: String;
begin
  Result :=
    RegQueryStringValue(HKLM64, 'SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Version) or
    RegQueryStringValue(HKLM32, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Version) or
    RegQueryStringValue(HKCU, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Version);
end;

procedure InitializeWizard();
begin
  if not IsWebView2Installed() then
  begin
    if MsgBox(
      'This application needs the Microsoft Edge WebView2 Runtime, which ' + #13#10 +
      'was not detected on this computer.' + #13#10 + #13#10 +
      'Setup will continue, but the application window will not be able ' + #13#10 +
      'to display until WebView2 Runtime is installed.' + #13#10 + #13#10 +
      'Open the Microsoft download page now?',
      mbConfirmation, MB_YESNO) = IDYES then
    begin
      ShellExec('open', 'https://developer.microsoft.com/en-us/microsoft-edge/webview2/', '', '', SW_SHOWNORMAL, ewNoWait, ErrorCode);
    end;
  end;
end;
