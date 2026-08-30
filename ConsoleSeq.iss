#define MyAppName "ConsoleSeq"
#define MyAppVersion "1.3.2"
#define MyAppPublisher "ConsoleSeq Project"
#define MyAppExeName "ConsoleSeq.exe"

[Setup]
AppId={{9C91877B-F652-4B84-AC19-D35AE38BF634}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\ConsoleSeq
DefaultGroupName=ConsoleSeq
UninstallDisplayIcon={app}\{#MyAppExeName}
LicenseFile=LICENSE
OutputDir=dist-installer
OutputBaseFilename=ConsoleSeq-Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
ChangesAssociations=yes
CloseApplications=yes
RestartApplications=no
VersionInfoVersion={#MyAppVersion}
VersionInfoProductName={#MyAppName}
VersionInfoDescription=ConsoleSeq terminal music sequencer installer

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "ConsoleSeq.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README_RU.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "REPORT.md"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{userdocs}\ConsoleSeq Projects"

[Icons]
Name: "{group}\ConsoleSeq"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{userdocs}\ConsoleSeq Projects"
Name: "{group}\Инструкция ConsoleSeq"; Filename: "{app}\README_RU.md"
Name: "{autodesktop}\ConsoleSeq"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{userdocs}\ConsoleSeq Projects"; Tasks: desktopicon

[Registry]
Root: HKA; Subkey: "Software\Classes\.cseq"; ValueType: string; ValueName: ""; ValueData: "ConsoleSeq.Project"; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\ConsoleSeq.Project"; ValueType: string; ValueName: ""; ValueData: "ConsoleSeq Project"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\ConsoleSeq.Project\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
Root: HKA; Subkey: "Software\Classes\ConsoleSeq.Project\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; WorkingDir: "{userdocs}\ConsoleSeq Projects"; Flags: nowait postinstall skipifsilent
