; Faceless YouTube - Professional Windows Installer
; Created with Inno Setup 6.5+
; Installs the Faceless YouTube PyQt6 desktop application

[Setup]
AppName=Faceless YouTube
AppVersion=1.0.0
AppPublisher=Faceless YouTube Project
DefaultDirName={pf}\Faceless YouTube
DefaultGroupName=Faceless YouTube
OutputDir=Output
OutputBaseFilename=faceless-youtube-setup
Compression=none
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
LicenseFile=LICENSE

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\faceless-youtube.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Faceless YouTube"; Filename: "{app}\faceless-youtube.exe"
Name: "{group}\Uninstall Faceless YouTube"; Filename: "{uninstallexe}"
Name: "{commondesktop}\Faceless YouTube"; Filename: "{app}\faceless-youtube.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional options:"; Flags: unchecked

[Run]
Filename: "{app}\faceless-youtube.exe"; Description: "Launch Faceless YouTube"; Flags: nowait postinstall skipifsilent
