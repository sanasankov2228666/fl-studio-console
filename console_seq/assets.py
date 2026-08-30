"""Resolve bundled assets in source checkouts and frozen ConsoleSeq builds."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterator


def asset_root() -> Path:
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        return Path(frozen_root) / "assets"
    return Path(__file__).resolve().parents[1] / "assets"


def default_soundfont() -> Path:
    return asset_root() / "soundfonts" / "GeneralUser-GS.sf2"


def sample_catalog() -> Iterator[tuple[str, str, str, Path]]:
    """Yield id, display name, category, and absolute file for bundled kits."""
    root = asset_root() / "drum_kits"
    if not root.is_dir():
        return
    for path in sorted(root.rglob("*"), key=lambda item: str(item).casefold()):
        if not path.is_file() or path.suffix.lower() not in {".wav", ".mp3"}:
            continue
        relative = path.relative_to(root)
        parts = relative.parts
        bank = parts[0]
        folders = list(parts[1:-1])
        # The Yakittido archive contains a wrapper directory repeating the kit
        # name. Keep it on disk verbatim, but hide that redundant level in UI.
        if bank == "Yakittido New Jazz" and folders and folders[0].startswith("@prod.yakittido"):
            folders.pop(0)
        folder = " / ".join(folders)
        category = f"Kit: {bank}" + (f" / {folder}" if folder else "")
        preset_id = "sample::" + relative.as_posix()
        yield preset_id, path.stem, category, path


def resolve_sample_id(preset_id: str) -> Path | None:
    prefix = "sample::"
    if not preset_id.startswith(prefix):
        return None
    relative = Path(preset_id[len(prefix):])
    if relative.is_absolute() or ".." in relative.parts:
        return None
    candidate = (asset_root() / "drum_kits" / relative).resolve()
    root = (asset_root() / "drum_kits").resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate
