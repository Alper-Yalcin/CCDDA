#define MyAppName "ChildArt Analyzer"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "CCDDA"
#define MyAppExeName "ChildArtAnalyzer.exe"
#define WebView2ClientId "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"

[Setup]
AppId={{A6AFB08F-8868-468D-9DF7-E703519B4EA7}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\ChildArtAnalyzer
DefaultGroupName={#MyAppName}
OutputDir=..\artifacts\installer
OutputBaseFilename=ChildArtAnalyzer-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
Source: "..\dist\ChildArtAnalyzer\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Code]
function IsWebView2Installed(): Boolean;
var
  Version: string;
begin
  Result :=
    RegQueryStringValue(HKLM64, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{#WebView2ClientId}', 'pv', Version) or
    RegQueryStringValue(HKCU64, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{#WebView2ClientId}', 'pv', Version) or
    RegQueryStringValue(HKLM32, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{#WebView2ClientId}', 'pv', Version) or
    RegQueryStringValue(HKCU32, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{#WebView2ClientId}', 'pv', Version) or
    RegQueryStringValue(HKLM, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{#WebView2ClientId}', 'pv', Version) or
    RegQueryStringValue(HKCU, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{#WebView2ClientId}', 'pv', Version);

  if Result then
    Result := (Version <> '') and (Version <> '0.0.0.0');
end;

function InitializeSetup(): Boolean;
begin
  if IsWebView2Installed() then
  begin
    Result := True;
    exit;
  end;

  MsgBox(
    'Microsoft Edge WebView2 Runtime is required before installing ChildArt Analyzer.' + #13#10#13#10 +
    'Install WebView2 Runtime from Microsoft, then run this installer again.',
    mbCriticalError,
    MB_OK
  );
  Result := False;
end;
