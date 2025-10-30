; Faceless YouTube - Professional Windows Installer
; Created with Inno Setup 6.2 or later
; 
; This script creates a professional one-click installer for
; the Faceless YouTube application (PyQt6 desktop application)

[Setup]
AppName=Faceless YouTube
AppVersion=1.0.0
AppPublisher=Faceless YouTube Project
AppPublisherURL=https://github.com/sgbilod/faceless-youtube
AppSupportURL=https://github.com/sgbilod/faceless-youtube/issues
AppUpdatesURL=https://github.com/sgbilod/faceless-youtube/releases
DefaultDirName={pf}\Faceless YouTube
DefaultGroupName=Faceless YouTube
OutputDir=Output
OutputBaseFilename=faceless-youtube-setup
Compression=lzma
SolidCompression=yes
AllowNetworkDrive=no
AllowUNCPath=no
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=no
DisableReadyPage=no
DisableStartupPrompt=no
LicenseFile=LICENSE
PrivilegesRequired=admin
SetupIconFile=faceless_youtube_icon.ico
UninstallDisplayIcon={app}\faceless-youtube.exe
WizardImageFile=installer_banner.bmp
WizardSmallImageFile=installer_small.bmp

; Language support
[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

; Files to install
[Files]
Source: "dist\faceless-youtube\faceless-youtube.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\faceless-youtube\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Create shortcuts
[Icons]
Name: "{commonprograms}\Faceless YouTube\Faceless YouTube"; Filename: "{app}\faceless-youtube.exe"
Name: "{commonprograms}\Faceless YouTube\Uninstall Faceless YouTube"; Filename: "{uninstallexe}"
Name: "{commondesktop}\Faceless YouTube"; Filename: "{app}\faceless-youtube.exe"; Tasks: desktopicon

; Tasks (optional installations)
[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

; Run after installation
[Run]
Filename: "{app}\faceless-youtube.exe"; Description: "{cm:LaunchProgram,Faceless YouTube}"; Flags: nowait postinstall skipifsilent

; Code section for advanced operations
[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    MsgBox('Faceless YouTube has been installed successfully!' + #13 +
           'You can now run the application from the Start menu or desktop shortcut.', 
           mbInformation, MB_OK);
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    MsgBox('Faceless YouTube has been uninstalled successfully.', 
           mbInformation, MB_OK);
  end;
end;

; Messages
[CustomMessages]
BeveledLabel=Faceless YouTube Installer
LaunchProgram=Launch Faceless YouTube
CreateDesktopIcon=Create a &desktop shortcut
AdditionalIcons=Additional icons:
