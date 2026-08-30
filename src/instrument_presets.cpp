#include "instrument_presets.hpp"

#include <algorithm>

namespace consoleseq {

const std::vector<PresetDefinition>& instrument_presets() {
  static const std::vector<PresetDefinition> presets{
      // Pianos and keys.
      {"piano_classic", "Classical Piano", "Pianos", ChannelType::Piano, Oscillator::Sine, 60, .003F, .34F, .20F, .34F, .43F, .68F, .01F},
      {"piano_grand", "Studio Grand", "Pianos", ChannelType::Piano, Oscillator::Sine, 60, .002F, .42F, .24F, .46F, .42F, .78F, .02F},
      {"piano_bright", "Bright Piano", "Pianos", ChannelType::Piano, Oscillator::Sine, 60, .003F, .22F, .18F, .22F, .42F, .88F, .02F},
      {"piano_soft", "Soft Piano", "Pianos", ChannelType::Piano, Oscillator::Sine, 60, .012F, .38F, .25F, .40F, .44F, .42F, .00F},
      {"rhodes", "Rhodes Piano", "Pianos", ChannelType::Piano, Oscillator::Sine, 60, .008F, .58F, .35F, .64F, .40F, .54F, .10F},
      {"electric_keys", "Electric Keys", "Pianos", ChannelType::Piano, Oscillator::Sine, 60, .008F, .52F, .32F, .55F, .40F, .62F, .08F},

      // Kicks.
      {"kick_deep", "Deep Kick", "Kicks", ChannelType::Drum, Oscillator::Sine, 36, .001F, .1F, 0.F, .1F, .88F, .45F, .10F},
      {"kick_punch", "Punch Kick", "Kicks", ChannelType::Drum, Oscillator::Sine, 36, .001F, .1F, 0.F, .1F, .90F, .72F, .22F},
      {"kick_808", "808 Kick", "Kicks", ChannelType::Drum, Oscillator::Sine, 36, .001F, .1F, 0.F, .1F, .82F, .35F, .30F},
      {"kick_trap_hard", "Trap Hard Kick", "Kicks", ChannelType::Drum, Oscillator::Sine, 36, .001F, .1F, 0.F, .1F, .82F, .84F, .55F},
      {"kick_trap_soft", "Trap Soft Kick", "Kicks", ChannelType::Drum, Oscillator::Sine, 36, .001F, .1F, 0.F, .1F, .78F, .30F, .03F},
      {"kick_distorted", "Distorted Kick", "Kicks", ChannelType::Drum, Oscillator::Sine, 36, .001F, .1F, 0.F, .1F, .68F, .70F, .85F},
      {"kick_detroit", "Detroit Kick", "Kicks", ChannelType::Drum, Oscillator::Sine, 36, .001F, .1F, 0.F, .1F, .76F, .60F, .32F},

      // Basses and 808s.
      {"bass_saw", "Saw Bass", "Basses", ChannelType::Bass, Oscillator::Saw, 36, .010F, .20F, .30F, .16F, .56F, .60F, .10F},
      {"bass_square", "Square Bass", "Basses", ChannelType::Bass, Oscillator::Square, 36, .006F, .16F, .38F, .18F, .50F, .45F, .18F},
      {"bass_sub", "Sub Bass", "Basses", ChannelType::Bass, Oscillator::Sine, 36, .018F, .28F, .58F, .32F, .64F, .24F, .06F},
      {"bass_pluck", "Pluck Bass", "Basses", ChannelType::Bass, Oscillator::Saw, 40, .002F, .11F, .12F, .10F, .54F, .76F, .24F},
      {"bass_808_short", "808 Clean Short", "Basses", ChannelType::Bass, Oscillator::Sine, 36, .001F, .10F, .10F, .12F, .72F, .20F, .08F},
      {"bass_808_long", "808 Clean Long", "Basses", ChannelType::Bass, Oscillator::Sine, 36, .008F, .35F, .88F, 1.20F, .70F, .18F, .12F},
      {"bass_808_distorted", "808 Distorted", "Basses", ChannelType::Bass, Oscillator::Sine, 36, .002F, .22F, .68F, .68F, .58F, .30F, .82F},
      {"bass_rap_modern", "Modern Rap Bass", "Basses", ChannelType::Bass, Oscillator::Square, 38, .006F, .18F, .55F, .34F, .52F, .52F, .34F},

      // Modeled guitars.
      {"guitar_acoustic", "Acoustic Guitar", "Guitars", ChannelType::Synth, Oscillator::Triangle, 52, .002F, .42F, .18F, .38F, .40F, .64F, .02F},
      {"guitar_electric_clean", "Electric Guitar Clean", "Guitars", ChannelType::Synth, Oscillator::Triangle, 52, .006F, .34F, .30F, .52F, .38F, .72F, .12F},
      {"guitar_electric_drive", "Electric Guitar Drive", "Guitars", ChannelType::Synth, Oscillator::Saw, 52, .004F, .28F, .42F, .48F, .30F, .58F, .68F},

      // Strings.
      {"strings_ensemble", "String Ensemble", "Strings", ChannelType::Synth, Oscillator::Saw, 60, .24F, .72F, .78F, 1.40F, .27F, .42F, .04F},
      {"strings_solo", "Solo Strings", "Strings", ChannelType::Synth, Oscillator::Triangle, 67, .12F, .44F, .70F, .90F, .31F, .58F, .06F},

      // Synths, FM, leads, pads, and plucks.
      {"lead_saw", "Saw Lead", "Synths", ChannelType::Synth, Oscillator::Saw, 72, .012F, .18F, .58F, .24F, .35F, .82F, .12F},
      {"lead_square", "Square Lead", "Synths", ChannelType::Synth, Oscillator::Square, 72, .006F, .14F, .52F, .20F, .32F, .66F, .08F},
      {"lead_analog", "Analog Lead", "Synths", ChannelType::Synth, Oscillator::Saw, 69, .018F, .24F, .64F, .32F, .34F, .58F, .18F},
      {"lead_fm", "FM Lead", "Synths", ChannelType::Synth, Oscillator::Sine, 72, .006F, .18F, .52F, .26F, .34F, .78F, .06F},
      {"fm_bell", "FM Bell", "Synths", ChannelType::Synth, Oscillator::Sine, 72, .002F, .82F, .04F, .70F, .36F, .92F, .02F},
      {"fm_keys", "FM Keys", "Synths", ChannelType::Synth, Oscillator::Sine, 60, .008F, .48F, .28F, .48F, .36F, .72F, .05F},
      {"pad_warm", "Warm Pad", "Synths", ChannelType::Synth, Oscillator::Saw, 60, .38F, .70F, .72F, 1.20F, .28F, .32F, .04F},
      {"pad_air", "Air Pad", "Synths", ChannelType::Synth, Oscillator::Triangle, 60, .52F, .86F, .76F, 1.60F, .25F, .68F, .01F},
      {"pluck", "Synth Pluck", "Synths", ChannelType::Synth, Oscillator::Square, 67, .002F, .09F, .08F, .12F, .38F, .72F, .16F},
      {"pluck_newjazz", "New Jazz Pluck", "Synths", ChannelType::Synth, Oscillator::Triangle, 72, .001F, .07F, .06F, .10F, .38F, .84F, .22F},

      // Snares, claps, and rimshots.
      {"snare_tight", "Tight Snare", "Snares", ChannelType::Drum, Oscillator::Sine, 38, .001F, .1F, 0.F, .1F, .68F, .70F, .08F},
      {"snare_big", "Big Snare", "Snares", ChannelType::Drum, Oscillator::Sine, 38, .001F, .1F, 0.F, .1F, .62F, .58F, .15F},
      {"snare_trap", "Trap Snare", "Snares", ChannelType::Drum, Oscillator::Sine, 38, .001F, .1F, 0.F, .1F, .62F, .82F, .18F},
      {"snare_detroit", "Detroit Snare", "Snares", ChannelType::Drum, Oscillator::Sine, 38, .001F, .1F, 0.F, .1F, .58F, .64F, .30F},
      {"rimshot", "Trap Rimshot", "Snares", ChannelType::Drum, Oscillator::Sine, 37, .001F, .1F, 0.F, .1F, .58F, .88F, .12F},
      {"clap", "Hand Clap", "Snares", ChannelType::Drum, Oscillator::Sine, 39, .001F, .1F, 0.F, .1F, .58F, .82F, .05F},
      {"clap_trap", "Trap Clap", "Snares", ChannelType::Drum, Oscillator::Sine, 39, .001F, .1F, 0.F, .1F, .56F, .90F, .16F},

      // Hi-hats.
      {"hihat_closed", "Closed Hat", "Hi-hats", ChannelType::Drum, Oscillator::Sine, 42, .001F, .1F, 0.F, .1F, .44F, .78F, .02F},
      {"hihat_open", "Open Hat", "Hi-hats", ChannelType::Drum, Oscillator::Sine, 46, .001F, .1F, 0.F, .1F, .38F, .85F, .02F},
      {"hihat_short", "Trap Short Hat", "Hi-hats", ChannelType::Drum, Oscillator::Sine, 42, .001F, .1F, 0.F, .1F, .42F, .92F, .04F},
      {"hihat_metal", "Metal Hat", "Hi-hats", ChannelType::Drum, Oscillator::Sine, 42, .001F, .1F, 0.F, .1F, .36F, .96F, .12F},
      {"hihat_roll", "Hat Roll", "Hi-hats", ChannelType::Drum, Oscillator::Sine, 42, .001F, .1F, 0.F, .1F, .38F, .90F, .04F},

      // Percussion and style sounds.
      {"tom_low", "Low Tom", "Percussion", ChannelType::Drum, Oscillator::Sine, 45, .001F, .1F, 0.F, .1F, .64F, .42F, .08F},
      {"tom_high", "High Tom", "Percussion", ChannelType::Drum, Oscillator::Sine, 50, .001F, .1F, 0.F, .1F, .58F, .62F, .06F},
      {"perc_click", "Perc Click", "Percussion", ChannelType::Drum, Oscillator::Sine, 56, .001F, .1F, 0.F, .1F, .48F, .92F, .12F},
      {"perc_newjazz", "New Jazz Perc", "Percussion", ChannelType::Drum, Oscillator::Sine, 60, .001F, .1F, 0.F, .1F, .46F, .78F, .20F},
      {"perc_jerk", "Jerk Perc", "Percussion", ChannelType::Drum, Oscillator::Sine, 61, .001F, .1F, 0.F, .1F, .46F, .86F, .32F},
      {"perc_detroit", "Detroit Perc", "Percussion", ChannelType::Drum, Oscillator::Sine, 62, .001F, .1F, 0.F, .1F, .44F, .66F, .25F},
      {"cowbell", "Rap Cowbell", "Percussion", ChannelType::Drum, Oscillator::Sine, 56, .001F, .1F, 0.F, .1F, .42F, .82F, .16F},
      {"shaker", "Trap Shaker", "Percussion", ChannelType::Drum, Oscillator::Sine, 70, .001F, .1F, 0.F, .1F, .36F, .88F, .02F},

      // Generated effects.
      {"fx_impact", "Impact", "FX", ChannelType::Drum, Oscillator::Sine, 36, .001F, .1F, 0.F, .1F, .48F, .58F, .30F},
      {"fx_riser", "Noise Riser", "FX", ChannelType::Drum, Oscillator::Sine, 72, .001F, .1F, 0.F, .1F, .34F, .88F, .04F},
      {"fx_reverse", "Reverse Cymbal", "FX", ChannelType::Drum, Oscillator::Sine, 72, .001F, .1F, 0.F, .1F, .34F, .92F, .03F},
      {"fx_vinyl", "Vinyl Texture", "FX", ChannelType::Drum, Oscillator::Sine, 60, .001F, .1F, 0.F, .1F, .24F, .42F, .02F},
  };
  return presets;
}

const PresetDefinition* find_instrument_preset(const std::string& requested_id) {
  std::string id = requested_id;
  if (id == "kick") id = "kick_punch";
  if (id == "snare") id = "snare_tight";
  if (id == "hihat") id = "hihat_closed";
  if (id == "piano") id = "piano_bright";
  if (id == "bass") id = "bass_saw";
  const auto& presets = instrument_presets();
  const auto found = std::find_if(presets.begin(), presets.end(),
      [&](const PresetDefinition& preset) { return id == preset.id; });
  return found == presets.end() ? nullptr : &*found;
}

}  // namespace consoleseq
