from __future__ import annotations

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
import curses


class ConsoleSeqCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = Engine()

    def test_default_project_and_editing(self) -> None:
        self.assertEqual(self.engine.channel_count(), 5)
        self.assertEqual([self.engine.get_channel(i).name for i in range(5)],
                         ["Kick", "Snare", "HiHat", "Piano", "Bass"])
        self.assertEqual(self.engine.get_channel(0).type, ChannelType.DRUM)
        self.assertTrue(self.engine.get_step(0, 0, 0))
        self.engine.set_step(0, 3, 3, True)
        self.engine.set_note(0, 3, 3, 65)
        self.engine.set_velocity(0, 3, 3, 0.55)
        self.assertTrue(self.engine.get_step(0, 3, 3))
        self.assertEqual(self.engine.get_note(0, 3, 3), 65)
        self.assertAlmostEqual(self.engine.get_velocity(0, 3, 3), 0.55, places=4)

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
            self.assertLessEqual(max(abs(value) for value in audio), 1.0)

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
        self.assertEqual(len(presets), 22)
        for required in ("kick_deep", "kick_punch", "kick_808", "bass_saw", "bass_sub", "pad_warm"):
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
            engine.clear_pattern(0)
            for channel in range(engine.channel_count()):
                engine.set_channel_mute(channel, True)
            added = engine.add_channel(preset)
            engine.set_step(0, added, 0, True)
            engine.set_channel_mute(added, False)
            peak = max(abs(value) for value in engine.render_offline(0.12))
            self.assertGreater(peak, 0.001, preset)

    def test_channel_and_pattern_changes_survive_round_trip(self) -> None:
        added = self.engine.add_channel("pad_warm")
        self.engine.set_channel_name(added, "Atmosphere")
        self.engine.set_synth_param(added, "tone", 0.21)
        pattern = self.engine.duplicate_pattern(0)
        self.engine.set_pattern_name(pattern, "Chorus")
        self.engine.set_pattern_at(added, 7, pattern)
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
            self.assertEqual(restored.get_pattern_at(added, 7), pattern)
            restored.remove_pattern(pattern)
            self.assertEqual(restored.get_pattern_at(added, 7), -1)

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

    def getmaxyx(self):
        return (self.height, self.width)

    def addstr(self, *_args):
        return None


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

    def test_song_panel_on_terminal_wider_than_song(self) -> None:
        # Regression: a wide Song panel used its screen capacity as the loop
        # bound and called get_pattern_at() with slot >= song_slot_count().
        self.ui.screen = _FakeScreen(height=40, width=260)
        with patch("console_seq.ui.curses.color_pair", return_value=0):
            self.ui.draw_song(3, 80, 20, 180)
        self.assertEqual(self.ui.engine.song_slot_count(), 16)


if __name__ == "__main__":
    unittest.main(verbosity=2)
