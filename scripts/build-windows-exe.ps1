$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$DistDir = Join-Path $ProjectRoot "dist"
$BuildDir = Join-Path $ProjectRoot "build\pyinstaller"
$EntryPoint = Join-Path $ProjectRoot "scripts\windows_main.py"
$Version = $env:VERSION

if ([string]::IsNullOrWhiteSpace($Version)) {
    $VersionLine = (Get-Content (Join-Path $ProjectRoot "pyproject.toml") | Where-Object { $_ -match '^version\s*=' } | Select-Object -First 1)
    if (-not $VersionLine) {
        throw "Unable to parse version from pyproject.toml"
    }

    $Version = ($VersionLine -split "=", 2)[1].Trim().Trim('"')
}

python -m PyInstaller --version *> $null
if ($LASTEXITCODE -ne 0) {
    python -m pip install --upgrade pip
    python -m pip install pyinstaller
}

python -m pip install --upgrade pip setuptools wheel
python -m pip install $ProjectRoot

New-Item -ItemType Directory -Force -Path $DistDir | Out-Null
New-Item -ItemType Directory -Force -Path $BuildDir | Out-Null

python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --name "nonet-movie" `
    --distpath $DistDir `
    --workpath $BuildDir `
    $EntryPoint

$SourceExe = Join-Path $DistDir "nonet-movie.exe"
$VersionedExe = Join-Path $DistDir ("nonet-movie-{0}.exe" -f $Version)

if (Test-Path $VersionedExe) {
    Remove-Item $VersionedExe -Force
}

Copy-Item $SourceExe $VersionedExe
Write-Host "Created: $SourceExe"
Write-Host "Created: $VersionedExe"
