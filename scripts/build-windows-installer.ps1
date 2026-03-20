$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$DistDir = Join-Path $ProjectRoot "dist"
$BuildDir = Join-Path $ProjectRoot "build\windows-installer"
$SharedIconSvg = Join-Path $ProjectRoot "assets\nonet-movie.svg"
$InstallerIconIco = Join-Path $BuildDir "nonet-movie-installer.ico"
$Version = $env:VERSION

if ([string]::IsNullOrWhiteSpace($Version)) {
    $VersionLine = (Get-Content (Join-Path $ProjectRoot "pyproject.toml") | Where-Object { $_ -match '^version\s*=' } | Select-Object -First 1)
    if (-not $VersionLine) {
        throw "Unable to parse version from pyproject.toml"
    }

    $Version = ($VersionLine -split "=", 2)[1].Trim().Trim('"')
}

$PortableExe = Join-Path $DistDir ("nonet-movie-{0}.exe" -f $Version)

if (-not (Test-Path $PortableExe)) {
    throw "Missing portable executable: $PortableExe. Run scripts/build-windows-exe.ps1 first."
}

if (-not (Test-Path $SharedIconSvg)) {
    throw "Missing shared icon file: $SharedIconSvg"
}

$MagickCmd = Get-Command magick -ErrorAction SilentlyContinue
if (-not $MagickCmd) {
    throw "ImageMagick ('magick') is required to convert $SharedIconSvg to .ico for Windows installer."
}

$IsccCmd = Get-Command iscc -ErrorAction SilentlyContinue
if (-not $IsccCmd) {
    throw "Inno Setup Compiler ('iscc') is required to build the Windows installer."
}

New-Item -ItemType Directory -Force -Path $DistDir | Out-Null
New-Item -ItemType Directory -Force -Path $BuildDir | Out-Null

& $MagickCmd.Source $SharedIconSvg -background none -define icon:auto-resize=256,128,64,48,32,16 $InstallerIconIco
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $InstallerIconIco)) {
    throw "Failed to generate installer icon file: $InstallerIconIco"
}

$InstallerScript = Join-Path $BuildDir "nonet-movie-installer.iss"
$EscapedPortableExe = $PortableExe.Replace('\', '\\')
$EscapedDistDir = $DistDir.Replace('\', '\\')
$EscapedInstallerIcon = $InstallerIconIco.Replace('\', '\\')

$ScriptContent = @"
#define MyAppName "Nonet Movie"
#define MyAppVersion "$Version"
#define MyAppPublisher "Ariana Maghsoudi"
#define MyAppExeName "nonet-movie.exe"

[Setup]
AppId={{A8E46657-5728-4A9F-ACB3-8626B6F80F4E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=$EscapedDistDir
OutputBaseFilename=nonet-movie-setup-$Version
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=$EscapedInstallerIcon
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "$EscapedPortableExe"; DestDir: "{app}"; DestName: "{#MyAppExeName}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
"@

$ScriptContent | Set-Content -Path $InstallerScript -Encoding UTF8

& $IsccCmd.Source $InstallerScript
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup compilation failed."
}

$InstallerExe = Join-Path $DistDir ("nonet-movie-setup-{0}.exe" -f $Version)
if (-not (Test-Path $InstallerExe)) {
    throw "Installer file was not created: $InstallerExe"
}

Write-Host "Created: $InstallerExe"
