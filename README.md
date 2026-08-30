# ConsoleSeq

Подробная инструкция на русском, включая решение проблем со звуком: [README_RU.md](README_RU.md).

ConsoleSeq is a keyboard-driven terminal music sequencer with a C++17 audio engine and a Python `curses` interface. It starts with a playable rock beat and five channels, can grow to 32 channels, and includes 22 generated drum, bass, keys, lead, pad, and percussion presets. No sample pack is needed.

The engine renders stereo audio at 44.1 kHz with 512-frame buffers through RtAudio, decodes user WAV files with libsndfile, exposes its project model through pybind11, and stores projects as readable `.cseq` JSON files.

## Quick start

### Windows (PowerShell)

```powershell
.\setup.cmd
.\run.cmd
```

`setup.cmd` bypasses restrictive PowerShell execution policies only for the setup process and calls `setup.ps1`. Setup creates `.venv-win`, installs `windows-curses`, builds the C++ extension in `build-win`, and runs the complete test suite. If necessary it downloads project-local copies of Python 3.12, CMake, Ninja, and w64devkit. It does not require administrator access and does not modify the system `PATH` permanently. Windows and Unix use separate build/venv directories, so running both setup paths in one checkout cannot corrupt either environment.

### Linux (Debian/Ubuntu and derivatives)

```bash
chmod +x setup.sh run.sh
./setup.sh
./run.sh
```

The script installs missing compiler, CMake, Python development, and ALSA development packages with `apt`, then creates `.venv-unix` and builds in `build-unix`. On other distributions, install the equivalent packages before running `setup.sh`.

### macOS

```bash
chmod +x setup.sh run.sh
./setup.sh
./run.sh
```

The script uses Homebrew for missing CMake or Python. Xcode Command Line Tools provide the compiler and CoreAudio SDK.

The first build downloads pinned source releases of RtAudio 6.0.1, libsndfile 1.2.2, nlohmann/json 3.11.3, and pybind11 2.13.6 through CMake. Later builds reuse the CMake download cache under `build/`.

## Running

Open a project directly:

```bash
./run.sh my_song.cseq
```

On Windows:

```powershell
.\run.cmd my_song.cseq
```

Run the UI without opening an audio device:

```bash
./run.sh --no-audio
```

Run a non-interactive health check:

```bash
./run.sh --smoke-test
```

For the best layout, use a terminal at least 100 columns by 28 rows. The UI remains usable down to 76 by 20 and shows a resize message below that.

## Keyboard controls

| Key | Action |
|---|---|
| `P` | Play; while playing, stop and rewind. After pause, resumes from the paused position. |
| `A` | Pause transport. |
| `T` | Toggle looping. |
| `+` / `-` | Change BPM from 40 to 300. |
| `Tab` | Cycle Pattern, Song, and Mixer focus. Entering Pattern/Song focus also selects that playback mode. |
| Arrow keys | Move the Pattern/Song cursor; in Mixer focus adjust volume and pan. |
| `Space` | Toggle a pattern step, or cycle the pattern in a song cell. |
| `F1`–`F10` | Select a channel. |
| `I` | Add a channel and choose one of 22 built-in instrument presets. |
| `Enter` | Open selected-channel settings (preset, rename, clone/delete, WAV, ADSR, tone and drive); in Song focus cycle a cell. |
| `[` / `]` | Lower/raise the MIDI note on the selected synth step. |
| `{` / `}` | Transpose the selected synth step by an octave. |
| `;` / `'` | Lower/raise selected-step velocity by 0.05. |
| `Page Up` / `Page Down` | Select the previous/next Mixer channel (`K`/`J` also work). |
| `M` / `O` | Toggle mute / solo on the selected channel. |
| `C` / `V` | Copy / paste the complete current pattern. |
| `N` | Create and select a new pattern. |
| `B` / `R` / `X` | Duplicate, rename, or delete the current pattern. |
| `G` | Go to a pattern number in Pattern focus, or assign any pattern number in Song focus. |
| `,` / `.` | Select previous / next pattern. |
| `D` | Clear the current pattern after confirmation. |
| `Backspace` / `Delete` | Clear the selected pattern step or song cell. |
| `S` / `L` | Save / load a `.cseq` project. |
| `W` | Load a WAV file on the selected channel. Failed loads leave its existing sound intact. |
| `Esc` | Open the main menu. The menu can also cycle pattern length through 16, 32, and 64 steps. |
| `Q` | Quit. |

