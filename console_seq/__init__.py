"""ConsoleSeq terminal DAW."""

from .core import (
    BUFFER_FRAMES,
    SAMPLE_RATE,
    Channel,
    ChannelType,
    Engine,
    Oscillator,
    Pattern,
    Song,
    _native,
)

__all__ = [
    "BUFFER_FRAMES", "SAMPLE_RATE", "Channel", "ChannelType", "Engine",
    "Oscillator", "Pattern", "Song",
]

__version__ = getattr(_native, "__version__", "development")
