[CmdletBinding()]
param(
    [switch]$SkipTests,
    [switch]$SkipExe
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ToolsDir = Join-Path $ProjectRoot ".tools"
$BuildDir = Join-Path $ProjectRoot "build-win"
$VenvDir = Join-Path $ProjectRoot ".venv-win"
New-Item -ItemType Directory -Force -Path $ToolsDir | Out-Null

function Test-UsablePython([string]$Candidate) {
    if (-not (Test-Path $Candidate)) { return $false }
    $includePath = & $Candidate -c "import sysconfig; print(sysconfig.get_paths()['include'])" 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $includePath) { return $false }
    return Test-Path (Join-Path $includePath.Trim() "Python.h")
}

function Remove-GeneratedDirectory([string]$Target) {
    if (-not (Test-Path -LiteralPath $Target)) { return }
    $resolvedRoot = [IO.Path]::GetFullPath($ProjectRoot).TrimEnd([IO.Path]::DirectorySeparatorChar)
    $resolvedTarget = [IO.Path]::GetFullPath($Target).TrimEnd([IO.Path]::DirectorySeparatorChar)
    if (-not $resolvedTarget.StartsWith($resolvedRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove generated directory outside the project: $resolvedTarget"
    }
    Remove-Item -LiteralPath $resolvedTarget -Recurse -Force
}

function Get-OrDownloadPython {
    $venvPython = Join-Path $VenvDir "Scripts\python.exe"
    if (Test-UsablePython $venvPython) { return $venvPython }
    $existing = Get-Command python -ErrorAction SilentlyContinue
    if ($existing -and (Test-UsablePython $existing.Source)) { return $existing.Source }

    $localPython = Join-Path $ToolsDir "Python312\python.exe"
    if (-not (Test-UsablePython $localPython)) {
        Remove-GeneratedDirectory (Split-Path -Parent $localPython)
        $installer = Join-Path $ToolsDir "python-3.12.7-amd64.exe"
        if (-not (Test-Path $installer) -or (Get-Item $installer).Length -lt 10MB) {
            if (Test-Path $installer) { Remove-Item -LiteralPath $installer -Force }
            Write-Host "Downloading a local Python 3.12 toolchain..."
            curl.exe -fL --retry 3 -o $installer "https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe"
        }
        $target = Join-Path $ToolsDir "Python312"
        $arguments = @(
            "/quiet", "InstallAllUsers=0", "TargetDir=$target", "PrependPath=0",
            "Include_pip=1", "Include_dev=1", "Include_launcher=0", "Include_test=0",
            "Shortcuts=0", "AssociateFiles=0"
        )
        $process = Start-Process -FilePath $installer -ArgumentList $arguments -Wait -PassThru
        if ($process.ExitCode -ne 0) { throw "Python installer exited with code $($process.ExitCode)" }
    }
    if (-not (Test-UsablePython $localPython)) { throw "The downloaded Python installation is unusable." }
    return $localPython
}

function Get-OrDownloadCMake {
    $existing = Get-Command cmake -ErrorAction SilentlyContinue
    if ($existing) { return $existing.Source }

    $localCMake = Join-Path $ToolsDir "cmake-3.30.5-windows-x86_64\bin\cmake.exe"
    if (-not (Test-Path $localCMake)) {
        $archive = Join-Path $ToolsDir "cmake-3.30.5-windows-x86_64.zip"
        if (-not (Test-Path $archive) -or (Get-Item $archive).Length -lt 10MB) {
            if (Test-Path $archive) { Remove-Item -LiteralPath $archive -Force }
            Write-Host "Downloading portable CMake..."
            curl.exe -fL --retry 3 -o $archive "https://github.com/Kitware/CMake/releases/download/v3.30.5/cmake-3.30.5-windows-x86_64.zip"
        }
        Expand-Archive -Path $archive -DestinationPath $ToolsDir -Force
    }
    return $localCMake
}

function Get-OrDownloadNinja {
    $existing = Get-Command ninja.exe -ErrorAction SilentlyContinue
    if ($existing) { return $existing.Source }

    $localNinja = Join-Path $ToolsDir "ninja.exe"
    if (-not (Test-Path $localNinja)) {
        $archive = Join-Path $ToolsDir "ninja-win.zip"
        if (-not (Test-Path $archive) -or (Get-Item $archive).Length -lt 100KB) {
            if (Test-Path $archive) { Remove-Item -LiteralPath $archive -Force }
            Write-Host "Downloading portable Ninja..."
            curl.exe -fL --retry 3 -o $archive "https://github.com/ninja-build/ninja/releases/download/v1.12.1/ninja-win.zip"
        }
        Expand-Archive -Path $archive -DestinationPath $ToolsDir -Force
    }
    return $localNinja
}

function Find-OrDownloadCompiler {
    $existing = Get-Command g++.exe -ErrorAction SilentlyContinue
    if ($existing) { return Split-Path -Parent $existing.Source }

    $knownCompiler = Join-Path $env:USERPROFILE "Downloads\w64devkit\bin\g++.exe"
    if (Test-Path $knownCompiler) { return Split-Path -Parent $knownCompiler }

    $localCompiler = Join-Path $ToolsDir "w64devkit\bin\g++.exe"
    if (-not (Test-Path $localCompiler)) {
        $archive = Join-Path $ToolsDir "w64devkit-x64-2.9.1.7z.exe"
        if (-not (Test-Path $archive) -or (Get-Item $archive).Length -lt 20MB) {
            if (Test-Path $archive) { Remove-Item -LiteralPath $archive -Force }
            Write-Host "Downloading the portable w64devkit C++ compiler..."
            curl.exe -fL --retry 3 -o $archive "https://github.com/skeeto/w64devkit/releases/download/v2.9.1/w64devkit-x64-2.9.1.7z.exe"
        }
        & $archive -y "-o$ToolsDir" | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "w64devkit extraction failed." }
    }
    if (-not (Test-Path $localCompiler)) { throw "Could not locate the downloaded C++ compiler." }
    return Split-Path -Parent $localCompiler
}

