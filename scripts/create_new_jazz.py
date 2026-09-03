"""Generate the bundled new_jazz.cseq demo arrangement."""

from __future__ import annotations

import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from console_seq import Engine  # noqa: E402
from console_seq.assets import asset_root, default_soundfont, sample_catalog  # noqa: E402


def select_sample(category_ending: str, name_fragment: str) -> Path:
    matches = [path for _preset, name, category, path in sample_catalog()
               if category.endswith(category_ending) and name_fragment.casefold() in name.casefold()]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected one sample for {category_ending!r}/{name_fragment!r}, got {len(matches)}"
        )
    return matches[0]


def generate(destination: Path) -> dict[str, float | int | str]:
    engine = Engine()
    engine.set_asset_root(str(asset_root()))
    if not engine.set_soundfont(str(default_soundfont())):
        raise RuntimeError(engine.soundfont_status())
    engine.set_bpm(130.0)
    engine.set_loop(True)

    # Start with one channel so all following channels are created in a stable,
    # documented order. Sample paths are converted to asset:// references on save.
    for channel in range(engine.channel_count() - 1, 0, -1):
        engine.remove_channel(channel)
    engine.set_channel_preset(0, "perc_click")

    samples = {
        "kick": select_sample("/ Kick", "Racks 1.0"),
        "snare": select_sample("/ snare", "destroy lonely snare"),
        "clap": select_sample("/ clap", "favorite clap"),
        "hat": select_sample("/ hi-hat", "hard hi-hat"),
        "open_hat": select_sample("/ open hat", "short open hat"),
        "crash": select_sample("/ crash", "new jazz crash"),
        "fx": select_sample("/ fx", "plugg ice fx"),
        "bass": select_sample("/ 808", "new jazz 808"),
    }

    def sample_channel(name: str, sample: Path, volume: float, pan: float = 0.0,
                       root: int = 60, first: bool = False) -> int:
        channel = 0 if first else engine.add_channel("perc_click", name)
        engine.set_channel_name(channel, name)
        engine.set_channel_base_note(channel, root)
        engine.set_channel_volume(channel, volume)
        engine.set_channel_pan(channel, pan)
        if not engine.set_channel_sample(channel, str(sample)):
            raise RuntimeError(f"Could not load {sample}: {engine.last_error()}")
        return channel

    kick = sample_channel("NJ Kick - Racks", samples["kick"], 0.82, root=36, first=True)
    snare = sample_channel("NJ Snare - Lonely", samples["snare"], 0.56, -0.04)
    clap = sample_channel("NJ Clap - Favorite", samples["clap"], 0.34, 0.08)
    hat = sample_channel("NJ Closed Hat", samples["hat"], 0.28, 0.18)
    roll_hat = engine.add_channel("hihat_roll", "NJ Hat Roll")
    open_hat = sample_channel("NJ Open Hat", samples["open_hat"], 0.23, -0.25)
    perc = engine.add_channel("perc_newjazz", "NJ Percussion")
    crash = sample_channel("NJ Crash", samples["crash"], 0.20, -0.12)
    fx = sample_channel("NJ Ice FX", samples["fx"], 0.15, 0.32)
    bass = sample_channel("NJ 808", samples["bass"], 0.64, root=36)

    engine.set_channel_volume(roll_hat, 0.20)
    engine.set_channel_pan(roll_hat, -0.18)
    engine.set_channel_volume(perc, 0.18)
    engine.set_channel_pan(perc, 0.40)

    rhodes = []
    for index, pan in enumerate((-0.36, -0.12, 0.12, 0.36), start=1):
        channel = engine.add_channel("sf_rhodes", f"Rhodes Voice {index}")
        engine.set_channel_volume(channel, 0.145)
        engine.set_channel_pan(channel, pan)
        rhodes.append(channel)

    pluck = engine.add_channel("pluck_newjazz", "New Jazz Pluck")
    bell = engine.add_channel("fm_bell", "Glass Bell")
    guitar = engine.add_channel("sf_jazz_guitar", "Jazz Guitar")
    pad = engine.add_channel("pad_warm", "Warm Atmosphere")
    engine.set_channel_volume(pluck, 0.23)
    engine.set_channel_pan(pluck, 0.22)
    engine.set_channel_volume(bell, 0.13)
    engine.set_channel_pan(bell, -0.32)
    engine.set_channel_volume(guitar, 0.16)
    engine.set_channel_pan(guitar, 0.30)
    engine.set_channel_volume(pad, 0.105)
    engine.set_channel_pan(pad, -0.10)

    pattern_names = [
        "Intro - Rhodes", "Main A", "Main B", "Main A Fill",
        "Breakdown", "Drop A", "Drop B", "Outro",
    ]
    while engine.pattern_count() < len(pattern_names):
        engine.add_pattern()
    while engine.pattern_count() > len(pattern_names):
        engine.remove_pattern(engine.pattern_count() - 1)
    for pattern, name in enumerate(pattern_names):
        engine.set_pattern_name(pattern, name)
        engine.clear_pattern(pattern)

    def hit(pattern: int, channel: int, step: int, note: int | None = None,
            velocity: float = 1.0, duration: int = 0) -> None:
        engine.set_step(pattern, channel, step, True)
        if note is not None:
            engine.set_note(pattern, channel, step, note)
        engine.set_velocity(pattern, channel, step, velocity)
        engine.set_duration(pattern, channel, step, duration)

    # Four-note upper structures. The 808 supplies the changing low root.
    c_sharp_m9 = (52, 56, 59, 63)  # E3 G#3 B3 D#4
    a_maj9 = (49, 52, 56, 59)      # C#3 E3 G#3 B3
    f_sharp_m9 = (45, 49, 52, 56)  # A2 C#3 E3 G#3
    g_sharp_7b9 = (48, 51, 54, 57) # C3 D#3 F#3 A3

    def harmony(pattern: int, first: tuple[int, ...], second: tuple[int, ...],
                pad_roots: tuple[int, int], velocity: float = 0.72) -> None:
        for voice, channel in enumerate(rhodes):
            hit(pattern, channel, 0, first[voice], velocity, 8)
            hit(pattern, channel, 8, second[voice], velocity * 0.94, 8)
        hit(pattern, pad, 0, pad_roots[0], 0.48, 8)
        hit(pattern, pad, 8, pad_roots[1], 0.44, 8)

    for pattern in (0, 1, 3, 5, 7):
        harmony(pattern, c_sharp_m9, a_maj9, (49, 45), 0.67 if pattern in (0, 7) else 0.74)
    for pattern in (2, 4, 6):
        harmony(pattern, f_sharp_m9, g_sharp_7b9, (42, 44), 0.65 if pattern == 4 else 0.74)

    def hats(pattern: int, dense: bool = False) -> None:
        steps = list(range(0, 16, 2))
        if dense:
            steps += [9, 11, 13, 14, 15]
        for step in sorted(set(steps)):
            hit(pattern, hat, step, 60, 0.58 if step % 4 == 0 else 0.40)
        hit(pattern, roll_hat, 7, 60, 0.42)
        hit(pattern, roll_hat, 15, 64, 0.56)

    def backbeat(pattern: int, fill: bool = False) -> None:
        hit(pattern, snare, 4, 60, 0.88)
        hit(pattern, snare, 12, 60, 0.95)
        hit(pattern, clap, 12, 60, 0.64)
        if fill:
            hit(pattern, snare, 14, 62, 0.56)
            hit(pattern, clap, 15, 64, 0.48)

    # Intro: musical hook and ear candy, with a deliberately late drum pickup.
    hit(0, fx, 0, 60, 0.72)
    hit(0, bell, 6, 80, 0.52, 2)
    hit(0, bell, 14, 75, 0.44, 2)
    hit(0, guitar, 3, 68, 0.52, 3)
    hit(0, guitar, 11, 64, 0.46, 3)
    for step in (10, 12, 14, 15):
        hit(0, hat, step, 60 + (step == 15) * 3, 0.30 + 0.05 * (step - 10))
    hit(0, open_hat, 15, 60, 0.45)

    # Main A: syncopated kick/808 around C#m9 -> Amaj9.
    hats(1)
    backbeat(1)
    for step, velocity in ((0, 0.96), (3, 0.78), (7, 0.90), (10, 0.76), (14, 0.92)):
        hit(1, kick, step, 36, velocity)
    for step, note, duration, velocity in (
        (0, 37, 4, 0.90), (7, 40, 2, 0.76), (10, 33, 3, 0.84), (14, 35, 2, 0.78)
    ):
        hit(1, bass, step, note, velocity, duration)
    for step, note in ((2, 68), (5, 71), (7, 73), (10, 76), (14, 75)):
        hit(1, pluck, step, note, 0.60, 1)
    hit(1, open_hat, 6, 60, 0.64)
    hit(1, perc, 11, 60, 0.46)
    hit(1, guitar, 3, 64, 0.42, 2)

    # Main B: turnaround and a more ascending bass answer.
    hats(2)
    backbeat(2)
    for step, velocity in ((0, 0.90), (5, 0.82), (8, 0.94), (11, 0.72), (15, 0.88)):
        hit(2, kick, step, 36, velocity)
    for step, note, duration, velocity in (
        (0, 42, 4, 0.88), (5, 40, 3, 0.72), (8, 44, 3, 0.86), (11, 35, 3, 0.76), (15, 36, 1, 0.72)
    ):
        hit(2, bass, step, note, velocity, duration)
    for step, note in ((1, 69), (4, 73), (7, 76), (11, 78), (15, 75)):
        hit(2, pluck, step, note, 0.58, 1)
    hit(2, open_hat, 10, 60, 0.60)
    hit(2, perc, 3, 60, 0.40)
    hit(2, perc, 13, 64, 0.48)
    hit(2, guitar, 9, 63, 0.46, 3)

    # Fill bar: familiar harmony with a dense final-quarter lift.
    hats(3, dense=True)
    backbeat(3, fill=True)
    for step, velocity in ((0, 0.96), (3, 0.74), (6, 0.86), (10, 0.84), (13, 0.78), (15, 0.90)):
        hit(3, kick, step, 36, velocity)
    for step, note, duration in ((0, 37, 3), (6, 40, 3), (10, 33, 3), (13, 35, 2), (15, 37, 1)):
        hit(3, bass, step, note, 0.82, duration)
    for step, note in ((8, 76), (10, 75), (12, 73), (13, 75), (14, 76), (15, 80)):
        hit(3, pluck, step, note, 0.58 + 0.03 * (step - 8), 1)
    hit(3, open_hat, 15, 63, 0.72)
    hit(3, crash, 15, 60, 0.36)

    # Breakdown keeps motion but opens space for vocals or a new lead.
    for step in (2, 6, 10, 14):
        hit(4, hat, step, 60, 0.30)
    hit(4, clap, 12, 60, 0.42)
    hit(4, bass, 0, 42, 0.55, 6)
    hit(4, bass, 10, 44, 0.50, 4)
    hit(4, guitar, 2, 69, 0.54, 4)
    hit(4, guitar, 10, 68, 0.48, 4)
    hit(4, bell, 7, 81, 0.46, 2)
    hit(4, fx, 14, 67, 0.32)

    # Drop A/B reuse the motifs with harder drums and extra accents.
    for target, source in ((5, 1), (6, 2)):
        for channel in range(engine.channel_count()):
            for step in range(16):
                if engine.get_step(source, channel, step):
                    hit(target, channel, step,
                        engine.get_note(source, channel, step),
                        engine.get_velocity(source, channel, step),
                        engine.get_duration(source, channel, step))
        hit(target, crash, 0, 60, 0.70)
        hit(target, kick, 12 if target == 5 else 13, 36, 0.82)
        hit(target, perc, 5, 64, 0.52)
        hit(target, bell, 6, 80 if target == 5 else 81, 0.48, 2)
        hit(target, roll_hat, 14, 67, 0.62)

    # Outro resolves to the initial harmony and removes the low end.
    hit(7, fx, 0, 55, 0.38)
    for step in (0, 4, 8, 12):
        hit(7, hat, step, 60, 0.24)
    hit(7, guitar, 3, 68, 0.48, 4)
    hit(7, guitar, 11, 64, 0.40, 4)
    hit(7, bell, 14, 73, 0.34, 2)

    arrangement = [
        0, 0, 1, 2, 1, 3,
        1, 2, 5, 6, 5, 3,
        4, 4, 1, 2, 5, 6,
        5, 3, 1, 2, 7, 7,
    ]
    engine.set_song_slot_count(len(arrangement))
    for channel in range(engine.channel_count()):
        for slot, pattern in enumerate(arrangement):
            engine.set_pattern_at(channel, slot, pattern)
    engine.set_current_pattern(1)
    engine.set_song_mode(True)

    destination = destination.resolve()
    if not engine.save_project(str(destination)):
        raise RuntimeError(engine.last_error())

    # Validate the exact file from disk and render enough audio to cover intro
    # and the first main-groove transition.
    probe = Engine()
    probe.set_asset_root(str(asset_root()))
    if not probe.set_soundfont(str(default_soundfont())):
        raise RuntimeError(probe.soundfont_status())
    if not probe.load_project(str(destination)):
        raise RuntimeError(probe.last_error())
    audio = probe.render_offline(10.0)
    peak = max(abs(value) for value in audio)
    rms = math.sqrt(sum(value * value for value in audio) / len(audio))
    if peak < 0.05 or rms < 0.005:
        raise RuntimeError(f"Rendered project is unexpectedly silent (peak={peak}, rms={rms})")
    return {
        "path": str(destination),
        "bpm": int(probe.bpm()),
        "channels": probe.channel_count(),
        "patterns": probe.pattern_count(),
        "song_slots": probe.song_slot_count(),
        "peak": peak,
        "rms": rms,
    }


if __name__ == "__main__":
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "new_jazz.cseq"
    result = generate(output)
    for key, value in result.items():
        print(f"{key}: {value}")
