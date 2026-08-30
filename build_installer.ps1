[CmdletBinding()]
param(
    [switch]$SkipExeBuild
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PortableExe = Join-Path $ProjectRoot "ConsoleSeq.exe"
$Installer = Join-Path $ProjectRoot "dist-installer\ConsoleSeq-Setup.exe"

if (-not $SkipExeBuild) {
    & (Join-Path $ProjectRoot "build_exe.ps1")
    if ($LASTEXITCODE -ne 0) { throw "Portable EXE build failed." }
}
if (-not (Test-Path -LiteralPath $PortableExe)) {
    throw "ConsoleSeq.exe is missing. Run build_exe.cmd first."
}

$candidates = @(
    (Get-Command ISCC.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue),
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }

if (-not $candidates) {
    $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
    if (-not $winget) {
        throw "Inno Setup is missing and winget is unavailable. Install Inno Setup 6 and retry."
    }
    Write-Host "Installing Inno Setup compiler..."
    & $winget.Source install --id JRSoftware.InnoSetup --exact --silent `
        --accept-package-agreements --accept-source-agreements --disable-interactivity
    if ($LASTEXITCODE -ne 0) { throw "winget could not install Inno Setup." }
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    ) | Where-Object { Test-Path -LiteralPath $_ }
}

$compiler = $candidates | Select-Object -First 1
if (-not $compiler) { throw "Inno Setup compiler was not found after installation." }
Push-Location $ProjectRoot
try {
    & $compiler (Join-Path $ProjectRoot "ConsoleSeq.iss")
    if ($LASTEXITCODE -ne 0) { throw "Inno Setup compilation failed." }
} finally {
    Pop-Location
}
if (-not (Test-Path -LiteralPath $Installer)) { throw "The installer was not created." }
Copy-Item -LiteralPath $Installer -Destination (Join-Path $ProjectRoot "ConsoleSeq-Setup.exe") -Force
Write-Host "Ready: $Installer"
