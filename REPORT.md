# ConsoleSeq implementation report

## Delivered

ConsoleSeq 1.1 is a working mixed C++/Python terminal DAW. The C++17 core owns sequencing, synthesis, generated samples, mixing, transport, WAV decoding, JSON persistence, offline rendering, RtAudio output, and the thread-safe state boundary. pybind11 exposes `Engine`, `Pattern`, `Channel`, and `Song` to the Python curses UI.

The default project contains four patterns and five configured channels. Pattern 1 is an immediately playable rock beat. Kick, Snare, and HiHat are generated as short in-memory samples; Piano uses a harmonic percussive voice; Bass uses selectable oscillators and a decaying low-pass filter. Mixer gain/pan/mute/solo and a soft limiter run in the audio renderer.

The terminal UI provides always-visible Pattern, Channel, Song, and Mixer panels, a transport bar and contextual status line, pop-up save/load/sample dialogs, a channel editor, and a main menu. Version 1.1 adds a 22-preset browser, dynamic add/clone/rename/remove operations for up to 32 channels, channel-list scrolling, pattern duplicate/rename/remove/go-to commands, octave and velocity step editing, and synth Tone/Drive controls. All pattern and Song rows resize consistently when channels change.

## Build and dependency behavior

CMake fetches pinned RtAudio, libsndfile, nlohmann/json, and pybind11 sources. `setup.ps1` bootstraps a local Windows Python/CMake/Ninja/MinGW toolchain when missing and handles Unicode paths. Windows users launch it through `setup.cmd`, which applies a process-local PowerShell execution-policy bypass without changing the machine configuration; `run.cmd` starts the application without invoking a PowerShell script. `setup.sh` installs missing Debian/Ubuntu system prerequisites or uses Homebrew on macOS. Both setup paths build, stage the extension, and run native plus Python verification automatically.

## Verification performed

The release configuration was rebuilt from a fresh `build-win` directory on Windows with GCC 15.2, CMake 3.30.5, Ninja 1.12.1, and Python 3.12. All fetched libraries were compiled from source, with RtAudio using WASAPI and libsndfile linked statically.

A cross-platform environment collision was found and fixed during the final debug pass. The old Windows and WSL launchers shared `.venv`; running the Unix setup could therefore replace the Windows environment with a `/usr/bin/python3.12` reference and make `run.ps1` fail with exit code 103. Windows now exclusively uses `.venv-win`/`build-win`, Unix uses `.venv-unix`/`build-unix`, setup detects and recreates unusable environments, and launchers report a direct repair instruction if validation fails.

A second WSL-specific crash was fixed in the Song panel: on terminals wide enough to display more than 16 cells, the drawing loop used screen capacity instead of the actual song-slot count and called `get_pattern_at()` out of range. Rendering is now capped to `song_slot_count()`. Linux dependency detection was also corrected so the bundled libsndfile build no longer causes an unnecessary `sudo apt-get` prompt.

Audio startup now records the active RtAudio backend and the UI permanently shows `AUDIO` or `SILENT` in its top bar. On WSL, PulseAudio is attempted only when explicitly selected with `CONSOLESEQ_AUDIO_API=pulse`, avoiding a 30-second libpulse timeout when a stale WSLg server socket exists. A separate `README_RU.md` provides a complete Russian tutorial and an audio troubleshooting flow; native Windows/WASAPI is the recommended audio path on the verified host.

Verification results:

- CTest native engine suite: passed.
- Python headless smoke test: passed.
- Sixteen Python integration/UI tests: passed, including Unicode project paths, expanded JSON round trip, dynamic channels, pattern-reference repair after deletion, all 22 audible presets, mixer/song/pattern editing, copy/paste/clear, synth Tone/Drive/ADSR, broken-sample fallback, WAV resampling, pan/mute/song audio output, real audio lifecycle, an 18-channel scrolling check, and a 260-column Song-panel regression test.
- Real WASAPI check: RtAudio opened successfully and transport advanced to step 3 after 350 ms.
- Windows `setup.cmd`: completed the incremental build plus all native, smoke, and Python tests despite not requiring `.ps1` execution permission.
- Interactive curses PTY launch through `run.cmd`: opened WASAPI, added an `808 Kick` through the preset browser, changed it to `Sub Bass`, created and duplicated patterns, accepted `P`, advanced the transport while showing `PLAY`, and exited cleanly with `Q`.
- WSL build and launch: C++/Python suites passed with the ALSA/Pulse build; the actual curses UI remained stable at 260×40 and while switching into Song focus. Direct `/usr/bin/python3 main.py --smoke-test` also passed.

## Deliberate limitations

This is a compact sequencer rather than a production DAW. It has no recording, effects/plugins, automation, audio export, or graphical piano roll. Song length is 16 slots and projects are limited to 32 channels. Custom sample paths are referenced rather than embedded. These constraints do not affect the out-of-box demo, preset instruments, dynamic channels, synthesis, sequencing, playback, mixing, or save/load workflow.
