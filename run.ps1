$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $ProjectRoot ".venv-win\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    Write-Error "ConsoleSeq is not built. Run .\setup.ps1 first."
    exit 1
}
& $Python -c "import sys" *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Error "ConsoleSeq's Windows environment is broken. Run .\setup.ps1 to repair it."
    exit 1
}
& $Python (Join-Path $ProjectRoot "main.py") @args
exit $LASTEXITCODE
