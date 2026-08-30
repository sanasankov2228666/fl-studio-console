#include "console_seq.hpp"

#include <algorithm>
#include <cassert>
#include <cmath>
#include <filesystem>
#include <iostream>

using consoleseq::Engine;

int main() {
  Engine engine;
  assert(engine.channel_count() == 5);
  assert(engine.pattern_count() == 4);
  assert(engine.step_count() == 16);
  assert(engine.get_channel(0).name() == "Kick");
  assert(engine.get_step(0, 0, 0));
  assert(engine.get_step(0, 1, 4));
  assert(Engine::preset_ids().size() == 60);
  assert(Engine::preset_catalog().size() == 60);
  engine.set_song_slot_count(48);
  assert(engine.song_slot_count() == 48);
  const int bank_start = engine.add_pattern_bank();
  assert(bank_start == 4);
  assert(engine.pattern_count() == 20);

  const int extra = engine.add_channel("kick_808");
  assert(extra == 5);
  assert(engine.channel_count() == 6);
  assert(engine.get_pattern(0).channel_count() == 6);
  assert(engine.get_song().channel_count() == 6);
  assert(engine.get_channel(extra).builtin_id() == "kick_808");
  engine.set_step(0, extra, 2, true);
  const int clone = engine.duplicate_channel(extra);
  assert(clone == 6);
  assert(engine.get_step(0, clone, 2));
  engine.set_channel_preset(extra, "bass_sub");
  assert(engine.get_channel(extra).name() == "Sub Bass");
  engine.remove_channel(clone);
  assert(engine.channel_count() == 6);

  const int copied_pattern = engine.duplicate_pattern(0);
  engine.set_pattern_name(copied_pattern, "Native Variation");
  engine.set_pattern_at(0, 6, copied_pattern);
  engine.remove_pattern(copied_pattern);
  assert(engine.get_pattern_at(0, 6) == -1);

  engine.set_step(0, 3, 2, true);
  engine.set_note(0, 3, 2, 64);
  assert(engine.get_step(0, 3, 2));
  assert(engine.get_note(0, 3, 2) == 64);
  engine.set_channel_pan(3, -0.35F);
  engine.set_channel_volume(3, 0.5F);

  const auto audio = engine.render_offline(0.6F);
  assert(audio.size() == static_cast<std::size_t>(44100 * 0.6F) * 2U);
  const auto peak = std::max_element(audio.begin(), audio.end(),
      [](float left, float right) { return std::abs(left) < std::abs(right); });
  assert(peak != audio.end());
  assert(std::abs(*peak) > 0.01F);
  assert(std::abs(*peak) <= 1.0F);

  const auto file = std::filesystem::current_path() / "native_test_project.cseq";
  assert(engine.save_project(file.string()));
  assert(!std::filesystem::exists(file.string() + ".tmp"));
  assert(engine.save_project(file.string()));
  engine.clear_pattern(0);
  assert(!engine.get_step(0, 0, 0));
  assert(engine.load_project(file.string()));
  assert(engine.get_step(0, 0, 0));
  assert(engine.get_note(0, 3, 2) == 64);
  assert(engine.song_slot_count() == 48);
  assert(engine.pattern_count() == 20);
  std::filesystem::remove(file);

  std::cout << "ConsoleSeq native tests passed\n";
  return 0;
}