$Python = Get-OrDownloadPython
$CMake = Get-OrDownloadCMake
$Ninja = Get-OrDownloadNinja
$CompilerBin = Find-OrDownloadCompiler
$env:Path = "$CompilerBin;$env:Path"

if (-not (Test-UsablePython (Join-Path $VenvDir "Scripts\python.exe"))) {
    Remove-GeneratedDirectory $VenvDir
    & $Python -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) { throw "Could not create the Windows virtual environment." }
}
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
if (-not (Test-UsablePython $VenvPython)) { throw "The new Windows virtual environment is unusable." }
& $VenvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Could not upgrade pip." }
& $VenvPython -m pip install -r (Join-Path $ProjectRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "Could not install Python dependencies." }

$cacheFile = Join-Path $BuildDir "CMakeCache.txt"
if (Test-Path -LiteralPath $cacheFile) {
    $generatorLine = Select-String -LiteralPath $cacheFile -Pattern '^CMAKE_GENERATOR:INTERNAL=Ninja$' -Quiet
    if (-not $generatorLine) {
        Write-Host "Removing a build directory configured with a different generator..."
        Remove-GeneratedDirectory $BuildDir
    }
}

Write-Host "Configuring ConsoleSeq..."
& $CMake -S $ProjectRoot -B $BuildDir -G "Ninja" `
    "-DCMAKE_MAKE_PROGRAM=$Ninja" `
    "-DCMAKE_BUILD_TYPE=Release" `
    "-DPython_EXECUTABLE=$VenvPython" `
    "-DCMAKE_INSTALL_PREFIX=$ProjectRoot"
if ($LASTEXITCODE -ne 0) { throw "CMake configuration failed." }

& $CMake --build $BuildDir --parallel
if ($LASTEXITCODE -ne 0) { throw "C++ build failed." }
$NativeModule = Get-ChildItem -Path (Join-Path $BuildDir "python") -Filter "console_seq_core*.pyd" |
    Select-Object -First 1
if (-not $NativeModule) { throw "The built Python module was not found." }
$stagedModule = Join-Path (Join-Path $ProjectRoot "console_seq") $NativeModule.Name
try {
    Copy-Item -LiteralPath $NativeModule.FullName -Destination $stagedModule -Force
} catch [System.IO.IOException] {
    Write-Warning "The staged module is open in a running ConsoleSeq process. Tests will use the fresh module from build-win; close the old app before packaging."
}
foreach ($runtimeName in @("libgcc_s_seh-1.dll", "libstdc++-6.dll", "libwinpthread-1.dll")) {
    $runtimePath = Join-Path $CompilerBin $runtimeName
    if (Test-Path $runtimePath) {
        Copy-Item -LiteralPath $runtimePath -Destination (Join-Path $ProjectRoot "console_seq") -Force
    }
}

if (-not $SkipTests) {
    & $CMake --build $BuildDir --target test
    if ($LASTEXITCODE -ne 0) { throw "Native tests failed." }
    & $VenvPython (Join-Path $ProjectRoot "main.py") --smoke-test `
        --smoke-output (Join-Path $BuildDir "setup_smoke.cseq")
    if ($LASTEXITCODE -ne 0) { throw "Python smoke test failed." }
    & $VenvPython -m unittest discover -s (Join-Path $ProjectRoot "tests") -p "test_python.py" -v
    if ($LASTEXITCODE -ne 0) { throw "Python integration tests failed." }
}

if (-not $SkipExe) {
    & (Join-Path $ProjectRoot "build_exe.ps1")
    if ($LASTEXITCODE -ne 0) { throw "Standalone executable build failed." }
}

Write-Host ""
Write-Host "ConsoleSeq is ready. Run:"
Write-Host "  .\ConsoleSeq.exe"
Write-Host "or from source:"
Write-Host "  .\run.cmd"
