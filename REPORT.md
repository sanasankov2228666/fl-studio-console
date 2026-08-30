# ConsoleSeq 1.3.2 implementation report

## Result

ConsoleSeq keeps its established four-panel curses workflow while adding a sampled instrument layer. The C++17 engine now embeds FluidSynth support and loads the bundled GeneralUser GS SoundFont. The original 60 generated/modelled presets remain available; 40 General MIDI presets add grand and electric pianos, organs, acoustic/electric guitars, live basses, strings, brass, winds, and five drum kits.

Three user-supplied kit directories were copied into the portable asset library. The instrument browser exposes 167 audio one-shots (163 WAV and 4 MP3) in 19 kit/folder tabs: Hard Times Detroit, Yakittido New Jazz, and Local drum_kits. Non-audio documents and DAW preset/project files from the source folders were not interpreted as instructions and were not exposed as sounds.

Pattern steps now store an optional duration. A normal `X` retains classic one-shot/natural-decay behavior. Pressing `E` on the `X` or any continuation cell enters length editing; Left/Right produces a colored `X ===` gate and `E`/Esc exits. Explicit gates stop procedural voices, SoundFont notes, and long user samples at the selected boundary. Durations survive copy/paste and project round trips.

Version 1.3.2 gives the Pattern cursor a dedicated black-on-white background instead of relying on underline support. The selected cell is therefore visible on active `X`, continuation `=`, and empty `.` cells independently of channel color and Windows terminal underline behavior. Popup rectangles are now fully painted with a separate blue background before their border and content are drawn, eliminating text bleed-through from Pattern, Song, Channels, and Mixer panels.

Every drum/sample voice now uses fractional playback position and linear interpolation. Per-step MIDI pitch controls transpose both user-loaded WAV/MP3 files and all bundled kit one-shots; an octave up doubles playback speed and an octave down halves it. The existing one-shot/gated-length behavior remains intact, and pitch editing from a continuation `=` resolves to the owning `X`.

The save prompt was replaced with a wide-character editor, fixing the Windows curses failure that produced filenames containing invalid U+FFFF characters. `.cseq` version 5 persists channel/preset data, SoundFont bank/program, mixer values, external sample paths, portable `asset://` kit references, patterns, pitch/velocity/duration values, and the full Song arrangement. Loading v4 projects includes a guarded drum-note migration so previously ignored default MIDI values cannot unexpectedly transpose old beats. Saving remains atomic through a temporary file plus replacement.

## Architecture and packaging

- FluidSynth is linked into the C++ engine and rendered inside the existing audio callback.
- GeneralUser GS, its license, the FluidSynth license, and all kit files are packaged as PyInstaller data.
- `console_seq/assets.py` resolves source-tree and frozen-EXE assets and provides the hierarchical sample catalog.
- Bundled samples save as portable `asset://drum_kits/...` references; external user files keep their filesystem paths.
- Windows setup downloads the official FluidSynth 2.6.0 SDK/runtime and GeneralUser GS when absent, builds the extension, stages the required DLLs, tests, and creates the one-file EXE.
- An Inno Setup definition and automatic `build_installer.cmd` create a per-user Windows installer with shortcuts, uninstall entry, project directory, and `.cseq` association. The portable single-file EXE remains available.
- Linux installs `libfluidsynth-dev`; macOS installs `fluid-synth` through Homebrew.

## Verification

Verified on 64-bit Windows with Python 3.12:

- native CTest suite: passed;
- 28 Python engine/UI integration tests: passed, including sample-pitch, legacy-project migration, opaque-popup, and high-contrast cursor regression tests;
- all 100 preset definitions rendered non-silent audio;
- GeneralUser GS loaded through FluidSynth and survived project save/load;
- all 167 bundled audio files decoded successfully (163 WAV, 4 MP3, zero failures);
- gated sample tail was silent while the same sample in one-shot mode remained audible;
- Unicode project path, atomic overwrite, and invalid-load state preservation tests passed;
- dynamic patterns/song banks, channel removal, copy/paste, duration editing, and wide Song-panel regression tests passed;
- standalone EXE smoke test checks procedural audio, FluidSynth/SF2, bundled WAV and MP3 decoding, and save/load from an isolated directory.
- installer test: silent per-user installation, installed-EXE smoke test, and clean uninstall all passed.

## Deliberate limitations

The sequencer currently stores one pitch per step and one active FluidSynth note per channel; it is not yet a graphical polyphonic piano roll. Sample transposition changes playback rate and duration; tempo-preserving time-stretch is not implemented. External user samples are referenced rather than copied into `.cseq`. Recording, VST plug-ins, automation lanes, effects chains, MIDI input, and WAV export remain roadmap items. The included kit audio was supplied by the project owner as free material; its original pack terms remain separate from the application-code license.
