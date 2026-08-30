from __future__ import annotations

import base64
import json
import math
import tempfile
import time
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

from console_seq import ChannelType, Engine, Pattern, Song
from console_seq.ui import ConsoleSeqUI
from console_seq.assets import asset_root, default_soundfont, sample_catalog
import curses


_TEST_MP3 = base64.b64decode(
    "//tQxAAACkA1PHWTAAFnlax3NNACAUbckNFE0TTJDVGFhDQaOKQ4mjQCQrWHTHUHWOzty4fl4QQBAAEECCAJg+D4Pn4IAhrB8/lAxKe/o9/R7+gpggD5+XAgYwwD76wIGNAPvynv6AAANdQKBQMBQMBQKBgH2ITGA6M4wJA2sRENkyDZxURn0C3uuNsEdAdPgOUSYL1+F2HaMKML/ifCNBdh2jC/+SJkXi8iXf/x6mReLxiXS7/UDQlCQNf8qd//0gBQAYDQBYmA4AWJgywOyf/7UsQHggsoKQy98YABQwShyc/wUICYDOGBmhGxtb+dSapIZBmNCCGJhlASKYL6DxGDZg1Bg7ILUYE2BGJ9NTWLLZcND1ChdemY3Vv0U6tn/q+g5/V1b9On6vTr//3FIBAQwmGTLhmNdtM7NtjDRRVM1XijzNT3FVzDVAeYwY0FDMDTA6zXzQNf2szqawEIFjv5G5YCdeNLMUxWrR9Pdb/1L1aG+j0ft3b/92qv/X3JAAAzB6rMhkwyUaTNasNeVkwcEQ8Mv6hMDLqxCQwZoEnM//tSxBCCCnglFS5/YoF2hSGV/+yQBfARDAIAC02tYOMvTWi8OEnFl17gtl7Fe/1fIZSxvrd6N69mS/uin+ncuc7sV0rejYigUAGAQACxgOoDiYG8B0GDSg8ph6Qu0bILZ2Gw2C8Bh8YQ+YOYC4GB4AiBga4HuYGoDVHBQBioKqRy4YjdvjRQUQBKUV3JxUxsmPs+71adJ9Xb456293t+rj9FVTO1FQAAMgWWTJxbMrn4zwzTaOUMHsE8zNIZp8zMgTXMHBBXjAYgF0wDEAuOCYz/+1LEFYIJkCMTLn9igWqFYYK+MADqdA282DB1p0VtDttd9dH2+vs/36v3a//oT2J/t+pz//6DAFACMwFEC/MFxBPTBQAwgwzIZGN9Wo4zbVzXUx0UUVMPdB1TBMQlcwhkHjMIFB4TAdQKcBAGaI7DIpDgQQlswf7CD5DY/ff6//t0a79fbfo26P6ujui9qNf0KgAAL7bLrvN6Nf8LhB6IaAEplAocjLxE9K4TE3cVNiGK7R/ORzjSvXRN0AOxC0dMirMsLFwDkD5BcpDhczuqHP/7UsQfgBF0+WG5qRAQ1AWjH54wBKBZWRMvkWMSKkVbydGXImK0FAE0RYgRiXfycHPJ8ghFC6kklU9VsiAuMg5PkENEEll0umReL3/fpuggxiXS6kkZLBX6bv/6flDh9AAUSnXL0ULcLkhS5NFZP4epUqY6ma717F1VAVdlst1nemHa3UQ7DvK/q8S/LPo//+Iv8GoNVMQU1FMy4xMDBVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV" + "V"
)


class ConsoleSeqCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = Engine()

    def test_default_project_and_editing(self) -> None:
        self.assertEqual(self.engine.channel_count(), 5)
        self.assertEqual([self.engine.get_channel(i).name for i in range(5)],
                         ["Kick", "Snare", "HiHat", "Piano", "Bass"])
        self.assertEqual(self.engine.get_channel(0).type, ChannelType.DRUM)
        self.assertTrue(self.engine.get_step(0, 0, 0))
        for channel_index in range(self.engine.channel_count()):
            root = self.engine.get_channel(channel_index).base_note
            self.assertEqual(self.engine.get_note(0, channel_index, 1), root)
        self.engine.set_step(0, 3, 3, True)
        self.engine.set_note(0, 3, 3, 65)
        self.engine.set_velocity(0, 3, 3, 0.55)
        self.engine.set_duration(0, 3, 3, 4)
        self.assertTrue(self.engine.get_step(0, 3, 3))
        self.assertEqual(self.engine.get_note(0, 3, 3), 65)
        self.assertAlmostEqual(self.engine.get_velocity(0, 3, 3), 0.55, places=4)
        self.assertEqual(self.engine.get_duration(0, 3, 3), 4)

    def test_pattern_sizes_song_and_mixer(self) -> None:
        self.engine.set_step_count(32)
        self.assertEqual(self.engine.step_count(), 32)
        self.assertTrue(self.engine.get_step(0, 0, 0))
        self.engine.set_pattern_at(4, 9, 2)
        self.assertEqual(self.engine.get_pattern_at(4, 9), 2)
        self.engine.set_channel_volume(4, 0.25)
        self.engine.set_channel_pan(4, 0.7)
        self.engine.set_channel_mute(4, True)
        bass = self.engine.get_channel(4)
        self.assertAlmostEqual(bass.volume, 0.25)
        self.assertAlmostEqual(bass.pan, 0.7)
        self.assertTrue(bass.mute)

    def test_project_round_trip_in_unicode_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ConsoleSeq-тест-") as directory:
            path = Path(directory) / "проект.cseq"
            self.engine.set_bpm(137.5)
            self.engine.set_channel_solo(3, True)
            self.assertTrue(self.engine.save_project(str(path)), self.engine.last_error())
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["format"], "ConsoleSeq")
            self.assertEqual(len(data["channels"]), 5)
            self.engine.new_project()
            self.assertTrue(self.engine.load_project(str(path)), self.engine.last_error())
            self.assertAlmostEqual(self.engine.bpm(), 137.5)
            self.assertTrue(self.engine.get_channel(3).solo)

    def test_legacy_v4_drum_notes_migrate_to_channel_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "legacy-v4.cseq"
            self.assertTrue(self.engine.save_project(str(path)), self.engine.last_error())
            data = json.loads(path.read_text(encoding="utf-8"))
            data["version"] = 4
            for pattern in data["patterns"]:
                for step in pattern["grid"][0]:
                    step["note"] = 60
            data["patterns"][0]["grid"][0][0]["note"] = 61
            path.write_text(json.dumps(data), encoding="utf-8")

            loaded = Engine()
            self.assertTrue(loaded.load_project(str(path)), loaded.last_error())
            kick_root = loaded.get_channel(0).base_note
            self.assertEqual(kick_root, 36)
            self.assertEqual(loaded.get_note(0, 0, 0), kick_root + 1)
            self.assertEqual(loaded.get_note(0, 0, 1), kick_root)

    def test_load_mono_wav_and_render(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            wav_path = Path(directory) / "sample.wav"
            frames = bytearray()
            for index in range(2205):
                sample = int(12000 * math.sin(2 * math.pi * 440 * index / 22050))
                frames.extend(sample.to_bytes(2, "little", signed=True))
            with wave.open(str(wav_path), "wb") as output:
                output.setnchannels(1)
                output.setsampwidth(2)
                output.setframerate(22050)
                output.writeframes(frames)
            self.assertTrue(self.engine.set_channel_sample(0, str(wav_path)), self.engine.last_error())
            self.assertEqual(self.engine.get_channel(0).sample_path, str(wav_path))
            audio = self.engine.render_offline(0.2)
            self.assertEqual(len(audio), int(44100 * 0.2) * 2)
            self.assertGreater(max(abs(value) for value in audio), 0.01)

    def test_gated_sample_is_cut_at_selected_step_length(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            wav_path = Path(directory) / "long.wav"
            with wave.open(str(wav_path), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(44100)
                sample = int(0.45 * 32767).to_bytes(2, "little", signed=True)
                wav.writeframes(sample * 22050)
            self.engine.clear_pattern(0)
            for channel in range(self.engine.channel_count()):
                self.engine.set_channel_mute(channel, True)
            channel = self.engine.add_channel("perc_click")
            self.assertTrue(self.engine.set_channel_sample(channel, str(wav_path)))
            self.engine.set_channel_mute(channel, False)
            self.engine.set_step(0, channel, 0, True)
            self.engine.set_duration(0, channel, 0, 1)
            gated = self.engine.render_offline(0.30)
            tail_start = int(0.15 * 44100) * 2
            self.assertLess(max(abs(value) for value in gated[tail_start:]), 0.0001)
            self.engine.set_duration(0, channel, 0, 0)
            one_shot = self.engine.render_offline(0.30)
            self.assertGreater(max(abs(value) for value in one_shot[tail_start:]), 0.1)
            self.assertLessEqual(max(abs(value) for value in one_shot), 1.0)

    def test_custom_sample_pitch_changes_playback_rate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            wav_path = Path(directory) / "pitched.wav"
            with wave.open(str(wav_path), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(44100)
                sample = int(0.40 * 32767).to_bytes(2, "little", signed=True)
                wav.writeframes(sample * 22050)  # 0.5 seconds
            self.engine.clear_pattern(0)
            for channel_index in range(self.engine.channel_count()):
                self.engine.set_channel_mute(channel_index, True)
            channel = self.engine.add_channel("perc_click", "Pitched sample")
            self.assertTrue(self.engine.set_channel_sample(channel, str(wav_path)))
            root = self.engine.get_channel(channel).base_note
            self.engine.set_step(0, channel, 0, True)
            self.engine.set_note(0, channel, 0, root)
            original = self.engine.render_offline(0.36)
            tail = int(0.30 * 44100) * 2
            self.assertGreater(max(abs(value) for value in original[tail:]), 0.1)
            self.engine.set_note(0, channel, 0, root + 12)
            octave_up = self.engine.render_offline(0.36)
            self.assertLess(max(abs(value) for value in octave_up[tail:]), 0.0001)

    def test_load_mp3_and_render(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ConsoleSeq-mp3-") as directory:
            mp3_path = Path(directory) / "user sample.mp3"
            mp3_path.write_bytes(_TEST_MP3)
            self.assertTrue(self.engine.set_channel_sample(0, str(mp3_path)), self.engine.last_error())
            self.assertEqual(self.engine.get_channel(0).sample_path, str(mp3_path))
            audio = self.engine.render_offline(0.18)
            self.assertGreater(max(abs(value) for value in audio), 0.01)

    def test_standalone_api_objects(self) -> None:
        pattern = Pattern(2, 16, "Unit")
        pattern.set_step(1, 7, True)
        pattern.set_note(1, 7, 72)
        self.assertTrue(pattern.get_step(1, 7))
        self.assertEqual(pattern.get_note(1, 7), 72)
        song = Song(2, 8)
        song.set_pattern_at(1, 3, 4)
        self.assertEqual(song.get_pattern_at(1, 3), 4)

    def test_audio_lifecycle(self) -> None:
        self.engine.start()
        self.assertTrue(
            self.engine.audio_status().startswith(("RtAudio output active", "silent timing mode")),
            self.engine.audio_status(),
        )
        self.engine.play()
        deadline = time.monotonic() + 2.0
        while self.engine.current_step() < 1 and time.monotonic() < deadline:
            time.sleep(0.05)
        self.assertGreaterEqual(self.engine.current_step(), 1)
        self.engine.pause()
        paused_step = self.engine.current_step()
        time.sleep(0.16)
        self.assertEqual(self.engine.current_step(), paused_step)
        self.engine.play()
        time.sleep(0.16)
        self.engine.stop()
        self.engine.shutdown()
        self.assertFalse(self.engine.is_playing())
        self.assertTrue(self.engine.audio_status())

    def test_bpm_loop_pattern_creation_and_synth_parameters(self) -> None:
        self.engine.set_bpm(999)
        self.assertEqual(self.engine.bpm(), 300)
        self.engine.set_bpm(1)
        self.assertEqual(self.engine.bpm(), 40)
        self.engine.set_loop(False)
        self.assertFalse(self.engine.loop())
        duplicate = self.engine.duplicate_pattern(0)
        self.assertEqual(duplicate, 4)
        self.assertEqual(self.engine.get_pattern(duplicate).name, "Demo Beat Copy")
        created = self.engine.add_pattern("Bridge")
        self.assertEqual(self.engine.get_pattern(created).name, "Bridge")
        for channel_index in range(self.engine.channel_count()):
            self.assertEqual(
                self.engine.get_note(created, channel_index, 0),
                self.engine.get_channel(channel_index).base_note,
            )
        self.engine.set_synth_param(4, "oscillator", 1)
        self.engine.set_synth_param(4, "attack", 0.1)
        self.engine.set_synth_param(4, "decay", 0.2)
        self.engine.set_synth_param(4, "sustain", 0.6)
        self.engine.set_synth_param(4, "release", 0.3)
        self.engine.set_synth_param(4, "base_note", 41)
        bass = self.engine.get_channel(4)
        self.assertEqual(str(bass.oscillator).split(".")[-1], "SQUARE")
        self.assertEqual(bass.base_note, 41)
        for actual, expected in zip(bass.adsr, (0.1, 0.2, 0.6, 0.3)):
            self.assertAlmostEqual(actual, expected, places=4)

    def test_instrument_presets_and_dynamic_channels(self) -> None:
        presets = self.engine.preset_ids()
        self.assertEqual(len(presets), 100)
        catalog = self.engine.preset_catalog()
        self.assertEqual(len(catalog), 100)
        categories = {category for _preset_id, _name, category in catalog}
        self.assertTrue({"Pianos", "Kicks", "Basses", "Guitars", "Strings",
                         "Synths", "Snares", "Hi-hats", "Percussion", "FX",
                         "Live Pianos", "Live Guitars", "Live Basses", "Live Drums",
                         "Live Organs", "Orchestral", "Brass & Winds"}.issubset(categories))
        for required in ("piano_classic", "guitar_acoustic", "kick_trap_hard",
                         "bass_808_long", "fm_bell", "perc_newjazz", "fx_riser"):
            self.assertIn(required, presets)
        added = self.engine.add_channel("kick_808", "Extra 808")
        self.assertEqual(added, 5)
        self.assertEqual(self.engine.channel_count(), 6)
        self.assertEqual(self.engine.get_pattern(0).channel_count, 6)
        self.assertEqual(self.engine.get_song().channel_count, 6)
        self.assertEqual(self.engine.get_channel(added).builtin_id, "kick_808")
        self.engine.set_step(0, added, 0, True)
        self.assertGreater(max(abs(value) for value in self.engine.render_offline(0.15)), 0.01)

        clone = self.engine.duplicate_channel(added)
        self.assertEqual(clone, 6)
        self.assertTrue(self.engine.get_step(0, clone, 0))
        self.engine.set_channel_preset(added, "bass_sub")
        self.assertEqual(self.engine.get_channel(added).name, "Sub Bass")
        self.engine.set_synth_param(added, "tone", 0.33)
        self.engine.set_synth_param(added, "drive", 0.44)
        self.assertAlmostEqual(self.engine.get_channel(added).tone, 0.33, places=4)
        self.assertAlmostEqual(self.engine.get_channel(added).drive, 0.44, places=4)
        self.engine.remove_channel(clone)
        self.assertEqual(self.engine.channel_count(), 6)

    def test_every_builtin_preset_renders_audio(self) -> None:
        for preset in self.engine.preset_ids():
            engine = Engine()
            self.assertTrue(engine.set_soundfont(str(default_soundfont())), engine.last_error())
            engine.clear_pattern(0)
            for channel in range(engine.channel_count()):
                engine.set_channel_mute(channel, True)
            added = engine.add_channel(preset)
            engine.set_step(0, added, 0, True)
            engine.set_channel_mute(added, False)
            peak = max(abs(value) for value in engine.render_offline(0.12))
            self.assertGreater(peak, 0.001, preset)

    def test_fluidsynth_duration_and_project_round_trip(self) -> None:
        self.assertTrue(self.engine.set_soundfont(str(default_soundfont())), self.engine.last_error())
        channel = self.engine.add_channel("sf_grand_piano")
        self.engine.set_step(0, channel, 0, True)
        self.engine.set_note(0, channel, 0, 64)
        self.engine.set_duration(0, channel, 0, 4)
        self.assertGreater(max(abs(value) for value in self.engine.render_offline(0.6)), 0.01)
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "живое пианино.cseq"
            self.assertTrue(self.engine.save_project(str(project)), self.engine.last_error())
            loaded = Engine()
            loaded.set_soundfont(str(default_soundfont()))
            self.assertTrue(loaded.load_project(str(project)), loaded.last_error())
            self.assertEqual(loaded.get_duration(0, channel, 0), 4)
            self.assertEqual(loaded.get_channel(channel).soundfont_program, 0)

    def test_bundled_sample_catalog_and_portable_reference(self) -> None:
        catalog = list(sample_catalog())
        self.assertEqual(len(catalog), 167)
        self.engine.set_asset_root(str(asset_root()))
        preset_id, _name, category, sample = catalog[0]
        self.assertTrue(preset_id.startswith("sample::"))
        self.assertTrue(category.startswith("Kit:"))
        channel = self.engine.add_channel("perc_click")
        self.assertTrue(self.engine.set_channel_sample(channel, str(sample)), self.engine.last_error())
        self.assertTrue(self.engine.get_channel(channel).sample_path.startswith("asset://"))
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "sample-bank.cseq"
            self.assertTrue(self.engine.save_project(str(project)), self.engine.last_error())
            loaded = Engine()
            loaded.set_asset_root(str(asset_root()))
            self.assertTrue(loaded.load_project(str(project)), loaded.last_error())
            self.assertTrue(loaded.get_channel(channel).sample_path.startswith("asset://"))
            self.assertGreater(max(abs(value) for value in loaded.render_offline(0.2)), 0.001)

    def test_channel_and_pattern_changes_survive_round_trip(self) -> None:
        added = self.engine.add_channel("pad_warm")
        self.engine.set_channel_name(added, "Atmosphere")
        self.engine.set_synth_param(added, "tone", 0.21)
        pattern = self.engine.duplicate_pattern(0)
        self.engine.set_pattern_name(pattern, "Chorus")
        self.engine.set_song_slot_count(64)
        self.engine.set_pattern_at(added, 47, pattern)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "expanded.cseq"
            self.assertTrue(self.engine.save_project(str(path)), self.engine.last_error())
            restored = Engine()
            self.assertTrue(restored.load_project(str(path)), restored.last_error())
            self.assertEqual(restored.channel_count(), 6)
            self.assertEqual(restored.get_channel(added).name, "Atmosphere")
            self.assertEqual(restored.get_channel(added).builtin_id, "pad_warm")
            self.assertAlmostEqual(restored.get_channel(added).tone, 0.21, places=4)
            self.assertEqual(restored.get_pattern(pattern).name, "Chorus")
            self.assertEqual(restored.song_slot_count(), 64)
            self.assertEqual(restored.get_pattern_at(added, 47), pattern)
            restored.remove_pattern(pattern)
            self.assertEqual(restored.get_pattern_at(added, 47), -1)

    def test_atomic_save_overwrite_and_pattern_banks(self) -> None:
        first = self.engine.add_pattern_bank()
        self.assertEqual(first, 4)
        self.assertEqual(self.engine.pattern_count(), 20)
        self.engine.set_song_slot_count(48)
        self.engine.set_pattern_at(0, 31, 19)
        with tempfile.TemporaryDirectory(prefix="ConsoleSeq-save-") as directory:
            path = Path(directory) / "nested" / "song.cseq"
            self.assertTrue(self.engine.save_project(str(path)), self.engine.last_error())
            self.assertFalse(Path(str(path) + ".tmp").exists())
            self.engine.set_bpm(151)
            self.assertTrue(self.engine.save_project(str(path)), self.engine.last_error())
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["bpm"], 151)
            restored = Engine()
            self.assertTrue(restored.load_project(str(path)), restored.last_error())
            self.assertEqual(restored.pattern_count(), 20)
            self.assertEqual(restored.song_slot_count(), 48)
            self.assertEqual(restored.get_pattern_at(0, 31), 19)

    def test_mute_solo_pan_and_song_mode_rendering(self) -> None:
        self.engine.clear_pattern(0)
        self.engine.set_step(0, 0, 0, True)
        for channel in range(self.engine.channel_count()):
            self.engine.set_channel_mute(channel, channel != 0)
        self.engine.set_channel_pan(0, -1.0)
        audio = self.engine.render_offline(0.2)
        left_peak = max(abs(audio[index]) for index in range(0, len(audio), 2))
        right_peak = max(abs(audio[index]) for index in range(1, len(audio), 2))
        self.assertGreater(left_peak, 0.01)
        self.assertLess(right_peak, 1e-6)

        for channel in range(self.engine.channel_count()):
            self.engine.set_pattern_at(channel, 0, -1)
            self.engine.set_channel_mute(channel, False)
        self.engine.set_song_mode(True)
        song_audio = self.engine.render_offline(0.1)
        self.assertLess(max(abs(value) for value in song_audio), 1e-6)

    def test_failed_sample_and_invalid_project_preserve_state(self) -> None:
        original_name = self.engine.get_channel(0).name
        self.assertFalse(self.engine.set_channel_sample(0, "definitely-missing.wav"))
        self.assertIn("built-in", self.engine.last_error())
        self.assertEqual(self.engine.get_channel(0).name, original_name)
        audio = self.engine.render_offline(0.1)
        self.assertGreater(max(abs(value) for value in audio), 0.01)
        with tempfile.TemporaryDirectory() as directory:
            bad_path = Path(directory) / "bad.cseq"
            bad_path.write_text('{"format":"Wrong"}', encoding="utf-8")
            self.assertFalse(self.engine.load_project(str(bad_path)))
            self.assertEqual(self.engine.channel_count(), 5)
            self.assertEqual(self.engine.get_channel(0).name, original_name)


class _FakeScreen:
    def __init__(self, height: int = 30, width: int = 120):
        self.height = height
        self.width = width
        self.calls = []

    def getmaxyx(self):
        return (self.height, self.width)

    def addstr(self, *args):
        self.calls.append(args)
        return None


class _InputScreen(_FakeScreen):
    def __init__(self, keys):
        super().__init__()
        self.keys = iter(keys)

    def move(self, *_args):
        return None

    def refresh(self):
        return None

    def timeout(self, *_args):
        return None

    def get_wch(self):
        return next(self.keys)


class ConsoleSeqUiLogicTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ui = ConsoleSeqUI(_FakeScreen(), no_audio=True)

    def tearDown(self) -> None:
        self.ui.engine.shutdown()

    def test_pattern_transport_song_and_mixer_keys(self) -> None:
        initial = self.ui.engine.get_step(0, 0, 0)
        self.ui.handle_key(ord(" "))
        self.assertNotEqual(self.ui.engine.get_step(0, 0, 0), initial)
        self.ui.handle_key(curses.KEY_RIGHT)
        self.assertEqual(self.ui.step, 1)
        bpm = self.ui.engine.bpm()
        self.ui.handle_key(ord("+"))
        self.assertEqual(self.ui.engine.bpm(), bpm + 1)
        loop = self.ui.engine.loop()
        self.ui.handle_key(ord("t"))
        self.assertNotEqual(self.ui.engine.loop(), loop)
        self.ui.handle_key(ord("p"))
        self.assertTrue(self.ui.engine.is_playing())
        self.assertIn("SILENT", self.ui.status)
        self.ui.handle_key(ord("a"))
        self.assertFalse(self.ui.engine.is_playing())

        self.ui.handle_key(9)
        self.assertEqual(self.ui.focus, "SONG")
        self.assertTrue(self.ui.engine.song_mode())
        old_cell = self.ui.engine.get_pattern_at(0, 0)
        self.ui.handle_key(ord(" "))
        self.assertNotEqual(self.ui.engine.get_pattern_at(0, 0), old_cell)

        self.ui.handle_key(9)
        self.assertEqual(self.ui.focus, "MIXER")
        old_volume = self.ui.engine.get_channel(0).volume
        self.ui.handle_key(curses.KEY_DOWN)
        self.assertLess(self.ui.engine.get_channel(0).volume, old_volume)
        self.ui.handle_key(curses.KEY_RIGHT)
        self.assertGreater(self.ui.engine.get_channel(0).pan, 0)
        self.ui.handle_key(ord("m"))
        self.ui.handle_key(ord("o"))
        self.assertTrue(self.ui.engine.get_channel(0).mute)
        self.assertTrue(self.ui.engine.get_channel(0).solo)

    def test_pattern_cursor_uses_high_contrast_background(self) -> None:
        self.ui.screen = _FakeScreen(height=30, width=120)
        self.ui.colors_enabled = False
        with patch("console_seq.ui.curses.color_pair", return_value=0):
            self.ui.draw_pattern(3, 0, 12, 50)
        # Pattern 1 starts with Kick X at row 5, column 16. The selected
        # cell must use reverse video even when the terminal has no colors.
        cursor_calls = [call for call in self.ui.screen.calls
                        if len(call) >= 4 and call[0] == 5 and call[1] == 16]
        self.assertTrue(cursor_calls)
        self.assertTrue(cursor_calls[-1][3] & curses.A_REVERSE)

    def test_popup_box_clears_every_row_with_opaque_background(self) -> None:
        self.ui.screen = _FakeScreen(height=30, width=120)
        self.ui.colors_enabled = False
        with patch("console_seq.ui.curses.color_pair", return_value=0):
            self.ui.box(4, 10, 6, 24, "OPAQUE", True, popup=True)
        cleared_rows = {(call[0], call[1]) for call in self.ui.screen.calls
                        if len(call) >= 4 and call[1] == 10 and call[2] == " " * 24
                        and call[3] & curses.A_REVERSE}
        self.assertEqual(cleared_rows, {(row, 10) for row in range(4, 10)})

    def test_copy_paste_new_pattern_and_clear(self) -> None:
        self.ui.copy_pattern()
        self.ui.handle_key(ord("n"))
        target = self.ui.engine.current_pattern()
        self.assertFalse(self.ui.engine.get_step(target, 0, 0))
        self.ui.paste_pattern()
        self.assertTrue(self.ui.engine.get_step(target, 0, 0))
        with patch.object(self.ui, "confirm", return_value=True):
            self.ui.handle_key(ord("d"))
        self.assertFalse(any(
            self.ui.engine.get_step(target, channel, step)
            for channel in range(self.ui.engine.channel_count())
            for step in range(self.ui.engine.step_count())
        ))

    def test_add_instrument_pattern_tools_and_step_expression(self) -> None:
        with patch.object(self.ui, "choose_preset", return_value="bass_sub"):
            self.ui.handle_key(ord("i"))
        self.assertEqual(self.ui.engine.channel_count(), 6)
        self.assertEqual(self.ui.channel, 5)
        self.assertEqual(self.ui.engine.get_channel(5).builtin_id, "bass_sub")

        original_velocity = self.ui.engine.get_velocity(0, 5, 0)
        self.ui.handle_key(ord(";"))
        self.assertLess(self.ui.engine.get_velocity(0, 5, 0), original_velocity)
        original_note = self.ui.engine.get_note(0, 5, 0)
        self.ui.handle_key(ord("}"))
        self.assertEqual(self.ui.engine.get_note(0, 5, 0), original_note + 12)

        self.ui.handle_key(ord("b"))
        self.assertEqual(self.ui.engine.pattern_count(), 5)
        with patch.object(self.ui, "prompt", return_value="Drop"):
            self.ui.handle_key(ord("r"))
        self.assertEqual(self.ui.engine.get_pattern(self.ui.engine.current_pattern()).name, "Drop")
        with patch.object(self.ui, "confirm", return_value=True):
            self.ui.handle_key(ord("x"))
        self.assertEqual(self.ui.engine.pattern_count(), 4)

        for _ in range(12):
            self.ui.engine.add_channel("perc_click")
        self.ui.channel = self.ui.engine.channel_count() - 1
        self.ui.screen = _FakeScreen(height=30, width=120)
        with patch("console_seq.ui.curses.color_pair", return_value=0):
            self.ui.draw_pattern(3, 0, 12, 50)
            self.ui.draw_channels(3, 50, 12, 18)
            self.ui.draw_song(3, 68, 12, 52)
            self.ui.draw_mixer(15, 0, 8, 120)

    def test_pattern_and_song_bank_navigation(self) -> None:
        self.ui.handle_key(ord("N"))
        self.assertEqual(self.ui.engine.pattern_count(), 20)
        self.assertEqual(self.ui.engine.current_pattern(), 4)
        self.ui.engine.set_current_pattern(0)
        self.ui.handle_key(curses.KEY_NPAGE)
        self.assertEqual(self.ui.engine.current_pattern(), 16)
        self.ui.handle_key(curses.KEY_PPAGE)
        self.assertEqual(self.ui.engine.current_pattern(), 0)

        self.ui.engine.set_song_slot_count(48)
        self.ui.handle_key(9)
        self.assertEqual(self.ui.focus, "SONG")
        self.ui.handle_key(curses.KEY_NPAGE)
        self.assertEqual(self.ui.song_slot, 16)
        self.ui.handle_key(curses.KEY_NPAGE)
        self.assertEqual(self.ui.song_slot, 32)
        self.ui.handle_key(curses.KEY_PPAGE)
        self.assertEqual(self.ui.song_slot, 16)

    def test_note_length_editing_from_x_and_continuation(self) -> None:
        self.ui.channel = 3  # Piano has an X on step 1 in the demo.
        self.ui.step = 0
        self.ui.handle_key(ord("e"))
        self.assertEqual(self.ui.engine.get_duration(0, 3, 0), 1)
        for _ in range(3):
            self.ui.handle_key(curses.KEY_RIGHT)
        self.assertEqual(self.ui.engine.get_duration(0, 3, 0), 4)
        self.assertEqual(self.ui.note_start_at(0, 3, 3), 0)
        self.ui.handle_key(27)
        self.assertIsNone(self.ui.length_edit_anchor)
        self.ui.step = 2
        self.ui.handle_key(ord("e"))
        self.assertEqual(self.ui.length_edit_anchor, (3, 0))
        self.ui.handle_key(27)
        self.ui.handle_key(curses.KEY_BACKSPACE)
        self.assertFalse(self.ui.engine.get_step(0, 3, 0))

    def test_unicode_prompt_replaces_default_and_ignores_ffff(self) -> None:
        self.ui.screen = _InputScreen(list("живой бит") + ["\uffff"] + list(".cseq") + ["\n"])
        with patch("console_seq.ui.curses.noecho"), \
             patch("console_seq.ui.curses.curs_set"), \
             patch("console_seq.ui.curses.color_pair", return_value=0):
            value = self.ui.prompt("SAVE", "project.cseq")
        self.assertEqual(value, "живой бит.cseq")
        self.assertNotIn("\uffff", value)

    def test_song_panel_on_terminal_wider_than_song(self) -> None:
        # Regression: a wide Song panel used its screen capacity as the loop
        # bound and called get_pattern_at() with slot >= song_slot_count().
        self.ui.screen = _FakeScreen(height=40, width=260)
        with patch("console_seq.ui.curses.color_pair", return_value=0):
            self.ui.draw_song(3, 80, 20, 180)
        self.assertEqual(self.ui.engine.song_slot_count(), 16)


if __name__ == "__main__":
    unittest.main(verbosity=2)
