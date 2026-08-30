"""Keyboard-driven curses interface for ConsoleSeq."""

from __future__ import annotations

import argparse
import curses
import sys
import tempfile
from pathlib import Path
from typing import Iterable

from .core import ChannelType, Engine


FOCUSES = ("PATTERN", "SONG", "MIXER")
NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
PATTERN_BANK_SIZE = 16


def note_name(note: int) -> str:
    return f"{NOTE_NAMES[note % 12]}{note // 12 - 1}"


def clipped(text: object, width: int) -> str:
    return str(text)[: max(0, width)]


class ConsoleSeqUI:
    def __init__(self, screen, project: str | None = None, no_audio: bool = False):
        self.screen = screen
        self.engine = Engine()
        self.focus_index = 0
        self.channel = 0
        self.step = 0
        self.song_slot = 0
        self.status = "Ready. The demo beat is loaded; press P to play."
        self.project_file = Path(project).expanduser() if project else Path("project.cseq")
        self.clipboard: list[list[tuple[bool, int, float]]] | None = None
        self.running = True
        self.no_audio = no_audio
        if project:
            if self.engine.load_project(str(self.project_file)):
                self.status = f"Loaded {self.project_file}"
            else:
                self.status = f"Load failed: {self.engine.last_error()}"

    @property
    def focus(self) -> str:
        return FOCUSES[self.focus_index]

    def run(self) -> None:
        self.configure_terminal()
        if not self.no_audio:
            self.engine.start()
            self.status = self.engine.audio_status()
        else:
            self.status = "Audio disabled by --no-audio; transport will be silent"
        try:
            while self.running:
                self.draw()
                try:
                    self.handle_key(self.screen.getch())
                except (RuntimeError, ValueError, IndexError) as error:
                    self.status = f"Operation failed: {error}"
        finally:
            self.engine.shutdown()

    def configure_terminal(self) -> None:
        curses.curs_set(0)
        self.screen.keypad(True)
        self.screen.timeout(80)
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
            curses.init_pair(2, curses.COLOR_CYAN, -1)
            curses.init_pair(3, curses.COLOR_GREEN, -1)
            curses.init_pair(4, curses.COLOR_YELLOW, -1)
            curses.init_pair(5, curses.COLOR_RED, -1)

    def put(self, y: int, x: int, text: object, attr: int = 0, width: int | None = None) -> None:
        height, screen_width = self.screen.getmaxyx()
        if y < 0 or y >= height or x < 0 or x >= screen_width:
            return
        limit = screen_width - x - (1 if y == height - 1 else 0)
        if width is not None:
            limit = min(limit, width)
        try:
            self.screen.addstr(y, x, clipped(text, limit), attr)
        except curses.error:
            pass

    def box(self, y: int, x: int, height: int, width: int, title: str, focused: bool = False) -> None:
        if height < 2 or width < 3:
            return
        attr = curses.color_pair(2) | (curses.A_BOLD if focused else 0)
        self.put(y, x, "+" + "-" * (width - 2) + "+", attr, width)
        for row in range(1, height - 1):
            self.put(y + row, x, "|", attr)
            self.put(y + row, x + width - 1, "|", attr)
        self.put(y + height - 1, x, "+" + "-" * (width - 2) + "+", attr, width)
        self.put(y, x + 2, f" {title} ", attr | curses.A_BOLD, max(0, width - 4))

    def draw(self) -> None:
        self.screen.erase()
        height, width = self.screen.getmaxyx()
        playback = "PLAY" if self.engine.is_playing() else "STOP"
        audio = "AUDIO" if self.engine.audio_available() else "SILENT"
        mode = "SONG" if self.engine.song_mode() else "PATTERN"
        top_attr = curses.color_pair(1) | curses.A_BOLD
        self.put(0, 0, " " * max(0, width - 1), top_attr)
        self.put(
            0, 1,
            f"ConsoleSeq | {playback:<4} | {audio:<6} | BPM {self.engine.bpm():5.1f} | {mode} | "
            f"Pat {self.engine.current_pattern() + 1} Step {self.engine.current_step() + 1:02d} "
            f"Slot {self.engine.current_song_slot() + 1:02d}",
            top_attr, max(0, width - 2),
        )
        self.put(1, 1, "P play  Tab focus  I add instrument  Enter settings  N new pattern  +/- BPM  Esc menu  Q quit", curses.A_DIM)

        if height < 20 or width < 76:
            self.put(5, 3, "Terminal is too small for the sequencer.", curses.color_pair(5) | curses.A_BOLD)
            self.put(7, 3, f"Current: {width}x{height}; minimum: 76x20")
            self.put(height - 2, 1, self.status, curses.color_pair(4), max(0, width - 2))
            self.screen.refresh()
            return

        body_y = 3
        status_y = height - 2
        body_height = status_y - body_y
        mixer_height = min(9, max(7, body_height // 3))
        upper_height = body_height - mixer_height
        pattern_width = min(58, max(42, int(width * 0.53)))
        channel_width = min(20, max(16, int(width * 0.17)))
        song_width = width - pattern_width - channel_width
        self.draw_pattern(body_y, 0, upper_height, pattern_width)
        self.draw_channels(body_y, pattern_width, upper_height, channel_width)
        self.draw_song(body_y, pattern_width + channel_width, upper_height, song_width)
        self.draw_mixer(body_y + upper_height, 0, mixer_height, width)

        hint = {
            "PATTERN": "Arrows move | PgUp/PgDn bank | n new | N +16 | B/R/X pattern | Enter channel",
            "SONG": "Arrows move | PgUp/PgDn slots | Space cycles | 1-9/G assign | Backspace empty",
            "MIXER": "PgUp/PgDn channel | Up/Down volume | Left/Right pan | M mute | O solo",
        }[self.focus]
        self.put(status_y, 0, " " * max(0, width - 1), curses.A_REVERSE)
        self.put(status_y, 1, f"{self.focus}: {hint}", curses.A_REVERSE, max(0, width - 2))
        self.put(status_y + 1, 1, self.status, curses.color_pair(4), max(0, width - 2))
        self.screen.refresh()

    def draw_pattern(self, y: int, x: int, height: int, width: int) -> None:
        pattern = self.engine.get_pattern(self.engine.current_pattern())
        bank = self.engine.current_pattern() // PATTERN_BANK_SIZE + 1
        banks = (self.engine.pattern_count() + PATTERN_BANK_SIZE - 1) // PATTERN_BANK_SIZE
        self.box(y, x, height, width,
                 f"PATTERN {self.engine.current_pattern() + 1}: {pattern.name} [{bank}/{banks}]",
                 self.focus == "PATTERN")
        cell_width = 2 if width < 52 else 3
        grid_x = x + max(9, width - pattern.step_count * cell_width - 2)
        visible_steps = min(pattern.step_count, max(1, (x + width - 1 - grid_x) // cell_width))
        step_start = min(max(0, self.step - visible_steps + 1), max(0, pattern.step_count - visible_steps))
        for offset in range(visible_steps):
            step = step_start + offset
            self.put(y + 1, grid_x + offset * cell_width, str((step + 1) % 10), curses.A_DIM)
        rows = min(self.engine.channel_count(), max(0, height - 3))
        channel_start = min(max(0, self.channel - rows + 1), max(0, self.engine.channel_count() - rows))
        for channel_index in range(channel_start, channel_start + rows):
            channel = self.engine.get_channel(channel_index)
            row_y = y + 2 + channel_index - channel_start
            selected_row = channel_index == self.channel
            self.put(row_y, x + 1, (">" if selected_row else " ") + clipped(channel.name, 7), curses.A_BOLD if selected_row else 0, 9)
            for offset in range(visible_steps):
                step = step_start + offset
                active = self.engine.get_step(self.engine.current_pattern(), channel_index, step)
                marker = "X" if active else "."
                attr = curses.color_pair(3) | curses.A_BOLD if active else curses.A_DIM
                if self.focus == "PATTERN" and selected_row and step == self.step:
                    attr = curses.color_pair(1) | curses.A_BOLD
                self.put(row_y, grid_x + offset * cell_width, marker.center(cell_width - 1), attr, cell_width - 1)
        selected = self.engine.get_channel(self.channel)
        if selected.type != ChannelType.DRUM and height >= 9:
            note = self.engine.get_note(self.engine.current_pattern(), self.channel, self.step)
            self.put(y + height - 2, x + 2,
                     f"Note {note_name(note)} ({note}) velocity {self.engine.get_velocity(self.engine.current_pattern(), self.channel, self.step):.2f}",
                     curses.color_pair(4), width - 4)

    def draw_channels(self, y: int, x: int, height: int, width: int) -> None:
        self.box(y, x, height, width, "CHANNELS")
        rows = min(self.engine.channel_count(), max(0, height - 2))
        channel_start = min(max(0, self.channel - rows + 1), max(0, self.engine.channel_count() - rows))
        for index in range(channel_start, channel_start + rows):
            channel = self.engine.get_channel(index)
            marker = ">" if index == self.channel else " "
            flags = ("M" if channel.mute else "-") + ("S" if channel.solo else "-")
            attr = curses.color_pair(1) | curses.A_BOLD if index == self.channel else 0
            key = f"F{index + 1}" if index < 10 else f"#{index + 1}"
            self.put(y + 1 + index - channel_start, x + 1, f"{marker}{key:<3} {channel.name:<7} {flags}", attr, width - 2)

    def draw_song(self, y: int, x: int, height: int, width: int) -> None:
        slot_count = self.engine.song_slot_count()
        bank = self.song_slot // PATTERN_BANK_SIZE + 1
        banks = (slot_count + PATTERN_BANK_SIZE - 1) // PATTERN_BANK_SIZE
        self.box(y, x, height, width, f"SONG SLOTS [{bank}/{banks}] TOTAL {slot_count}", self.focus == "SONG")
        cell_width = 3
        label_width = 5 if width >= 16 else 1
        if slot_count <= 0:
            return
        # A wide terminal can fit more cells than the song owns. Never let the
        # drawing loop address a slot beyond the arrangement's fixed bounds.
        visible = min(slot_count, max(1, (width - label_width - 2) // cell_width))
        start = min(max(0, self.song_slot - visible + 1), max(0, slot_count - visible))
        for offset in range(visible):
            slot = start + offset
            self.put(y + 1, x + label_width + offset * cell_width, str((slot + 1) % 10).center(cell_width), curses.A_DIM)
        rows = min(self.engine.channel_count(), max(0, height - 3))
        channel_start = min(max(0, self.channel - rows + 1), max(0, self.engine.channel_count() - rows))
        for channel_index in range(channel_start, channel_start + rows):
            row_y = y + 2 + channel_index - channel_start
            if label_width > 1:
                self.put(row_y, x + 1, clipped(self.engine.get_channel(channel_index).name, label_width - 1), 0, label_width - 1)
            for offset in range(visible):
                slot = start + offset
                pattern = self.engine.get_pattern_at(channel_index, slot)
                value = " . " if pattern < 0 else f"{pattern + 1:^3}"
                attr = curses.color_pair(3) if pattern >= 0 else curses.A_DIM
                if self.focus == "SONG" and channel_index == self.channel and slot == self.song_slot:
                    attr = curses.color_pair(1) | curses.A_BOLD
                self.put(row_y, x + label_width + offset * cell_width, value, attr, cell_width)

    def draw_mixer(self, y: int, x: int, height: int, width: int) -> None:
        self.box(y, x, height, width, "MIXER", self.focus == "MIXER")
        available = max(1, width - 4)
        visible_strips = max(1, available // 14)
        strip_width = max(14, available // min(self.engine.channel_count(), visible_strips))
        channel_start = min(max(0, self.channel - visible_strips + 1),
                            max(0, self.engine.channel_count() - visible_strips))
        for index in range(channel_start, min(self.engine.channel_count(), channel_start + visible_strips)):
            start_x = x + 2 + (index - channel_start) * strip_width
            if start_x + 8 >= x + width - 1:
                break
            channel = self.engine.get_channel(index)
            attr = curses.color_pair(1) | curses.A_BOLD if index == self.channel else curses.A_BOLD
            slider_size = max(5, min(10, strip_width - 3))
            filled = round(channel.volume * slider_size)
            pan = "C" if abs(channel.pan) < 0.05 else (f"L{abs(channel.pan) * 100:.0f}" if channel.pan < 0 else f"R{channel.pan * 100:.0f}")
            self.put(y + 1, start_x, clipped(channel.name, strip_width - 1), attr, strip_width - 1)
            self.put(y + 2, start_x, "[" + "|" * filled + "-" * (slider_size - filled) + "]", curses.color_pair(3), strip_width - 1)
            self.put(y + 3, start_x, f"Vol {channel.volume * 100:3.0f}", 0, strip_width - 1)
            self.put(y + 4, start_x, f"Pan {pan:<3}", 0, strip_width - 1)
            self.put(y + 5, start_x, f"{'MUTE' if channel.mute else '    '} {'SOLO' if channel.solo else ''}", curses.color_pair(5) if channel.mute else curses.color_pair(4), strip_width - 1)

    def handle_key(self, key: int) -> None:
        if key == -1:
            return
        if key in (ord("q"), ord("Q")):
            self.running = False
        elif key == 9:
            self.focus_index = (self.focus_index + 1) % len(FOCUSES)
            if self.focus == "PATTERN":
                self.engine.set_song_mode(False)
            elif self.focus == "SONG":
                self.engine.set_song_mode(True)
        elif key in (ord("p"), ord("P")):
            if self.engine.is_playing():
                self.engine.stop()
                self.status = "Transport stopped"
            else:
                self.engine.play()
                if self.engine.audio_available():
                    self.status = f"Playing in {'song' if self.engine.song_mode() else 'pattern'} mode"
                else:
                    self.status = "Transport is running, but audio is SILENT. See README_RU.md"
        elif key in (ord("a"), ord("A")):
            self.engine.pause()
            self.status = "Transport paused; P resumes from this position"
        elif key in (ord("t"), ord("T")):
            self.engine.set_loop(not self.engine.loop())
            self.status = f"Loop {'enabled' if self.engine.loop() else 'disabled'}"
        elif key in (ord("+"), ord("=")):
            self.engine.set_bpm(self.engine.bpm() + 1)
        elif key == ord("-"):
            self.engine.set_bpm(self.engine.bpm() - 1)
        elif key in (ord("s"), ord("S")):
            self.save_dialog()
        elif key in (ord("l"), ord("L")):
            self.load_dialog()
        elif key in (ord("w"), ord("W")):
            self.sample_dialog()
        elif key in (ord("i"), ord("I")):
            self.add_instrument_dialog()
        elif key == 27:
            self.menu()
        elif key in (ord("m"), ord("M")):
            channel = self.engine.get_channel(self.channel)
            self.engine.set_channel_mute(self.channel, not channel.mute)
        elif key in (ord("o"), ord("O")):
            channel = self.engine.get_channel(self.channel)
            self.engine.set_channel_solo(self.channel, not channel.solo)
        elif key in (curses.KEY_F1, curses.KEY_F2, curses.KEY_F3, curses.KEY_F4, curses.KEY_F5,
                     curses.KEY_F6, curses.KEY_F7, curses.KEY_F8, curses.KEY_F9, curses.KEY_F10):
            self.channel = min(self.engine.channel_count() - 1, key - curses.KEY_F1)
        elif key in (ord("c"), ord("C")) and self.focus == "PATTERN":
            self.copy_pattern()
        elif key in (ord("v"), ord("V")) and self.focus == "PATTERN":
            self.paste_pattern()
        elif key == ord("n") and self.focus == "PATTERN":
            index = self.engine.add_pattern()
            self.engine.set_current_pattern(index)
            self.status = f"Created Pattern {index + 1}"
        elif key == ord("N") and self.focus == "PATTERN":
            index = self.engine.add_pattern_bank(PATTERN_BANK_SIZE)
            self.engine.set_current_pattern(index)
            self.status = f"Added Patterns {index + 1}-{index + PATTERN_BANK_SIZE}"
        elif key in (ord("b"), ord("B")) and self.focus == "PATTERN":
            index = self.engine.duplicate_pattern(self.engine.current_pattern())
            self.engine.set_current_pattern(index)
            self.status = f"Duplicated as Pattern {index + 1}"
        elif key in (ord("r"), ord("R")) and self.focus == "PATTERN":
            current = self.engine.get_pattern(self.engine.current_pattern())
            name = self.prompt("RENAME PATTERN", current.name)
            if name:
                self.engine.set_pattern_name(self.engine.current_pattern(), name)
                self.status = f"Pattern renamed to {name}"
        elif key in (ord("x"), ord("X")) and self.focus == "PATTERN":
            if self.engine.pattern_count() <= 1:
                self.status = "A project must keep at least one pattern"
            elif self.confirm(f"Delete Pattern {self.engine.current_pattern() + 1}?"):
                removed = self.engine.current_pattern() + 1
                self.engine.remove_pattern(self.engine.current_pattern())
                self.status = f"Deleted Pattern {removed}; Song assignments were updated"
        elif key in (ord("d"), ord("D")) and self.focus == "PATTERN":
            if self.confirm("Clear every step in this pattern?"):
                self.engine.clear_pattern(self.engine.current_pattern())
                self.status = f"Cleared Pattern {self.engine.current_pattern() + 1}"
        elif key == ord(","):
            self.engine.set_current_pattern((self.engine.current_pattern() - 1) % self.engine.pattern_count())
        elif key == ord("."):
            self.engine.set_current_pattern((self.engine.current_pattern() + 1) % self.engine.pattern_count())
        else:
            self.handle_focus_key(key)

    def handle_focus_key(self, key: int) -> None:
        if self.focus == "PATTERN":
            if key == curses.KEY_PPAGE:
                target = max(0, self.engine.current_pattern() - PATTERN_BANK_SIZE)
                self.engine.set_current_pattern(target)
                self.status = f"Pattern bank {target // PATTERN_BANK_SIZE + 1}"
            elif key == curses.KEY_NPAGE:
                target = min(self.engine.pattern_count() - 1,
                             self.engine.current_pattern() + PATTERN_BANK_SIZE)
                self.engine.set_current_pattern(target)
                self.status = f"Pattern bank {target // PATTERN_BANK_SIZE + 1}"
            elif key == curses.KEY_LEFT:
                self.step = (self.step - 1) % self.engine.step_count()
            elif key == curses.KEY_RIGHT:
                self.step = (self.step + 1) % self.engine.step_count()
            elif key == curses.KEY_UP:
                self.channel = (self.channel - 1) % self.engine.channel_count()
            elif key == curses.KEY_DOWN:
                self.channel = (self.channel + 1) % self.engine.channel_count()
            elif key == ord(" "):
                value = self.engine.get_step(self.engine.current_pattern(), self.channel, self.step)
                self.engine.set_step(self.engine.current_pattern(), self.channel, self.step, not value)
            elif key in (10, 13, curses.KEY_ENTER):
                self.instrument_dialog()
            elif key in (curses.KEY_BACKSPACE, curses.KEY_DC, 8, 127):
                self.engine.set_step(self.engine.current_pattern(), self.channel, self.step, False)
            elif key in (ord("["), ord("]")):
                direction = -1 if key == ord("[") else 1
                note = self.engine.get_note(self.engine.current_pattern(), self.channel, self.step)
                self.engine.set_note(self.engine.current_pattern(), self.channel, self.step, note + direction)
            elif key in (ord("{"), ord("}")):
                direction = -12 if key == ord("{") else 12
                note = self.engine.get_note(self.engine.current_pattern(), self.channel, self.step)
                self.engine.set_note(self.engine.current_pattern(), self.channel, self.step, note + direction)
            elif key in (ord(";"), ord("'")):
                direction = -0.05 if key == ord(";") else 0.05
                velocity = self.engine.get_velocity(self.engine.current_pattern(), self.channel, self.step)
                self.engine.set_velocity(self.engine.current_pattern(), self.channel, self.step, velocity + direction)
                self.status = f"Step velocity: {self.engine.get_velocity(self.engine.current_pattern(), self.channel, self.step):.2f}"
            elif key in (ord("g"), ord("G")):
                value = self.prompt("GO TO PATTERN NUMBER", str(self.engine.current_pattern() + 1))
                try:
                    pattern = int(value) - 1 if value else -1
                    self.engine.set_current_pattern(pattern)
                    self.status = f"Selected Pattern {pattern + 1}"
                except (ValueError, IndexError):
                    self.status = f"Pattern number must be 1..{self.engine.pattern_count()}"
        elif self.focus == "SONG":
            if key == curses.KEY_PPAGE:
                self.song_slot = max(0, self.song_slot - PATTERN_BANK_SIZE)
                self.status = f"Song slots {self.song_slot // PATTERN_BANK_SIZE * PATTERN_BANK_SIZE + 1}-" \
                              f"{min(self.engine.song_slot_count(), (self.song_slot // PATTERN_BANK_SIZE + 1) * PATTERN_BANK_SIZE)}"
            elif key == curses.KEY_NPAGE:
                self.song_slot = min(self.engine.song_slot_count() - 1,
                                     self.song_slot + PATTERN_BANK_SIZE)
                self.status = f"Song slots {self.song_slot // PATTERN_BANK_SIZE * PATTERN_BANK_SIZE + 1}-" \
                              f"{min(self.engine.song_slot_count(), (self.song_slot // PATTERN_BANK_SIZE + 1) * PATTERN_BANK_SIZE)}"
            elif key == curses.KEY_LEFT:
                self.song_slot = (self.song_slot - 1) % self.engine.song_slot_count()
            elif key == curses.KEY_RIGHT:
                self.song_slot = (self.song_slot + 1) % self.engine.song_slot_count()
            elif key == curses.KEY_UP:
                self.channel = (self.channel - 1) % self.engine.channel_count()
            elif key == curses.KEY_DOWN:
                self.channel = (self.channel + 1) % self.engine.channel_count()
            elif key in (ord(" "), 10, 13, curses.KEY_ENTER):
                current = self.engine.get_pattern_at(self.channel, self.song_slot)
                self.engine.set_pattern_at(self.channel, self.song_slot, (current + 1) % self.engine.pattern_count())
            elif key in (curses.KEY_BACKSPACE, curses.KEY_DC, 8, 127):
                self.engine.set_pattern_at(self.channel, self.song_slot, -1)
            elif ord("1") <= key <= ord("9"):
                pattern = key - ord("1")
                if pattern < self.engine.pattern_count():
                    self.engine.set_pattern_at(self.channel, self.song_slot, pattern)
            elif key in (ord("g"), ord("G")):
                value = self.prompt("ASSIGN PATTERN NUMBER", "1")
                try:
                    pattern = int(value) - 1 if value else -1
                    self.engine.set_pattern_at(self.channel, self.song_slot, pattern)
                    self.status = f"Assigned Pattern {pattern + 1} to slot {self.song_slot + 1}"
                except (ValueError, IndexError):
                    self.status = f"Pattern number must be 1..{self.engine.pattern_count()}"
        elif self.focus == "MIXER":
            channel = self.engine.get_channel(self.channel)
            if key == curses.KEY_UP:
                self.engine.set_channel_volume(self.channel, channel.volume + 0.02)
            elif key == curses.KEY_DOWN:
                self.engine.set_channel_volume(self.channel, channel.volume - 0.02)
            elif key == curses.KEY_LEFT:
                self.engine.set_channel_pan(self.channel, channel.pan - 0.05)
            elif key == curses.KEY_RIGHT:
                self.engine.set_channel_pan(self.channel, channel.pan + 0.05)
            elif key in (curses.KEY_PPAGE, ord("k")):
                self.channel = (self.channel - 1) % self.engine.channel_count()
            elif key in (curses.KEY_NPAGE, ord("j")):
                self.channel = (self.channel + 1) % self.engine.channel_count()

    def copy_pattern(self) -> None:
        pattern = self.engine.current_pattern()
        self.clipboard = [[(
            self.engine.get_step(pattern, channel, step),
            self.engine.get_note(pattern, channel, step),
            self.engine.get_velocity(pattern, channel, step),
        ) for step in range(self.engine.step_count())] for channel in range(self.engine.channel_count())]
        self.status = f"Copied Pattern {pattern + 1}"

    def paste_pattern(self) -> None:
        if self.clipboard is None:
            self.status = "Pattern clipboard is empty"
            return
        pattern = self.engine.current_pattern()
        for channel, row in enumerate(self.clipboard[: self.engine.channel_count()]):
            for step, (active, note, velocity) in enumerate(row[: self.engine.step_count()]):
                self.engine.set_step(pattern, channel, step, active)
                self.engine.set_note(pattern, channel, step, note)
                self.engine.set_velocity(pattern, channel, step, velocity)
        self.status = f"Pasted into Pattern {pattern + 1}"

    def prompt(self, title: str, default: str = "") -> str | None:
        height, width = self.screen.getmaxyx()
        popup_width = min(max(40, len(default) + 8), width - 4)
        popup_y = max(1, height // 2 - 2)
        popup_x = max(1, (width - popup_width) // 2)
        self.box(popup_y, popup_x, 5, popup_width, title, True)
        self.put(popup_y + 2, popup_x + 2, " " * (popup_width - 4), curses.A_REVERSE)
        self.put(popup_y + 2, popup_x + 2, default, curses.A_REVERSE, popup_width - 4)
        self.screen.refresh()
        curses.echo()
        curses.curs_set(1)
        try:
            self.screen.move(popup_y + 2, popup_x + 2 + min(len(default), popup_width - 5))
            raw = self.screen.getstr(popup_y + 2, popup_x + 2, popup_width - 5)
            value = raw.decode(sys.getfilesystemencoding(), errors="replace").strip()
            return value or default or None
        except (curses.error, KeyboardInterrupt):
            return None
        finally:
            curses.noecho()
            curses.curs_set(0)

    def confirm(self, question: str) -> bool:
        height, width = self.screen.getmaxyx()
        popup_width = min(max(40, len(question) + 8), width - 4)
        y, x = max(1, height // 2 - 2), max(1, (width - popup_width) // 2)
        self.box(y, x, 5, popup_width, "CONFIRM", True)
        self.put(y + 2, x + 3, question + " [y/N]", curses.A_BOLD, popup_width - 6)
        self.screen.refresh()
        self.screen.timeout(-1)
        key = self.screen.getch()
        self.screen.timeout(80)
        return key in (ord("y"), ord("Y"))

    def instrument_dialog(self) -> None:
        channel = self.engine.get_channel(self.channel)
        height, width = self.screen.getmaxyx()
        popup_width = min(62, width - 4)
        popup_height = min(17, height - 2)
        y, x = max(1, (height - popup_height) // 2), max(1, (width - popup_width) // 2)
        oscillator = str(channel.oscillator).split(".")[-1]
        attack, decay, sustain, release = channel.adsr
        kind = "DRUM" if channel.type == ChannelType.DRUM else "SYNTH"
        self.box(y, x, popup_height, popup_width, f"{channel.name.upper()} SETTINGS", True)
        common = (
            f"P  Choose preset: {channel.builtin_id or 'custom WAV'}",
            "H  Rename channel     C  Clone channel     X  Delete channel",
            "W  Load custom WAV (changes this channel to drum)",
        )
        synth = (
            f"O  Oscillator: {oscillator}       N  Base note: {note_name(channel.base_note)} ({channel.base_note})",
            f"A  Attack: {attack:.3f}s          D  Decay: {decay:.3f}s",
            f"E  Sustain: {sustain:.3f}         R  Release: {release:.3f}s",
            f"F  Tone/filter: {channel.tone:.2f}       G  Drive: {channel.drive:.2f}",
        )
        lines = common + (() if kind == "DRUM" else synth) + ("Esc/other  Close",)
        for row, line in enumerate(lines, start=2):
            self.put(y + row, x + 3, line, curses.A_BOLD if row < len(lines) + 1 else curses.A_DIM, popup_width - 6)
        self.screen.refresh()
        self.screen.timeout(-1)
        key = self.screen.getch()
        self.screen.timeout(80)
        if key in (ord("p"), ord("P")):
            preset = self.choose_preset(f"PRESET FOR {channel.name}", channel.builtin_id)
            if preset:
                self.engine.set_channel_preset(self.channel, preset)
                self.status = f"Preset changed to {preset}"
            return
        if key in (ord("h"), ord("H")):
            name = self.prompt("RENAME CHANNEL", channel.name)
            if name:
                self.engine.set_channel_name(self.channel, name)
                self.status = f"Channel renamed to {name}"
            return
        if key in (ord("c"), ord("C")):
            self.channel = self.engine.duplicate_channel(self.channel)
            self.status = f"Cloned channel as #{self.channel + 1}"
            return
        if key in (ord("x"), ord("X")):
            if self.engine.channel_count() <= 1:
                self.status = "A project must keep at least one channel"
            elif self.confirm(f"Delete channel {channel.name}?"):
                self.engine.remove_channel(self.channel)
                self.channel = min(self.channel, self.engine.channel_count() - 1)
                self.status = f"Deleted channel {channel.name}"
            return
        if key in (ord("w"), ord("W")):
            self.sample_dialog()
            return
        if channel.type == ChannelType.DRUM:
            return
        if key in (ord("o"), ord("O")):
            names = ("SINE", "SQUARE", "SAW", "TRIANGLE")
            current = names.index(oscillator) if oscillator in names else 0
            self.engine.set_synth_param(self.channel, "oscillator", float((current + 1) % len(names)))
            self.status = f"{channel.name} oscillator changed"
            return
        fields = {
            ord("a"): ("attack", attack), ord("A"): ("attack", attack),
            ord("d"): ("decay", decay), ord("D"): ("decay", decay),
            ord("e"): ("sustain", sustain), ord("E"): ("sustain", sustain),
            ord("r"): ("release", release), ord("R"): ("release", release),
            ord("n"): ("base_note", float(channel.base_note)), ord("N"): ("base_note", float(channel.base_note)),
            ord("f"): ("tone", channel.tone), ord("F"): ("tone", channel.tone),
            ord("g"): ("drive", channel.drive), ord("G"): ("drive", channel.drive),
        }
        if key in fields:
            parameter, current = fields[key]
            value = self.prompt(f"SET {parameter.upper()}", f"{current:.3f}")
            try:
                if value is not None:
                    self.engine.set_synth_param(self.channel, parameter, float(value))
                    self.status = f"Set {channel.name} {parameter} to {value}"
            except ValueError:
                self.status = f"Invalid numeric value: {value}"

    def choose_preset(self, title: str, current: str = "") -> str | None:
        catalog = [(str(preset_id), str(name), str(category))
                   for preset_id, name, category in self.engine.preset_catalog()]
        if not catalog:
            self.status = "The engine did not report any instrument presets"
            return None
        categories = list(dict.fromkeys(item[2] for item in catalog))
        current_entry = next((item for item in catalog if item[0] == current), None)
        category_index = categories.index(current_entry[2]) if current_entry else 0
        selected_by_category = {category: 0 for category in categories}
        if current_entry:
            current_items = [item for item in catalog if item[2] == current_entry[2]]
            selected_by_category[current_entry[2]] = current_items.index(current_entry)
        height, width = self.screen.getmaxyx()
        popup_width = min(72, width - 4)
        popup_height = min(18, height - 2)
        visible = max(1, popup_height - 5)
        y, x = max(1, (height - popup_height) // 2), max(1, (width - popup_width) // 2)
        self.screen.timeout(-1)
        try:
            while True:
                self.box(y, x, popup_height, popup_width, title, True)
                category = categories[category_index]
                choices = [item for item in catalog if item[2] == category]
                selected = selected_by_category[category]
                start = min(max(0, selected - visible + 1), max(0, len(choices) - visible))
                previous_category = categories[(category_index - 1) % len(categories)]
                next_category = categories[(category_index + 1) % len(categories)]
                self.put(y + 1, x + 2, " " * (popup_width - 4), 0, popup_width - 4)
                self.put(y + 1, x + 2,
                         f"< {previous_category} | [{category}] {category_index + 1}/{len(categories)} | {next_category} >",
                         curses.color_pair(4) | curses.A_BOLD, popup_width - 4)
                for row in range(visible):
                    index = start + row
                    self.put(y + 2 + row, x + 1, " " * (popup_width - 2), 0, popup_width - 2)
                    if index >= len(choices):
                        continue
                    preset_id, label, _ = choices[index]
                    marker = ">" if index == selected else " "
                    attr = curses.color_pair(1) | curses.A_BOLD if index == selected else 0
                    self.put(y + 2 + row, x + 2,
                             f"{marker} {label:<26} {preset_id}", attr, popup_width - 4)
                self.put(y + popup_height - 2, x + 2,
                         "Left/Right category | Up/Down sound | Enter | Esc",
                         curses.A_DIM, popup_width - 4)
                self.screen.refresh()
                key = self.screen.getch()
                if key == curses.KEY_UP:
                    selected_by_category[category] = (selected - 1) % len(choices)
                elif key == curses.KEY_DOWN:
                    selected_by_category[category] = (selected + 1) % len(choices)
                elif key == curses.KEY_LEFT:
                    category_index = (category_index - 1) % len(categories)
                elif key in (curses.KEY_RIGHT, 9):
                    category_index = (category_index + 1) % len(categories)
                elif key in (10, 13, curses.KEY_ENTER):
                    return choices[selected][0]
                elif key in (27, ord("q"), ord("Q")):
                    return None
        finally:
            self.screen.timeout(80)

    def add_instrument_dialog(self) -> None:
        preset = self.choose_preset("ADD INSTRUMENT")
        if not preset:
            return
        try:
            self.channel = self.engine.add_channel(preset)
            self.status = f"Added channel #{self.channel + 1}: {self.engine.get_channel(self.channel).name}"
        except RuntimeError as error:
            self.status = str(error)

    def save_dialog(self) -> None:
        value = self.prompt("SAVE PROJECT (.cseq)", str(self.project_file))
        if not value:
            return
        path = Path(value)
        if path.suffix.lower() != ".cseq":
            path = path.with_suffix(".cseq")
        if self.engine.save_project(str(path)):
            self.project_file = path
            self.status = f"Saved {path.resolve()}"
        else:
            self.status = f"Save failed: {self.engine.last_error()}"

    def load_dialog(self) -> None:
        value = self.prompt("LOAD PROJECT", str(self.project_file))
        if value and self.engine.load_project(value):
            self.project_file = Path(value)
            self.channel = self.step = self.song_slot = 0
            self.status = f"Loaded {value}"
        elif value:
            self.status = f"Load failed: {self.engine.last_error()}"

    def sample_dialog(self) -> None:
        value = self.prompt(f"LOAD WAV/MP3 FOR {self.engine.get_channel(self.channel).name}")
        if value and self.engine.set_channel_sample(self.channel, value):
            self.status = f"Loaded sample {value}"
        elif value:
            self.status = self.engine.last_error()

    def song_length_dialog(self) -> None:
        current = self.engine.song_slot_count()
        value = self.prompt("SONG LENGTH IN SLOTS (1-512)", str(current))
        if value is None:
            return
        try:
            requested = int(value)
            if requested < current and not self.confirm(
                    f"Shrink Song to {requested}? Later slots are lost?"):
                return
            self.engine.set_song_slot_count(requested)
            self.song_slot = min(self.song_slot, requested - 1)
            self.status = f"Song length changed to {requested} slots"
        except (ValueError, RuntimeError) as error:
            self.status = f"Song length must be 1..512: {error}"

    def menu(self) -> None:
        height, width = self.screen.getmaxyx()
        popup_width = min(48, width - 4)
        y, x = max(1, height // 2 - 7), max(1, (width - popup_width) // 2)
        self.box(y, x, 14, popup_width, "MAIN MENU", True)
        options: Iterable[str] = (
            "N  New project", "O  Open project", "S  Save project",
            "I  Add instrument/channel", "E  Selected channel settings",
            "W  Load WAV/MP3", "Y  Set Song length (1-512 slots)",
            "Z  Cycle 16/32/64 pattern steps",
            "R  Resume", "Q  Exit",
        )
        for row, option in enumerate(options, start=2):
            self.put(y + row, x + 4, option, curses.A_BOLD, popup_width - 8)
        self.screen.refresh()
        self.screen.timeout(-1)
        key = self.screen.getch()
        self.screen.timeout(80)
        if key in (ord("n"), ord("N")):
            self.engine.new_project()
            self.status = "Created a new demo project"
        elif key in (ord("o"), ord("O")):
            self.load_dialog()
        elif key in (ord("s"), ord("S")):
            self.save_dialog()
        elif key in (ord("i"), ord("I")):
            self.add_instrument_dialog()
        elif key in (ord("e"), ord("E")):
            self.instrument_dialog()
        elif key in (ord("w"), ord("W")):
            self.sample_dialog()
        elif key in (ord("y"), ord("Y")):
            self.song_length_dialog()
        elif key in (ord("z"), ord("Z")):
            sizes = (16, 32, 64)
            current = self.engine.step_count()
            next_size = sizes[(sizes.index(current) + 1) % len(sizes)] if current in sizes else 16
            if next_size < current and not self.confirm(f"Shrink patterns to {next_size} steps? Data past the limit is lost."):
                return
            self.engine.set_step_count(next_size)
            self.step = min(self.step, next_size - 1)
            self.status = f"Patterns now have {next_size} steps"
        elif key in (ord("q"), ord("Q")):
            self.running = False


def smoke_test(output: str | None = None) -> int:
    engine = Engine()
    if engine.channel_count() != 5 or engine.pattern_count() < 4:
        raise RuntimeError("The default project was not initialized correctly")
    if not engine.get_step(0, 0, 0):
        raise RuntimeError("The default demo beat is missing")
    audio = engine.render_offline(0.25)
    if len(audio) != int(44100 * 0.25) * 2:
        raise RuntimeError("Offline rendering returned an invalid buffer")
    if max(abs(sample) for sample in audio) <= 0.01:
        raise RuntimeError("Offline rendering produced silence")
    destination = Path(output) if output else Path(tempfile.gettempdir()) / "console_seq_smoke.cseq"
    if not engine.save_project(str(destination)):
        raise RuntimeError(engine.last_error())
    engine.clear_pattern(0)
    if not engine.load_project(str(destination)):
        raise RuntimeError(engine.last_error())
    if not engine.get_step(0, 0, 0):
        raise RuntimeError("Saved pattern did not survive the round trip")
    print(f"ConsoleSeq smoke test passed; project: {destination}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ConsoleSeq terminal music sequencer")
    parser.add_argument("project", nargs="?", help=".cseq project to open")
    parser.add_argument("--no-audio", action="store_true", help="run UI without opening an audio device")
    parser.add_argument("--smoke-test", action="store_true", help="run a headless engine/save/load test")
    parser.add_argument("--smoke-output", help="project path used by --smoke-test")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.smoke_test:
        return smoke_test(args.smoke_output)
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print("ConsoleSeq needs an interactive terminal. Use --smoke-test for a headless check.", file=sys.stderr)
        return 2
    try:
        curses.wrapper(lambda screen: ConsoleSeqUI(screen, args.project, args.no_audio).run())
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
