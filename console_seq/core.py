"""Import the native core, including an in-tree build during development."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


def _load_native():
    root = Path(__file__).resolve().parents[1]
    candidates = [
        root / "build-win" / "python",
        root / "build-unix" / "python",
        root / "build" / "python",
    ]
    for build_dir in (root / "build-win", root / "build-unix", root / "build"):
        candidates.extend(build_dir.glob("python/*"))
    valid_candidates = [str(candidate) for candidate in candidates
                        if candidate.is_dir() and str(candidate) not in sys.path]
    sys.path[:0] = valid_candidates
    try:
        return importlib.import_module("console_seq_core")
    except ImportError as build_error:
        try:
            return importlib.import_module("console_seq.console_seq_core")
        except ImportError:
            raise ImportError(
                "ConsoleSeq's native module is not built. Run setup.ps1 on Windows "
                "or ./setup.sh on Linux/macOS."
            ) from build_error


_native = _load_native()

BUFFER_FRAMES = _native.BUFFER_FRAMES
SAMPLE_RATE = _native.SAMPLE_RATE
Channel = _native.Channel
ChannelType = _native.ChannelType
Engine = _native.Engine
Oscillator = _native.Oscillator
Pattern = _native.Pattern
Song = _native.Song
