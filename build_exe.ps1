[CmdletBinding()]
param(
    [switch]$SkipSmokeTest
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $ProjectRoot ".venv-win\Scripts\python.exe"
$NativeDirectory = Join-Path $ProjectRoot "build-win\python"
$SpecFile = Join-Path $ProjectRoot "ConsoleSeq.spec"
$DistDirectory = Join-Path $ProjectRoot "dist"
$WorkDirectory = Join-Path $ProjectRoot "pyinstaller-build"
$ExePath = Join-Path $DistDirectory "ConsoleSeq.exe"

if (-not (Test-Path -LiteralPath $VenvPython)) {
    throw "Windows environment is missing. Run setup.cmd first."
}
if (-not (Get-ChildItem -LiteralPath $NativeDirectory -Filter "console_seq_core*.pyd" -ErrorAction SilentlyContinue)) {
    throw "Fresh native module is missing. Run setup.cmd first."
}

Write-Host "Installing the pinned executable packager..."
& $VenvPython -m pip install -r (Join-Path $ProjectRoot "requirements-build.txt")
if ($LASTEXITCODE -ne 0) { throw "Could not install PyInstaller." }

Write-Host "Building the standalone ConsoleSeq.exe..."
& $VenvPython -m PyInstaller --noconfirm --clean `
    --distpath $DistDirectory --workpath $WorkDirectory $SpecFile
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $ExePath)) {
    throw "PyInstaller did not create ConsoleSeq.exe."
}

if (-not $SkipSmokeTest) {
    $SmokeDirectory = Join-Path $WorkDirectory "clean-smoke"
    New-Item -ItemType Directory -Force -Path $SmokeDirectory | Out-Null
    $SmokeProject = Join-Path $SmokeDirectory "exe-smoke.cseq"
    $previousPythonHome = $env:PYTHONHOME
    $previousPythonPath = $env:PYTHONPATH
    try {
        Remove-Item Env:PYTHONHOME -ErrorAction SilentlyContinue
        Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
        Push-Location $SmokeDirectory
        try {
            & $ExePath --smoke-test --no-audio --smoke-output $SmokeProject
            $smokeExitCode = $LASTEXITCODE
            if ($smokeExitCode -ne 0 -or -not (Test-Path -LiteralPath $SmokeProject)) {
                throw "The standalone executable smoke test failed."
            }
        } finally {
            Pop-Location
        }
    } finally {
        if ($null -ne $previousPythonHome) { $env:PYTHONHOME = $previousPythonHome }
        if ($null -ne $previousPythonPath) { $env:PYTHONPATH = $previousPythonPath }
    }
}

Copy-Item -LiteralPath $ExePath -Destination (Join-Path $ProjectRoot "ConsoleSeq.exe") -Force
Write-Host "Ready: $ExePath"
