"""Import the native core, including an in-tree build during development."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


def _load_native():
    try:
        return importlib.import_module("console_seq.console_seq_core")
    except ImportError as first_error:
        root = Path(__file__).resolve().parents[1]
        candidates = [
            root / "build-win" / "python",
            root / "build-unix" / "python",
            root / "build" / "python",
        ]
        for build_dir in (root / "build-win", root / "build-unix", root / "build"):
            candidates.extend(build_dir.glob("python/*"))
        for candidate in candidates:
            if candidate.is_dir() and str(candidate) not in sys.path:
                sys.path.insert(0, str(candidate))
        try:
            return importlib.import_module("console_seq_core")
        except ImportError:
            raise ImportError(
                "ConsoleSeq's native module is not built. Run setup.ps1 on Windows "
                "or ./setup.sh on Linux/macOS."
            ) from first_error


_native = _load_native()

BUFFER_FRAMES = _native.BUFFER_FRAMES
SAMPLE_RATE = _native.SAMPLE_RATE
Channel = _native.Channel
ChannelType = _native.ChannelType
Engine = _native.Engine
Oscillator = _native.Oscillator
Pattern = _native.Pattern
Song = _native.Song
