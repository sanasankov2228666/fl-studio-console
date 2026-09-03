[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$GeneratedRoot = Join-Path $ProjectRoot "pyinstaller-build\release"
$PackageRoot = Join-Path $GeneratedRoot "ConsoleSeq"
$ZipPath = Join-Path $ProjectRoot "ConsoleSeq.zip"
$TemporaryZip = Join-Path $GeneratedRoot "ConsoleSeq.zip"

function Remove-GeneratedDirectory([string]$Target) {
    if (-not (Test-Path -LiteralPath $Target)) { return }
    $resolvedProject = [IO.Path]::GetFullPath($ProjectRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
    $resolvedTarget = [IO.Path]::GetFullPath($Target).TrimEnd([IO.Path]::DirectorySeparatorChar)
    if (-not $resolvedTarget.StartsWith($resolvedProject + [IO.Path]::DirectorySeparatorChar,
            [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove generated directory outside the project: $resolvedTarget"
    }
    Remove-Item -LiteralPath $resolvedTarget -Recurse -Force
}

if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot "ConsoleSeq.exe"))) {
    throw "ConsoleSeq.exe is missing. Run build_exe.cmd first."
}

Remove-GeneratedDirectory $GeneratedRoot
New-Item -ItemType Directory -Force -Path $PackageRoot | Out-Null

foreach ($directory in @("assets", "src", "scripts")) {
    Copy-Item -LiteralPath (Join-Path $ProjectRoot $directory) -Destination $PackageRoot -Recurse
}
New-Item -ItemType Directory -Force -Path (Join-Path $PackageRoot "tests") | Out-Null
Get-ChildItem -LiteralPath (Join-Path $ProjectRoot "tests") -File |
    Where-Object { $_.Extension -in ".py", ".cpp", ".hpp", ".h" } |
    Copy-Item -Destination (Join-Path $PackageRoot "tests")
New-Item -ItemType Directory -Force -Path (Join-Path $PackageRoot "console_seq") | Out-Null
Get-ChildItem -LiteralPath (Join-Path $ProjectRoot "console_seq") -Filter "*.py" -File |
    Copy-Item -Destination (Join-Path $PackageRoot "console_seq")

$topLevel = @(
    ".gitignore", "CMakeLists.txt", "ConsoleSeq.spec", "ConsoleSeq.iss", "LICENSE", "README.md", "README_RU.md", "REPORT.md",
    "main.py", "requirements.txt", "requirements-build.txt", "setup.cmd", "setup.ps1", "setup.sh",
    "run.cmd", "run.ps1", "run.sh", "build_exe.cmd", "build_exe.ps1",
    "build_installer.cmd", "build_installer.ps1", "package_release.cmd", "package_release.ps1",
    "ConsoleSeq.exe", "ConsoleSeq-Setup.exe", "new_jazz.cseq"
)
foreach ($name in $topLevel) {
    $source = Join-Path $ProjectRoot $name
    if (Test-Path -LiteralPath $source) {
        Copy-Item -LiteralPath $source -Destination $PackageRoot
    }
}

Compress-Archive -LiteralPath $PackageRoot -DestinationPath $TemporaryZip -CompressionLevel Optimal
if (Test-Path -LiteralPath $ZipPath) { Remove-Item -LiteralPath $ZipPath -Force }
Move-Item -LiteralPath $TemporaryZip -Destination $ZipPath
Write-Host "Ready: $ZipPath"