In channel settings, use `P` for the preset browser, `H` to rename, `C` to clone, `X` to delete, and `W` for a custom WAV. Synth channels additionally use `O` for sine/square/saw, `A`/`D`/`E`/`R` for ADSR, `N` for base note, `F` for tone/filter, and `G` for drive.

## What is included

- Pattern editor with 16/32/64 steps, per-step enable, MIDI pitch, and velocity in the project model.
- Per-channel song arrangement across 16 pattern slots.
- Mixer volume, constant-power pan, mute, solo, and soft master limiting.
- Thread-safe editable state published to the real-time callback as immutable snapshots; the callback takes no project mutex and performs no file I/O.
- Eight voices per channel for overlapping drum hits and synth notes.
- Twenty-two generated presets: three kicks, two snares, clap, closed/open hats, two toms, percussion, three keyboards, four basses, two leads, a pad, and a synth pluck.
- Dynamic add/clone/remove/rename operations for up to 32 channels; Pattern and Song rows resize atomically with the engine state.
- Harmonic, percussive piano and filtered saw/square/sine bass/synth voices with ADSR controls.
- WAV loading, mono conversion, and linear resampling to 44.1 kHz through libsndfile.
- JSON project save/load with mixer, instrument, pattern, note, velocity, and song data.
- A silent timing fallback when no audio device is available, plus offline rendering for tests.

## Project layout

```text
ConsoleSeq/
  CMakeLists.txt          C++ build and dependency fetching
  src/                    engine, project model, and pybind11 bindings
  console_seq/            Python package and curses UI
  tests/                  native and Python integration tests
  setup.cmd/.ps1/.sh      complete platform setup and verification
  run.cmd/.ps1/.sh        launchers
  main.py                 direct Python entry point
```

## Manual build (advanced)

After installing CMake, a C++17 compiler, Python development headers, and the platform audio SDK:

```bash
python3 -m venv .venv-unix
.venv-unix/bin/python -m pip install -r requirements.txt
cmake -S . -B build-unix -DCMAKE_BUILD_TYPE=Release -DPython_EXECUTABLE="$PWD/.venv-unix/bin/python"
cmake --build build-unix --parallel
ctest --test-dir build-unix --output-on-failure
```

Copy the resulting `build-unix/python/console_seq_core.*` next to `console_seq/core.py`, or leave it in the build directory; the development import path recognizes Windows, Unix, and legacy build layouts.

Useful CMake switches are `-DCONSOLESEQ_WITH_AUDIO=OFF`, `-DCONSOLESEQ_WITH_SNDFILE=OFF`, and `-DCONSOLESEQ_BUILD_TESTS=OFF`. The normal setup enables all three features.

## Troubleshooting

**The UI says it is in silent timing mode.** RtAudio could not open a default output device. Confirm that the device is connected, not exclusively locked, and supports stereo 44.1 kHz output. Editing, save/load, and transport position still work. On Linux, confirm that ALSA development/runtime packages are installed and that the user can access the audio device.

**No sound, but transport moves.** Check channel mute/solo flags and Mixer volume. Press `Esc`, then `N` to restore the audible demo project. If `--no-audio` was used, relaunch without it.

**`curses` import fails on Windows.** Re-run `setup.cmd`; it installs `windows-curses` into `.venv-win`. Always use `run.cmd` or `.venv-win\Scripts\python.exe`, not an unrelated global interpreter.

**PowerShell says script execution is disabled.** Use `setup.cmd` and `run.cmd`. Batch launchers are not governed by PowerShell execution policy. You do not need to change the permanent system policy.

**CMake cannot compile in a path with non-ASCII characters on Windows.** The supplied setup uses Ninja specifically to support Unicode workspace paths. Delete only the generated `build-win` directory and rerun `setup.cmd` if the directory was previously configured with another generator.

**A WAV does not load.** ConsoleSeq intentionally builds libsndfile without optional compressed codecs. Use PCM or IEEE-float WAV. The old/built-in sound remains active after a failed load.

**Automatic package installation is unavailable.** On Linux install `build-essential cmake python3 python3-venv python3-dev pkg-config libasound2-dev`; on macOS install Xcode Command Line Tools plus `cmake` and `python` from Homebrew. Then rerun the same setup script.

## Current limitations

ConsoleSeq intentionally keeps the workflow compact: there are 16 song slots and up to 32 channels; notes are edited per sequencer step rather than in a graphical piano roll; sample paths are stored as provided, so moving a project does not copy its custom WAV files; and there are no plug-ins, automation lanes, recording, effects, or audio export. The 22 built-in presets are fully portable because they reference no external assets.
