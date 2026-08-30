# ConsoleSeq 1.3.2

For the complete Russian tutorial, troubleshooting guide, instrument list, pattern-bank examples, custom sample guide, and save/load instructions, see [README_RU.md](README_RU.md).

ConsoleSeq is a keyboard-driven terminal sequencer with a C++17 real-time engine and a Python curses UI. Version 1.3.2 includes 60 generated/modelled presets, 40 GeneralUser GS instruments rendered by FluidSynth, and 167 bundled WAV/MP3 one-shots arranged in 19 drum-kit tabs. Every custom or bundled sample can be transposed per step. It supports colored gated notes (`X ===`), a high-contrast pattern cursor, opaque popup menus, up to 32 channels, 512 patterns and 512 song slots, atomic JSON persistence, a portable Windows EXE, and an optional Windows installer.

## Windows quick start

Run the ready executable:

```powershell
.\ConsoleSeq.exe
```

`ConsoleSeq.exe` is fully portable and may be sent by itself. `ConsoleSeq-Setup.exe` is the optional per-user installer with Start Menu/Desktop shortcuts and `.cseq` file association; it does not require administrator rights.

Or rebuild and test everything without administrator rights:

```powershell
.\setup.cmd
.\run.cmd
```

The `.cmd` launchers work when PowerShell script execution is disabled. `setup.cmd` bootstraps project-local Python/CMake/Ninja/MinGW tools when required, builds the C++ extension, runs all tests, builds `ConsoleSeq.exe`, and smoke-tests the executable in a separate directory.

Rebuild only the executable with `build_exe.cmd`.

Build the Windows installer with `build_installer.cmd`; it installs Inno Setup through `winget` when the compiler is absent.

Rebuild the clean source/assets/EXE archive with `package_release.cmd`.

## Linux/macOS

```bash
chmod +x setup.sh run.sh
./setup.sh
./run.sh
```

## Core controls

| Key | Action |
|---|---|
| `P`, `A`, `T` | Play/stop, pause, loop |
| `Tab` | Pattern, Song, Mixer focus |
| `Space` | Toggle a step or cycle a Song cell |
| `E`, then `Left/Right` | Edit the selected `X ===` note length; `E`/`Esc` finishes |
| `[`/`]`, `{`/`}` | Transpose the selected note or sample by a semitone/octave |
| `I`, `Enter` | Add an instrument; edit selected channel |
| `n`, `N` | Add one pattern; add a bank of 16 |
| `Page Up/Down` | Move between 16-pattern or 16-slot banks |
| `B`, `R`, `X`, `G` | Duplicate, rename, delete, go to pattern |
| `C`, `V`, `D` | Copy, paste, clear pattern |
| `S`, `L`, `W` | Save, load, load WAV/MP3 |
| `M`, `O` | Mute, solo |
| `Esc`, `Q` | Main menu, quit |

The preset browser uses Left/Right for category tabs, Up/Down for sounds, and Enter to apply. The main menu (`Esc`) changes Song length from 1–512 and pattern length between 16/32/64 steps.

## Architecture and dependencies

- RtAudio 6.0.1 for 44.1 kHz stereo real-time output;
- FluidSynth 2.6.0 plus the bundled GeneralUser GS SoundFont for sampled instruments;
- libsndfile 1.2.2 for WAV and dr_mp3 0.7.3 for MP3;
- nlohmann/json 3.11.3 for `.cseq` JSON;
- pybind11 2.13.6 for the Python extension;
- PyInstaller 6.22.2 for the Windows one-file executable.

The setup scripts install or download all required build dependencies. The Windows build downloads the official FluidSynth binary SDK and GeneralUser GS automatically. Bundled kit samples use portable `asset://` references; custom WAV/MP3 files remain external and are referenced by their paths.

## Project layout

```text
CMakeLists.txt             C++ build and pinned dependencies
src/                       engine, preset catalog, model, bindings
console_seq/               Python package and curses UI
assets/                    GeneralUser GS, licenses, bundled drum kits
tests/                     native and Python integration/UI tests
setup.cmd/.ps1/.sh         setup, build, verification
build_exe.cmd/.ps1         reproducible Windows EXE build
build_installer.cmd/.ps1   Inno Setup installer build
ConsoleSeq.iss             per-user installer definition
ConsoleSeq.spec            one-file packaging definition
main.py                    source entry point
```

Run a headless check:

```powershell
.\ConsoleSeq.exe --smoke-test --no-audio --smoke-output .\check.cseq
```

Current deliberate limits: no recording, plug-ins, automation lanes, audio export, or graphical piano roll. See the Russian README for detailed usage and roadmap.
