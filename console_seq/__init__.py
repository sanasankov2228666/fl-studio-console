"""ConsoleSeq terminal DAW."""

from .core import BUFFER_FRAMES, SAMPLE_RATE, Channel, ChannelType, Engine, Oscillator, Pattern, Song

__all__ = [
    "BUFFER_FRAMES", "SAMPLE_RATE", "Channel", "ChannelType", "Engine",
    "Oscillator", "Pattern", "Song",
]

try:
    from .console_seq_core import __version__
except ImportError:
    __version__ = "development"
