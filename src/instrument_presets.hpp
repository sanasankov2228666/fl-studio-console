#pragma once

#include "console_seq.hpp"

#include <string>
#include <vector>

namespace consoleseq {

struct PresetDefinition {
  const char* id;
  const char* name;
  const char* category;
  ChannelType type;
  Oscillator oscillator;
  int base_note;
  float attack;
  float decay;
  float sustain;
  float release;
  float volume;
  float tone;
  float drive;
};

const std::vector<PresetDefinition>& instrument_presets();
const PresetDefinition* find_instrument_preset(const std::string& id);

}  // namespace consoleseq
