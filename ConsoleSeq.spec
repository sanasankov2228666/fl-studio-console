# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


project_root = Path(SPECPATH)
native_modules = sorted((project_root / "build-win" / "python").glob("console_seq_core*.pyd"))
if len(native_modules) != 1:
    raise RuntimeError(
        "Expected one freshly built console_seq_core module in build-win/python; "
        "run setup.cmd first."
    )

binaries = [(str(native_modules[0]), "console_seq")]
for runtime_name in ("libgcc_s_seh-1.dll", "libstdc++-6.dll", "libwinpthread-1.dll"):
    runtime_path = project_root / "console_seq" / runtime_name
    if runtime_path.exists():
        binaries.append((str(runtime_path), "console_seq"))

a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=[],
    # The native package extension is supplied explicitly above. Listing it as
    # a hidden import would let an older staged development copy override it.
    hiddenimports=["curses", "_curses"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="ConsoleSeq",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
