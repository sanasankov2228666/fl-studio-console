#include "console_seq.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <random>
#include <stdexcept>
#include <utility>

#include <nlohmann/json.hpp>

#ifdef CONSOLESEQ_WITH_SNDFILE
#include <sndfile.h>
#endif

namespace consoleseq {
namespace {

using json = nlohmann::json;
constexpr double kPi = 3.14159265358979323846;

float clampf(float value, float low, float high) {
  return std::max(low, std::min(high, value));
}

int clamp_note(int value) { return std::max(0, std::min(127, value)); }

const char* channel_type_name(ChannelType type) {
  switch (type) {
    case ChannelType::Drum: return "drum";
    case ChannelType::Piano: return "piano";
    case ChannelType::Bass: return "bass";
    case ChannelType::Synth: return "synth";
  }
  return "synth";
}

ChannelType channel_type_from_name(const std::string& value) {
  if (value == "drum") return ChannelType::Drum;
  if (value == "piano") return ChannelType::Piano;
  if (value == "bass") return ChannelType::Bass;
  return ChannelType::Synth;
}

const char* oscillator_name(Oscillator oscillator) {
  switch (oscillator) {
    case Oscillator::Sine: return "sine";
    case Oscillator::Square: return "square";
    case Oscillator::Saw: return "saw";
  }
  return "sine";
}

Oscillator oscillator_from_name(const std::string& value) {
  if (value == "square") return Oscillator::Square;
  if (value == "saw") return Oscillator::Saw;
  return Oscillator::Sine;
}

struct PresetDefinition {
  const char* id;
  const char* name;
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

constexpr std::array<PresetDefinition, 22> kPresets{{
    {"kick_deep", "Deep Kick", ChannelType::Drum, Oscillator::Sine, 36, .001F, .1F, 0.F, .1F, .88F, .45F, .10F},
    {"kick_punch", "Punch Kick", ChannelType::Drum, Oscillator::Sine, 36, .001F, .1F, 0.F, .1F, .90F, .72F, .22F},
    {"kick_808", "808 Kick", ChannelType::Drum, Oscillator::Sine, 36, .001F, .1F, 0.F, .1F, .82F, .35F, .30F},
    {"snare_tight", "Tight Snare", ChannelType::Drum, Oscillator::Sine, 38, .001F, .1F, 0.F, .1F, .68F, .70F, .08F},
    {"snare_big", "Big Snare", ChannelType::Drum, Oscillator::Sine, 38, .001F, .1F, 0.F, .1F, .62F, .58F, .15F},
    {"clap", "Hand Clap", ChannelType::Drum, Oscillator::Sine, 39, .001F, .1F, 0.F, .1F, .58F, .82F, .05F},
    {"hihat_closed", "Closed Hat", ChannelType::Drum, Oscillator::Sine, 42, .001F, .1F, 0.F, .1F, .44F, .78F, .02F},
    {"hihat_open", "Open Hat", ChannelType::Drum, Oscillator::Sine, 46, .001F, .1F, 0.F, .1F, .38F, .85F, .02F},
    {"tom_low", "Low Tom", ChannelType::Drum, Oscillator::Sine, 45, .001F, .1F, 0.F, .1F, .64F, .42F, .08F},
    {"tom_high", "High Tom", ChannelType::Drum, Oscillator::Sine, 50, .001F, .1F, 0.F, .1F, .58F, .62F, .06F},
    {"perc_click", "Perc Click", ChannelType::Drum, Oscillator::Sine, 56, .001F, .1F, 0.F, .1F, .48F, .92F, .12F},
    {"piano_bright", "Bright Piano", ChannelType::Piano, Oscillator::Sine, 60, .003F, .22F, .18F, .22F, .42F, .88F, .02F},
    {"piano_soft", "Soft Piano", ChannelType::Piano, Oscillator::Sine, 60, .012F, .38F, .25F, .40F, .44F, .42F, .00F},
    {"electric_keys", "Electric Keys", ChannelType::Piano, Oscillator::Sine, 60, .008F, .52F, .32F, .55F, .40F, .62F, .08F},
    {"bass_saw", "Saw Bass", ChannelType::Bass, Oscillator::Saw, 36, .010F, .20F, .30F, .16F, .56F, .60F, .10F},
    {"bass_square", "Square Bass", ChannelType::Bass, Oscillator::Square, 36, .006F, .16F, .38F, .18F, .50F, .45F, .18F},
    {"bass_sub", "Sub Bass", ChannelType::Bass, Oscillator::Sine, 36, .018F, .28F, .58F, .32F, .64F, .24F, .06F},
    {"bass_pluck", "Pluck Bass", ChannelType::Bass, Oscillator::Saw, 40, .002F, .11F, .12F, .10F, .54F, .76F, .24F},
    {"lead_saw", "Saw Lead", ChannelType::Synth, Oscillator::Saw, 72, .012F, .18F, .58F, .24F, .35F, .82F, .12F},
    {"lead_square", "Square Lead", ChannelType::Synth, Oscillator::Square, 72, .006F, .14F, .52F, .20F, .32F, .66F, .08F},
    {"pad_warm", "Warm Pad", ChannelType::Synth, Oscillator::Saw, 60, .38F, .70F, .72F, 1.20F, .28F, .32F, .04F},
    {"pluck", "Synth Pluck", ChannelType::Synth, Oscillator::Square, 67, .002F, .09F, .08F, .12F, .38F, .72F, .16F},
}};

const PresetDefinition* find_preset(std::string id) {
  if (id == "kick") id = "kick_punch";
  if (id == "snare") id = "snare_tight";
  if (id == "hihat") id = "hihat_closed";
  if (id == "piano") id = "piano_bright";
  if (id == "bass") id = "bass_saw";
  const auto found = std::find_if(kPresets.begin(), kPresets.end(),
      [&](const PresetDefinition& preset) { return id == preset.id; });
  return found == kPresets.end() ? nullptr : &*found;
}

json step_to_json(const Step& step) {
  return json{{"active", step.active}, {"note", step.note}, {"velocity", step.velocity}};
}

Step step_from_json(const json& value, int fallback_note) {
  Step step;
  step.active = value.value("active", false);
  step.note = clamp_note(value.value("note", fallback_note));
  step.velocity = clampf(value.value("velocity", 1.0F), 0.0F, 1.0F);
  return step;
}

}  // namespace

Pattern::Pattern(int channel_count, int step_count, std::string name)
    : name_(std::move(name)), steps_(step_count) {
  if (channel_count < 1 || step_count < 1) {
    throw std::invalid_argument("Pattern dimensions must be positive");
  }
  grid_.assign(static_cast<std::size_t>(channel_count),
               std::vector<Step>(static_cast<std::size_t>(step_count)));
}

void Pattern::check_index(int channel, int step) const {
  if (channel < 0 || channel >= channel_count() || step < 0 || step >= steps_) {
    throw std::out_of_range("Pattern channel or step is out of range");
  }
}

void Pattern::set_step(int channel, int step, bool value) {
  check_index(channel, step);
  grid_[static_cast<std::size_t>(channel)][static_cast<std::size_t>(step)].active = value;
}

bool Pattern::get_step(int channel, int step) const {
  return at(channel, step).active;
}

void Pattern::set_note(int channel, int step, int midi_note) {
  check_index(channel, step);
  grid_[static_cast<std::size_t>(channel)][static_cast<std::size_t>(step)].note =
      clamp_note(midi_note);
}

int Pattern::get_note(int channel, int step) const { return at(channel, step).note; }

void Pattern::set_velocity(int channel, int step, float velocity) {
  check_index(channel, step);
  grid_[static_cast<std::size_t>(channel)][static_cast<std::size_t>(step)].velocity =
      clampf(velocity, 0.0F, 1.0F);
}

float Pattern::get_velocity(int channel, int step) const { return at(channel, step).velocity; }

void Pattern::clear() {
  for (auto& row : grid_) {
    for (auto& step : row) step.active = false;
  }
}

void Pattern::resize_channels(int count) {
  if (count < 1) throw std::invalid_argument("Channel count must be positive");
  grid_.resize(static_cast<std::size_t>(count),
               std::vector<Step>(static_cast<std::size_t>(steps_)));
}

void Pattern::resize_steps(int count) {
  if (count < 1 || count > 64) throw std::invalid_argument("Step count must be between 1 and 64");
  for (auto& row : grid_) row.resize(static_cast<std::size_t>(count));
  steps_ = count;
}

int Pattern::channel_count() const { return static_cast<int>(grid_.size()); }
int Pattern::step_count() const { return steps_; }
const std::string& Pattern::name() const { return name_; }
void Pattern::set_name(const std::string& name) { name_ = name; }

const Step& Pattern::at(int channel, int step) const {
  check_index(channel, step);
  return grid_[static_cast<std::size_t>(channel)][static_cast<std::size_t>(step)];
}

Channel::Channel(std::string name, ChannelType type)
    : name_(std::move(name)), type_(type) {}

const std::string& Channel::name() const { return name_; }
void Channel::set_name(const std::string& value) { name_ = value; }
ChannelType Channel::type() const { return type_; }
void Channel::set_type(ChannelType value) { type_ = value; }
float Channel::volume() const { return volume_; }
void Channel::set_volume(float value) { volume_ = clampf(value, 0.0F, 1.0F); }
float Channel::pan() const { return pan_; }
void Channel::set_pan(float value) { pan_ = clampf(value, -1.0F, 1.0F); }
bool Channel::muted() const { return mute_; }
void Channel::set_mute(bool value) { mute_ = value; }
bool Channel::soloed() const { return solo_; }
void Channel::set_solo(bool value) { solo_ = value; }
int Channel::base_note() const { return base_note_; }
void Channel::set_base_note(int value) { base_note_ = clamp_note(value); }
Oscillator Channel::oscillator() const { return oscillator_; }
void Channel::set_oscillator(Oscillator value) { oscillator_ = value; }

void Channel::set_adsr(float attack, float decay, float sustain, float release) {
  attack_ = clampf(attack, 0.0001F, 10.0F);
  decay_ = clampf(decay, 0.0001F, 10.0F);
  sustain_ = clampf(sustain, 0.0F, 1.0F);
  release_ = clampf(release, 0.0001F, 10.0F);
}

std::array<float, 4> Channel::adsr() const { return {attack_, decay_, sustain_, release_}; }
float Channel::tone() const { return tone_; }
void Channel::set_tone(float value) { tone_ = clampf(value, 0.0F, 1.0F); }
float Channel::drive() const { return drive_; }
void Channel::set_drive(float value) { drive_ = clampf(value, 0.0F, 1.0F); }
const std::string& Channel::sample_path() const { return sample_path_; }
const std::string& Channel::builtin_id() const { return builtin_id_; }

bool Channel::set_sample(const std::string& filename) {
  std::ifstream stream(std::filesystem::u8path(filename), std::ios::binary);
  if (!stream.good()) return false;
  sample_path_ = filename;
  return true;
}

void Channel::set_builtin_id(const std::string& value) { builtin_id_ = value; }

void Channel::set_synth_param(const std::string& parameter, float value) {
  if (parameter == "attack") attack_ = clampf(value, 0.0001F, 10.0F);
  else if (parameter == "decay") decay_ = clampf(value, 0.0001F, 10.0F);
  else if (parameter == "sustain") sustain_ = clampf(value, 0.0F, 1.0F);
  else if (parameter == "release") release_ = clampf(value, 0.0001F, 10.0F);
  else if (parameter == "tone") tone_ = clampf(value, 0.0F, 1.0F);
  else if (parameter == "drive") drive_ = clampf(value, 0.0F, 1.0F);
  else if (parameter == "base_note") base_note_ = clamp_note(static_cast<int>(std::lround(value)));
  else if (parameter == "oscillator") {
    const int index = std::max(0, std::min(2, static_cast<int>(std::lround(value))));
    oscillator_ = static_cast<Oscillator>(index);
  } else {
    throw std::invalid_argument("Unknown synthesizer parameter: " + parameter);
  }
}

Song::Song(int channel_count, int slots) {
  if (channel_count < 1 || slots < 1) throw std::invalid_argument("Song dimensions must be positive");
  arrangement_.assign(static_cast<std::size_t>(channel_count),
                      std::vector<int>(static_cast<std::size_t>(slots), -1));
}

void Song::check_index(int channel, int slot) const {
  if (channel < 0 || channel >= channel_count() || slot < 0 || slot >= slot_count()) {
    throw std::out_of_range("Song channel or slot is out of range");
  }
}

void Song::set_pattern_at(int channel, int slot, int pattern_id) {
  check_index(channel, slot);
  arrangement_[static_cast<std::size_t>(channel)][static_cast<std::size_t>(slot)] = pattern_id;
}

int Song::get_pattern_at(int channel, int slot) const {
  check_index(channel, slot);
  return arrangement_[static_cast<std::size_t>(channel)][static_cast<std::size_t>(slot)];
}

void Song::clear() {
  for (auto& row : arrangement_) std::fill(row.begin(), row.end(), -1);
}

void Song::resize_channels(int count) {
  if (count < 1) throw std::invalid_argument("Channel count must be positive");
  const auto slots = arrangement_.empty() ? static_cast<std::size_t>(kDefaultSongSlots)
                                           : arrangement_.front().size();
  arrangement_.resize(static_cast<std::size_t>(count), std::vector<int>(slots, -1));
}

int Song::channel_count() const { return static_cast<int>(arrangement_.size()); }
int Song::slot_count() const {
  return arrangement_.empty() ? 0 : static_cast<int>(arrangement_.front().size());
}

Engine::Engine() {
  runtime_.reserve(32);
  new_project();
}
Engine::~Engine() { shutdown(); }

Channel Engine::make_preset_channel(const std::string& preset_id) {
  const auto* preset = find_preset(preset_id);
  if (!preset) throw std::invalid_argument("Unknown instrument preset: " + preset_id);
  Channel channel(preset->name, preset->type);
  channel.builtin_id_ = preset->id;
  channel.base_note_ = preset->base_note;
  channel.oscillator_ = preset->oscillator;
  channel.set_adsr(preset->attack, preset->decay, preset->sustain, preset->release);
  channel.volume_ = preset->volume;
  channel.tone_ = preset->tone;
  channel.drive_ = preset->drive;
  if (preset->type == ChannelType::Drum) channel.sample_ = generate_builtin(preset->id);
  return channel;
}

std::vector<std::string> Engine::preset_ids() {
  std::vector<std::string> result;
  result.reserve(kPresets.size());
  for (const auto& preset : kPresets) result.emplace_back(preset.id);
  return result;
}

void Engine::new_project() {
  stop();
  std::lock_guard<std::mutex> lock(state_mutex_);
  ProjectState project;
  project.bpm = 120.0F;
  project.loop = true;
  project.song_mode = false;
  project.current_pattern = 0;

  Channel kick = make_preset_channel("kick_punch"); kick.set_name("Kick");
  Channel snare = make_preset_channel("snare_tight"); snare.set_name("Snare"); snare.set_volume(.72F);
  Channel hat = make_preset_channel("hihat_closed"); hat.set_name("HiHat"); hat.set_volume(.46F);
  Channel piano = make_preset_channel("piano_bright"); piano.set_name("Piano");
  Channel bass = make_preset_channel("bass_saw"); bass.set_name("Bass");
  project.channels = {kick, snare, hat, piano, bass};

  Pattern demo(5, kDefaultSteps, "Demo Beat");
  for (int step : {0, 4, 8, 12}) demo.set_step(0, step, true);
  for (int step : {4, 12}) demo.set_step(1, step, true);
  for (int step = 0; step < kDefaultSteps; step += 2) demo.set_step(2, step, true);
  for (int step : {0, 8}) {
    demo.set_step(3, step, true);
    demo.set_note(3, step, step == 0 ? 60 : 67);
  }
  const std::array<int, 4> bass_steps{{0, 6, 8, 14}};
  const std::array<int, 4> bass_notes{{36, 36, 43, 34}};
  for (std::size_t i = 0; i < bass_steps.size(); ++i) {
    demo.set_step(4, bass_steps[i], true);
    demo.set_note(4, bass_steps[i], bass_notes[i]);
  }
  project.patterns.push_back(demo);
  project.patterns.emplace_back(5, kDefaultSteps, "Pattern 2");
  project.patterns.emplace_back(5, kDefaultSteps, "Pattern 3");
  project.patterns.emplace_back(5, kDefaultSteps, "Pattern 4");
  project.song = Song(5, kDefaultSongSlots);
  for (int channel = 0; channel < 5; ++channel) {
    for (int slot = 0; slot < 4; ++slot) project.song.set_pattern_at(channel, slot, 0);
  }
  editable_ = std::move(project);
  publish_locked();
}

void Engine::publish_locked() {
  ++editable_.revision;
  std::atomic_store_explicit(&published_, std::make_shared<const ProjectState>(editable_),
                             std::memory_order_release);
}

bool Engine::start() {
  if (running_.exchange(true)) return audio_available_.load();
#ifdef CONSOLESEQ_WITH_AUDIO
  std::vector<RtAudio::Api> apis;
  RtAudio::getCompiledApi(apis);
  const char* requested_name = std::getenv("CONSOLESEQ_AUDIO_API");
  const bool wsl_environment = std::getenv("WSL_DISTRO_NAME") != nullptr;
  std::stable_sort(apis.begin(), apis.end(), [&](RtAudio::Api left, RtAudio::Api right) {
    const auto priority = [&](RtAudio::Api api) {
      const std::string name = RtAudio::getApiName(api);
      if (requested_name && name == requested_name) return 0;
      if (api == RtAudio::WINDOWS_WASAPI || api == RtAudio::MACOSX_CORE) return 1;
      if (api == RtAudio::LINUX_ALSA) return 2;
      if (api == RtAudio::LINUX_PULSE) return 3;
      return 4;
    };
    return priority(left) < priority(right);
  });

  std::string errors;
  for (const auto api : apis) {
    if (api == RtAudio::RTAUDIO_DUMMY) continue;
    const std::string api_name = RtAudio::getApiName(api);
    // A stale WSLg PulseServer can block libpulse for about 30 seconds. WSL
    // therefore uses its fast ALSA probe by default and tries Pulse only when
    // the user explicitly opts in after confirming WSLg audio works.
    if (wsl_environment && api == RtAudio::LINUX_PULSE &&
        (!requested_name || api_name != requested_name)) {
      continue;
    }
    try {
      auto candidate = std::make_unique<RtAudio>(api);
      if (candidate->getDeviceCount() < 1) throw std::runtime_error("no output device found");
      RtAudio::StreamParameters parameters;
      parameters.deviceId = candidate->getDefaultOutputDevice();
      parameters.nChannels = 2;
      parameters.firstChannel = 0;
      unsigned int frames = kDefaultBufferFrames;
      candidate->openStream(&parameters, nullptr, RTAUDIO_FLOAT32, kSampleRate, &frames,
                            &Engine::audio_callback, this);
      candidate->startStream();
      audio_ = std::move(candidate);
      audio_available_.store(true);
      audio_status_ = "RtAudio output active (" + api_name + ")";
      return true;
    } catch (const std::exception& error) {
      if (!errors.empty()) errors += "; ";
      errors += api_name + ": " + error.what();
    }
  }
  audio_.reset();
  audio_status_ = "silent timing mode: " +
                  (errors.empty() ? std::string("no compiled audio API") : errors);
#else
  audio_status_ = "silent timing mode: built without RtAudio";
#endif
  audio_available_.store(false);
  silent_thread_ = std::thread(&Engine::silent_loop, this);
  return false;
}

void Engine::shutdown() {
  if (!running_.exchange(false)) return;
#ifdef CONSOLESEQ_WITH_AUDIO
  if (audio_) {
    try {
      if (audio_->isStreamRunning()) audio_->stopStream();
      if (audio_->isStreamOpen()) audio_->closeStream();
    } catch (...) {
    }
    audio_.reset();
  }
#endif
  if (silent_thread_.joinable()) silent_thread_.join();
  audio_available_.store(false);
}

void Engine::silent_loop() {
  std::vector<float> scratch(static_cast<std::size_t>(kDefaultBufferFrames) * 2U);
  const auto duration = std::chrono::duration<double>(
      static_cast<double>(kDefaultBufferFrames) / static_cast<double>(kSampleRate));
  auto deadline = std::chrono::steady_clock::now();
  while (running_.load()) {
    render(scratch.data(), kDefaultBufferFrames);
    deadline += std::chrono::duration_cast<std::chrono::steady_clock::duration>(duration);
    std::this_thread::sleep_until(deadline);
  }
}

void Engine::play() { playing_.store(true); paused_.store(false); }
void Engine::pause() { paused_.store(true); playing_.store(false); }

void Engine::stop() {
  playing_.store(false);
  paused_.store(false);
  current_step_atomic_.store(0);
  current_song_slot_atomic_.store(0);
  transport_revision_.fetch_add(1);
}

bool Engine::is_playing() const { return playing_.load(); }
bool Engine::audio_available() const { return audio_available_.load(); }
const std::string& Engine::audio_status() const { return audio_status_; }

bool Engine::save_project(const std::string& filename) const {
  try {
    ProjectState state;
    {
      std::lock_guard<std::mutex> lock(state_mutex_);
      state = editable_;
    }
    json root;
    root["format"] = "ConsoleSeq";
    root["version"] = 2;
    root["bpm"] = state.bpm;
    root["loop"] = state.loop;
    root["song_mode"] = state.song_mode;
    root["current_pattern"] = state.current_pattern;
    root["channels"] = json::array();
    for (const auto& channel : state.channels) {
      root["channels"].push_back({
          {"name", channel.name_}, {"type", channel_type_name(channel.type_)},
          {"volume", channel.volume_}, {"pan", channel.pan_}, {"mute", channel.mute_},
          {"solo", channel.solo_}, {"base_note", channel.base_note_},
          {"oscillator", oscillator_name(channel.oscillator_)},
          {"adsr", {channel.attack_, channel.decay_, channel.sustain_, channel.release_}},
          {"tone", channel.tone_}, {"drive", channel.drive_},
          {"sample_path", channel.sample_path_}, {"builtin", channel.builtin_id_}});
    }
    root["patterns"] = json::array();
    for (const auto& pattern : state.patterns) {
      json p{{"name", pattern.name_}, {"steps", pattern.steps_}, {"grid", json::array()}};
      for (const auto& row : pattern.grid_) {
        json json_row = json::array();
        for (const auto& step : row) json_row.push_back(step_to_json(step));
        p["grid"].push_back(std::move(json_row));
      }
      root["patterns"].push_back(std::move(p));
    }
    root["song"] = state.song.arrangement_;

    std::ofstream output(std::filesystem::u8path(filename), std::ios::binary | std::ios::trunc);
    if (!output) throw std::runtime_error("cannot open project for writing");
    output << root.dump(2) << '\n';
    if (!output) throw std::runtime_error("failed while writing project");
    return true;
  } catch (const std::exception& error) {
    std::lock_guard<std::mutex> lock(state_mutex_);
    last_error_ = error.what();
    return false;
  }
}

bool Engine::load_project(const std::string& filename) {
  try {
    std::ifstream input(std::filesystem::u8path(filename), std::ios::binary);
    if (!input) throw std::runtime_error("cannot open project file");
    json root;
    input >> root;
    if (root.value("format", std::string()) != "ConsoleSeq") {
      throw std::runtime_error("not a ConsoleSeq project");
    }
    const auto& channels_json = root.at("channels");
    if (!channels_json.is_array() || channels_json.empty()) {
      throw std::runtime_error("project has no channels");
    }
    if (channels_json.size() > 32) throw std::runtime_error("project exceeds the 32-channel limit");

    ProjectState loaded;
    loaded.bpm = clampf(root.value("bpm", 120.0F), 40.0F, 300.0F);
    loaded.loop = root.value("loop", true);
    loaded.song_mode = root.value("song_mode", false);
    for (const auto& item : channels_json) {
      Channel channel(item.value("name", "Channel"),
                      channel_type_from_name(item.value("type", "synth")));
      channel.set_volume(item.value("volume", 0.8F));
      channel.set_pan(item.value("pan", 0.0F));
      channel.set_mute(item.value("mute", false));
      channel.set_solo(item.value("solo", false));
      channel.set_base_note(item.value("base_note", 60));
      channel.set_oscillator(oscillator_from_name(item.value("oscillator", "sine")));
      if (item.contains("adsr") && item["adsr"].is_array() && item["adsr"].size() == 4) {
        channel.set_adsr(item["adsr"][0].get<float>(), item["adsr"][1].get<float>(),
                         item["adsr"][2].get<float>(), item["adsr"][3].get<float>());
      }
      channel.set_tone(item.value("tone", 0.75F));
      channel.set_drive(item.value("drive", 0.0F));
      channel.builtin_id_ = item.value("builtin", "");
      channel.sample_path_ = item.value("sample_path", "");
      if (!channel.sample_path_.empty()) channel.sample_ = load_audio_file(channel.sample_path_);
      if (!channel.sample_) channel.sample_ = generate_builtin(channel.builtin_id_);
      loaded.channels.push_back(std::move(channel));
    }

    const auto& patterns_json = root.at("patterns");
    if (!patterns_json.is_array() || patterns_json.empty()) {
      throw std::runtime_error("project has no patterns");
    }
    for (const auto& item : patterns_json) {
      const int steps = std::max(1, std::min(64, item.value("steps", kDefaultSteps)));
      Pattern pattern(static_cast<int>(loaded.channels.size()), steps,
                      item.value("name", "Pattern"));
      if (item.contains("grid") && item["grid"].is_array()) {
        for (std::size_t channel = 0;
             channel < pattern.grid_.size() && channel < item["grid"].size(); ++channel) {
          const auto& row = item["grid"][channel];
          for (std::size_t step = 0;
               step < pattern.grid_[channel].size() && step < row.size(); ++step) {
            pattern.grid_[channel][step] =
                step_from_json(row[step], loaded.channels[channel].base_note_);
          }
        }
      }
      loaded.patterns.push_back(std::move(pattern));
    }
    loaded.current_pattern = std::max(
        0, std::min(static_cast<int>(loaded.patterns.size()) - 1,
                    root.value("current_pattern", 0)));
    loaded.song = Song(static_cast<int>(loaded.channels.size()), kDefaultSongSlots);
    if (root.contains("song") && root["song"].is_array()) {
      const auto& song_json = root["song"];
      for (std::size_t channel = 0;
           channel < loaded.song.arrangement_.size() && channel < song_json.size(); ++channel) {
        if (!song_json[channel].is_array()) continue;
        for (std::size_t slot = 0;
             slot < loaded.song.arrangement_[channel].size() && slot < song_json[channel].size();
             ++slot) {
          int pattern_id = song_json[channel][slot].get<int>();
          if (pattern_id < -1 || pattern_id >= static_cast<int>(loaded.patterns.size())) {
            pattern_id = -1;
          }
          loaded.song.arrangement_[channel][slot] = pattern_id;
        }
      }
    }

    stop();
    std::lock_guard<std::mutex> lock(state_mutex_);
    editable_ = std::move(loaded);
    last_error_.clear();
    publish_locked();
    return true;
  } catch (const std::exception& error) {
    std::lock_guard<std::mutex> lock(state_mutex_);
    last_error_ = error.what();
    return false;
  }
}

std::string Engine::last_error() const {
  std::lock_guard<std::mutex> lock(state_mutex_);
  return last_error_;
}

float Engine::bpm() const { std::lock_guard<std::mutex> lock(state_mutex_); return editable_.bpm; }
void Engine::set_bpm(float value) {
  std::lock_guard<std::mutex> lock(state_mutex_); editable_.bpm = clampf(value, 40.0F, 300.0F); publish_locked();
}
bool Engine::loop() const { std::lock_guard<std::mutex> lock(state_mutex_); return editable_.loop; }
void Engine::set_loop(bool value) { std::lock_guard<std::mutex> lock(state_mutex_); editable_.loop = value; publish_locked(); }
bool Engine::song_mode() const { std::lock_guard<std::mutex> lock(state_mutex_); return editable_.song_mode; }
void Engine::set_song_mode(bool value) { std::lock_guard<std::mutex> lock(state_mutex_); editable_.song_mode = value; publish_locked(); stop(); }
int Engine::current_pattern() const { std::lock_guard<std::mutex> lock(state_mutex_); return editable_.current_pattern; }
void Engine::set_current_pattern(int value) {
  std::lock_guard<std::mutex> lock(state_mutex_);
  if (value < 0 || value >= static_cast<int>(editable_.patterns.size())) throw std::out_of_range("Pattern index is out of range");
  editable_.current_pattern = value; publish_locked();
}
int Engine::current_step() const { return current_step_atomic_.load(); }
int Engine::current_song_slot() const { return current_song_slot_atomic_.load(); }
int Engine::channel_count() const { std::lock_guard<std::mutex> lock(state_mutex_); return static_cast<int>(editable_.channels.size()); }
int Engine::pattern_count() const { std::lock_guard<std::mutex> lock(state_mutex_); return static_cast<int>(editable_.patterns.size()); }
int Engine::step_count() const { std::lock_guard<std::mutex> lock(state_mutex_); return editable_.patterns.at(static_cast<std::size_t>(editable_.current_pattern)).step_count(); }
int Engine::song_slot_count() const { std::lock_guard<std::mutex> lock(state_mutex_); return editable_.song.slot_count(); }
void Engine::set_step_count(int count) {
  if (count != 16 && count != 32 && count != 64) {
    throw std::invalid_argument("Step count must be 16, 32, or 64");
  }
  {
    std::lock_guard<std::mutex> lock(state_mutex_);
    for (auto& pattern : editable_.patterns) {
      const int old_count = pattern.step_count();
      pattern.resize_steps(count);
      if (count > old_count) {
        for (int channel = 0; channel < pattern.channel_count(); ++channel) {
          for (int step = old_count; step < count; ++step) {
            pattern.set_note(channel, step, editable_.channels[static_cast<std::size_t>(channel)].base_note_);
          }
        }
      }
    }
    publish_locked();
  }
  stop();
}
Channel Engine::get_channel(int index) const { std::lock_guard<std::mutex> lock(state_mutex_); return editable_.channels.at(static_cast<std::size_t>(index)); }
Pattern Engine::get_pattern(int index) const { std::lock_guard<std::mutex> lock(state_mutex_); return editable_.patterns.at(static_cast<std::size_t>(index)); }
Song Engine::get_song() const { std::lock_guard<std::mutex> lock(state_mutex_); return editable_.song; }

bool Engine::get_step(int pattern, int channel, int step) const { std::lock_guard<std::mutex> lock(state_mutex_); return editable_.patterns.at(static_cast<std::size_t>(pattern)).get_step(channel, step); }
void Engine::set_step(int pattern, int channel, int step, bool value) { std::lock_guard<std::mutex> lock(state_mutex_); editable_.patterns.at(static_cast<std::size_t>(pattern)).set_step(channel, step, value); publish_locked(); }
int Engine::get_note(int pattern, int channel, int step) const { std::lock_guard<std::mutex> lock(state_mutex_); return editable_.patterns.at(static_cast<std::size_t>(pattern)).get_note(channel, step); }
void Engine::set_note(int pattern, int channel, int step, int note) { std::lock_guard<std::mutex> lock(state_mutex_); editable_.patterns.at(static_cast<std::size_t>(pattern)).set_note(channel, step, note); publish_locked(); }
float Engine::get_velocity(int pattern, int channel, int step) const { std::lock_guard<std::mutex> lock(state_mutex_); return editable_.patterns.at(static_cast<std::size_t>(pattern)).get_velocity(channel, step); }
void Engine::set_velocity(int pattern, int channel, int step, float velocity) { std::lock_guard<std::mutex> lock(state_mutex_); editable_.patterns.at(static_cast<std::size_t>(pattern)).set_velocity(channel, step, velocity); publish_locked(); }
void Engine::clear_pattern(int pattern) { std::lock_guard<std::mutex> lock(state_mutex_); editable_.patterns.at(static_cast<std::size_t>(pattern)).clear(); publish_locked(); }

int Engine::add_pattern(const std::string& name) {
  std::lock_guard<std::mutex> lock(state_mutex_);
  const int index = static_cast<int>(editable_.patterns.size());
  const int steps = editable_.patterns.empty() ? kDefaultSteps : editable_.patterns.front().step_count();
  editable_.patterns.emplace_back(static_cast<int>(editable_.channels.size()), steps,
                                  name.empty() ? "Pattern " + std::to_string(index + 1) : name);
  publish_locked(); return index;
}

int Engine::duplicate_pattern(int pattern) {
  std::lock_guard<std::mutex> lock(state_mutex_);
  Pattern copy = editable_.patterns.at(static_cast<std::size_t>(pattern));
  copy.set_name(copy.name() + " Copy");
  editable_.patterns.push_back(std::move(copy)); publish_locked();
  return static_cast<int>(editable_.patterns.size()) - 1;
}

void Engine::remove_pattern(int pattern) {
  {
    std::lock_guard<std::mutex> lock(state_mutex_);
    if (editable_.patterns.size() <= 1) {
      throw std::runtime_error("A project must contain at least one pattern");
    }
    if (pattern < 0 || pattern >= static_cast<int>(editable_.patterns.size())) {
      throw std::out_of_range("Pattern index is out of range");
    }
    editable_.patterns.erase(editable_.patterns.begin() + pattern);
    for (auto& row : editable_.song.arrangement_) {
      for (auto& pattern_id : row) {
        if (pattern_id == pattern) pattern_id = -1;
        else if (pattern_id > pattern) --pattern_id;
      }
    }
    editable_.current_pattern = std::min(
        editable_.current_pattern, static_cast<int>(editable_.patterns.size()) - 1);
    publish_locked();
  }
  stop();
}

void Engine::set_pattern_name(int pattern, const std::string& name) {
  if (name.empty()) throw std::invalid_argument("Pattern name cannot be empty");
  std::lock_guard<std::mutex> lock(state_mutex_);
  editable_.patterns.at(static_cast<std::size_t>(pattern)).set_name(name);
  publish_locked();
}

void Engine::set_pattern_at(int channel, int slot, int pattern_id) {
  std::lock_guard<std::mutex> lock(state_mutex_);
  if (pattern_id < -1 || pattern_id >= static_cast<int>(editable_.patterns.size())) throw std::out_of_range("Pattern index is out of range");
  editable_.song.set_pattern_at(channel, slot, pattern_id); publish_locked();
}
int Engine::get_pattern_at(int channel, int slot) const { std::lock_guard<std::mutex> lock(state_mutex_); return editable_.song.get_pattern_at(channel, slot); }

int Engine::add_channel(const std::string& preset_id, const std::string& name) {
  Channel channel = make_preset_channel(preset_id);
  if (!name.empty()) channel.set_name(name);
  std::lock_guard<std::mutex> lock(state_mutex_);
  if (editable_.channels.size() >= 32) throw std::runtime_error("The 32-channel limit was reached");
  const int index = static_cast<int>(editable_.channels.size());
  editable_.channels.push_back(std::move(channel));
  const int base_note = editable_.channels.back().base_note_;
  for (auto& pattern : editable_.patterns) {
    pattern.resize_channels(index + 1);
    for (int step = 0; step < pattern.step_count(); ++step) pattern.set_note(index, step, base_note);
  }
  editable_.song.resize_channels(index + 1);
  publish_locked();
  return index;
}

int Engine::duplicate_channel(int channel) {
  std::lock_guard<std::mutex> lock(state_mutex_);
  if (editable_.channels.size() >= 32) throw std::runtime_error("The 32-channel limit was reached");
  if (channel < 0 || channel >= static_cast<int>(editable_.channels.size())) {
    throw std::out_of_range("Channel index is out of range");
  }
  Channel copy = editable_.channels[static_cast<std::size_t>(channel)];
  copy.name_ += " Copy";
  editable_.channels.push_back(std::move(copy));
  for (auto& pattern : editable_.patterns) {
    pattern.grid_.push_back(pattern.grid_[static_cast<std::size_t>(channel)]);
  }
  editable_.song.arrangement_.push_back(
      editable_.song.arrangement_[static_cast<std::size_t>(channel)]);
  publish_locked();
  return static_cast<int>(editable_.channels.size()) - 1;
}

void Engine::remove_channel(int channel) {
  {
    std::lock_guard<std::mutex> lock(state_mutex_);
    if (editable_.channels.size() <= 1) {
      throw std::runtime_error("A project must contain at least one channel");
    }
    if (channel < 0 || channel >= static_cast<int>(editable_.channels.size())) {
      throw std::out_of_range("Channel index is out of range");
    }
    editable_.channels.erase(editable_.channels.begin() + channel);
    for (auto& pattern : editable_.patterns) {
      pattern.grid_.erase(pattern.grid_.begin() + channel);
    }
    editable_.song.arrangement_.erase(editable_.song.arrangement_.begin() + channel);
    publish_locked();
  }
  stop();
}

void Engine::set_channel_preset(int channel, const std::string& preset_id) {
  Channel replacement = make_preset_channel(preset_id);
  std::lock_guard<std::mutex> lock(state_mutex_);
  auto& old = editable_.channels.at(static_cast<std::size_t>(channel));
  const int old_base_note = old.base_note_;
  replacement.pan_ = old.pan_;
  replacement.mute_ = old.mute_;
  replacement.solo_ = old.solo_;
  old = std::move(replacement);
  for (auto& pattern : editable_.patterns) {
    for (int step = 0; step < pattern.step_count(); ++step) {
      auto& note = pattern.grid_[static_cast<std::size_t>(channel)][static_cast<std::size_t>(step)].note;
      if (note == old_base_note) note = old.base_note_;
    }
  }
  publish_locked();
}

void Engine::set_channel_name(int channel, const std::string& name) {
  if (name.empty()) throw std::invalid_argument("Channel name cannot be empty");
  std::lock_guard<std::mutex> lock(state_mutex_);
  editable_.channels.at(static_cast<std::size_t>(channel)).set_name(name);
  publish_locked();
}

void Engine::set_channel_volume(int channel, float value) { std::lock_guard<std::mutex> lock(state_mutex_); editable_.channels.at(static_cast<std::size_t>(channel)).set_volume(value); publish_locked(); }
void Engine::set_channel_pan(int channel, float value) { std::lock_guard<std::mutex> lock(state_mutex_); editable_.channels.at(static_cast<std::size_t>(channel)).set_pan(value); publish_locked(); }
void Engine::set_channel_mute(int channel, bool value) { std::lock_guard<std::mutex> lock(state_mutex_); editable_.channels.at(static_cast<std::size_t>(channel)).set_mute(value); publish_locked(); }
void Engine::set_channel_solo(int channel, bool value) { std::lock_guard<std::mutex> lock(state_mutex_); editable_.channels.at(static_cast<std::size_t>(channel)).set_solo(value); publish_locked(); }
void Engine::set_channel_base_note(int channel, int value) { std::lock_guard<std::mutex> lock(state_mutex_); editable_.channels.at(static_cast<std::size_t>(channel)).set_base_note(value); publish_locked(); }

bool Engine::set_channel_sample(int channel, const std::string& filename) {
  auto sample = load_audio_file(filename);
  if (!sample || sample->empty()) {
    std::lock_guard<std::mutex> lock(state_mutex_);
    last_error_ = "Could not decode WAV file; the built-in sound was kept";
    return false;
  }
  std::lock_guard<std::mutex> lock(state_mutex_);
  auto& target = editable_.channels.at(static_cast<std::size_t>(channel));
  if (target.type_ != ChannelType::Drum || !find_preset(target.builtin_id_) ||
      find_preset(target.builtin_id_)->type != ChannelType::Drum) {
    target.builtin_id_ = "perc_click";
  }
  target.sample_path_ = filename; target.sample_ = std::move(sample); target.type_ = ChannelType::Drum;
  last_error_.clear(); publish_locked(); return true;
}

void Engine::set_synth_param(int channel, const std::string& parameter, float value) {
  std::lock_guard<std::mutex> lock(state_mutex_);
  editable_.channels.at(static_cast<std::size_t>(channel)).set_synth_param(parameter, value); publish_locked();
}

std::shared_ptr<const std::vector<float>> Engine::generate_builtin(const std::string& id) {
  std::string sound = id;
  if (sound == "kick") sound = "kick_punch";
  if (sound == "snare") sound = "snare_tight";
  if (sound == "hihat") sound = "hihat_closed";
  const auto* definition = find_preset(sound);
  if (!definition || definition->type != ChannelType::Drum) return {};
  double length = 0.25;
  if (sound == "kick_deep") length = 0.42;
  else if (sound == "kick_808") length = 0.58;
  else if (sound == "snare_tight") length = 0.16;
  else if (sound == "snare_big" || sound == "hihat_open") length = 0.42;
  else if (sound == "clap") length = 0.28;
  else if (sound == "hihat_closed" || sound == "perc_click") length = 0.08;
  else if (sound == "tom_low" || sound == "tom_high") length = 0.36;
  auto sample = std::make_shared<std::vector<float>>(static_cast<std::size_t>(length * kSampleRate));
  unsigned int seed = 0xC05E051U;
  for (const unsigned char character : sound) seed = seed * 33U + character;
  std::mt19937 random(seed);
  std::uniform_real_distribution<float> noise(-1.0F, 1.0F);
  double phase = 0.0;
  float previous_noise = 0.0F;
  float lowpass = 0.0F;
  for (std::size_t i = 0; i < sample->size(); ++i) {
    const double time = static_cast<double>(i) / kSampleRate;
    float value = 0.0F;
    if (sound == "kick_deep" || sound == "kick_punch" || sound == "kick_808") {
      const bool deep = sound == "kick_deep";
      const bool eight_oh_eight = sound == "kick_808";
      const double base = eight_oh_eight ? 42.0 : (deep ? 43.0 : 50.0);
      const double sweep = eight_oh_eight ? 88.0 : (deep ? 105.0 : 155.0);
      const double sweep_rate = eight_oh_eight ? 11.0 : (deep ? 18.0 : 31.0);
      const double decay = eight_oh_eight ? 6.2 : (deep ? 11.0 : 18.0);
      const double frequency = base + sweep * std::exp(-time * sweep_rate);
      phase += 2.0 * kPi * frequency / kSampleRate;
      value = static_cast<float>(std::sin(phase) * std::exp(-time * decay));
      if (!eight_oh_eight) {
        value += static_cast<float>(0.18 * (1.0 - 2.0 * time / .012) *
                                    std::exp(-time * 75.0) * (time < .012));
      }
    } else if (sound == "snare_tight" || sound == "snare_big") {
      const bool big = sound == "snare_big";
      const float raw = noise(random);
      lowpass += (big ? .18F : .31F) * (raw - lowpass);
      const float band = raw - lowpass * (big ? .48F : .62F);
      const float body = static_cast<float>(std::sin(2.0 * kPi * (big ? 165.0 : 205.0) * time));
      value = (.76F * band + .34F * body) * static_cast<float>(std::exp(-time * (big ? 10.5 : 27.0)));
    } else if (sound == "clap") {
      const float raw = noise(random);
      lowpass += .16F * (raw - lowpass);
      const float high = raw - lowpass;
      double envelope = 0.0;
      for (double start : {0.0, .032, .064}) {
        if (time >= start) envelope += std::exp(-(time - start) * 72.0);
      }
      if (time >= .085) envelope += .55 * std::exp(-(time - .085) * 16.0);
      value = high * static_cast<float>(.46 * envelope);
    } else if (sound == "hihat_closed" || sound == "hihat_open") {
      const float raw = noise(random);
      const float high = raw - previous_noise * 0.92F;
      previous_noise = raw;
      const double decay = sound == "hihat_open" ? 11.0 : 76.0;
      value = high * static_cast<float>(0.54 * std::exp(-time * decay));
    } else if (sound == "tom_low" || sound == "tom_high") {
      const bool high = sound == "tom_high";
      const double base = high ? 145.0 : 82.0;
      const double frequency = base + (high ? 115.0 : 72.0) * std::exp(-time * 18.0);
      phase += 2.0 * kPi * frequency / kSampleRate;
      value = static_cast<float>((std::sin(phase) + .18 * std::sin(phase * 2.0)) *
                                 std::exp(-time * (high ? 15.0 : 10.5)));
    } else if (sound == "perc_click") {
      phase += 2.0 * kPi * (1250.0 + 900.0 * std::exp(-time * 80.0)) / kSampleRate;
      value = static_cast<float>((.65 * std::sin(phase) + .25 * noise(random)) *
                                 std::exp(-time * 72.0));
    }
    (*sample)[i] = clampf(value, -1.0F, 1.0F);
  }
  return sample;
}

std::shared_ptr<const std::vector<float>> Engine::load_audio_file(const std::string& filename) {
#ifdef CONSOLESEQ_WITH_SNDFILE
  SF_INFO info{};
#ifdef _WIN32
  const std::wstring wide_filename = std::filesystem::u8path(filename).wstring();
  SNDFILE* file = sf_wchar_open(wide_filename.c_str(), SFM_READ, &info);
#else
  SNDFILE* file = sf_open(filename.c_str(), SFM_READ, &info);
#endif
  if (!file || info.frames <= 0 || info.channels <= 0 || info.samplerate <= 0) {
    if (file) sf_close(file);
    return {};
  }
  std::vector<float> interleaved(static_cast<std::size_t>(info.frames) * static_cast<std::size_t>(info.channels));
  const sf_count_t frames_read = sf_readf_float(file, interleaved.data(), info.frames);
  sf_close(file);
  if (frames_read <= 0) return {};
  std::vector<float> mono(static_cast<std::size_t>(frames_read));
  for (sf_count_t frame = 0; frame < frames_read; ++frame) {
    float sum = 0.0F;
    for (int channel = 0; channel < info.channels; ++channel) {
      sum += interleaved[static_cast<std::size_t>(frame) * static_cast<std::size_t>(info.channels) + static_cast<std::size_t>(channel)];
    }
    mono[static_cast<std::size_t>(frame)] = sum / static_cast<float>(info.channels);
  }
  if (info.samplerate == static_cast<int>(kSampleRate)) return std::make_shared<const std::vector<float>>(std::move(mono));
  const auto output_size = static_cast<std::size_t>(std::ceil(static_cast<double>(mono.size()) * kSampleRate / info.samplerate));
  auto output = std::make_shared<std::vector<float>>(output_size);
  const double ratio = static_cast<double>(info.samplerate) / kSampleRate;
  for (std::size_t i = 0; i < output_size; ++i) {
    const double position = i * ratio;
    const std::size_t left = std::min(static_cast<std::size_t>(position), mono.size() - 1);
    const std::size_t right = std::min(left + 1, mono.size() - 1);
    const float fraction = static_cast<float>(position - static_cast<double>(left));
    (*output)[i] = mono[left] + (mono[right] - mono[left]) * fraction;
  }
  return output;
#else
  (void)filename;
  return {};
#endif
}

double Engine::midi_frequency(int note) { return 440.0 * std::pow(2.0, (clamp_note(note) - 69) / 12.0); }

void Engine::reset_runtime_if_needed(const std::shared_ptr<const ProjectState>& state) {
  const auto transport = transport_revision_.load();
  if (runtime_state_revision_ != state->revision || runtime_transport_revision_ != transport) {
    runtime_.resize(state->channels.size());
    for (auto& channel : runtime_) channel = RuntimeChannel{};
    runtime_state_revision_ = state->revision;
    if (runtime_transport_revision_ != transport) {
      global_step_ = 0; step_phase_ = 0.0; runtime_transport_revision_ = transport;
    }
  }
}

void Engine::trigger_voice(RuntimeChannel& runtime, const Channel& channel, const Step& step) {
  Voice* voice = &runtime.voices.front();
  for (auto& candidate : runtime.voices) {
    if (!candidate.active) { voice = &candidate; break; }
    if (candidate.age > voice->age) voice = &candidate;
  }
  *voice = Voice{};
  voice->active = true; voice->velocity = step.velocity; voice->note = step.note;
  voice->sample = channel.sample_;
  if (channel.type_ == ChannelType::Piano) voice->release_at = 0.42;
  else if (channel.type_ == ChannelType::Bass) voice->release_at = 0.24;
  else voice->release_at = std::max(0.28, static_cast<double>(channel.attack_ + channel.decay_ + .12F));
}

void Engine::trigger_step(const std::shared_ptr<const ProjectState>& state, int global_step) {
  if (state->patterns.empty()) return;
  const int steps = state->patterns.front().step_count();
  const int local_step = global_step % steps;
  const int slot = (global_step / steps) % std::max(1, state->song.slot_count());
  current_step_atomic_.store(local_step); current_song_slot_atomic_.store(slot);
  for (std::size_t channel_index = 0; channel_index < state->channels.size(); ++channel_index) {
    int pattern_id = state->current_pattern;
    if (state->song_mode) pattern_id = state->song.get_pattern_at(static_cast<int>(channel_index), slot);
    if (pattern_id < 0 || pattern_id >= static_cast<int>(state->patterns.size())) continue;
    const auto& pattern = state->patterns[static_cast<std::size_t>(pattern_id)];
    const Step& step = pattern.at(static_cast<int>(channel_index), local_step % pattern.step_count());
    if (step.active) trigger_voice(runtime_[channel_index], state->channels[channel_index], step);
  }
}

float Engine::render_voice(Voice& voice, const Channel& channel) {
  if (!voice.active) return 0.0F;
  float value = 0.0F;
  if (channel.type_ == ChannelType::Drum) {
    if (!voice.sample || voice.sample_position >= voice.sample->size()) { voice.active = false; return 0.0F; }
    value = (*voice.sample)[voice.sample_position++];
  } else {
    const double frequency = midi_frequency(voice.note);
    voice.phase += frequency / kSampleRate;
    if (voice.phase >= 1.0) voice.phase -= std::floor(voice.phase);
    if (channel.type_ == ChannelType::Piano) {
      value = static_cast<float>(std::sin(2.0 * kPi * voice.phase) +
                                 (0.10 + channel.tone_ * .34) * std::sin(4.0 * kPi * voice.phase) +
                                 (0.03 + channel.tone_ * .13) * std::sin(6.0 * kPi * voice.phase));
      value *= static_cast<float>(std::exp(-voice.age * (2.8 + channel.tone_ * 2.5)));
    } else {
      if (channel.oscillator_ == Oscillator::Sine) value = static_cast<float>(std::sin(2.0 * kPi * voice.phase));
      else if (channel.oscillator_ == Oscillator::Square) value = voice.phase < 0.5 ? 0.8F : -0.8F;
      else value = static_cast<float>(2.0 * voice.phase - 1.0);
      if (channel.type_ == ChannelType::Bass || channel.tone_ < .99F) {
        const float base_cutoff = 140.0F + channel.tone_ * 1800.0F;
        const float sweep = channel.type_ == ChannelType::Bass ?
            channel.tone_ * 5200.0F * static_cast<float>(std::exp(-voice.age * 8.0)) :
            channel.tone_ * 2600.0F;
        const float cutoff = std::min(16000.0F, base_cutoff + sweep);
        const float coefficient = 1.0F - std::exp(-2.0F * static_cast<float>(kPi) * cutoff / kSampleRate);
        voice.filter_state += coefficient * (value - voice.filter_state);
        value = voice.filter_state;
      }
      float envelope = 0.0F;
      if (voice.age < channel.attack_) envelope = static_cast<float>(voice.age / channel.attack_);
      else if (voice.age < channel.attack_ + channel.decay_) {
        const float progress = static_cast<float>((voice.age - channel.attack_) / channel.decay_);
        envelope = 1.0F + (channel.sustain_ - 1.0F) * progress;
      } else envelope = channel.sustain_;
      if (voice.age > voice.release_at) {
        envelope *= std::max(0.0F, 1.0F - static_cast<float>((voice.age - voice.release_at) / channel.release_));
      }
      value *= envelope;
    }
    if (channel.drive_ > 0.001F) {
      const float gain = 1.0F + channel.drive_ * 8.0F;
      value = std::tanh(value * gain) / std::tanh(gain);
    }
    if (voice.age > voice.release_at + channel.release_ + 0.5) voice.active = false;
  }
  voice.age += 1.0 / kSampleRate;
  return value * voice.velocity;
}

void Engine::render(float* output, unsigned int frames) {
  const auto state = std::atomic_load_explicit(&published_, std::memory_order_acquire);
  if (!state) { std::fill(output, output + static_cast<std::size_t>(frames) * 2U, 0.0F); return; }
  reset_runtime_if_needed(state);
  const bool any_solo = std::any_of(state->channels.begin(), state->channels.end(), [](const Channel& c) { return c.solo_; });
  const double samples_per_step = kSampleRate * 60.0 / std::max(40.0F, state->bpm) / 4.0;
  const int total_song_steps = std::max(1, state->song.slot_count()) * state->patterns.front().step_count();
  for (unsigned int frame = 0; frame < frames; ++frame) {
    if (playing_.load()) {
      if (state->song_mode && global_step_ >= total_song_steps) {
        if (state->loop) global_step_ = 0;
        else { playing_.store(false); global_step_ = 0; }
      }
      if (playing_.load() && step_phase_ <= 0.0) { trigger_step(state, global_step_); step_phase_ += samples_per_step; }
      if (playing_.load()) { step_phase_ -= 1.0; if (step_phase_ <= 0.0) ++global_step_; }
    }
    float left = 0.0F, right = 0.0F;
    for (std::size_t index = 0; index < state->channels.size(); ++index) {
      const auto& channel = state->channels[index];
      const bool audible = !channel.mute_ && (!any_solo || channel.solo_);
      float mono = 0.0F;
      for (auto& voice : runtime_[index].voices) mono += render_voice(voice, channel);
      if (!audible) continue;
      const float left_gain = std::sqrt(0.5F * (1.0F - channel.pan_));
      const float right_gain = std::sqrt(0.5F * (1.0F + channel.pan_));
      left += mono * channel.volume_ * left_gain;
      right += mono * channel.volume_ * right_gain;
    }
    output[static_cast<std::size_t>(frame) * 2U] = std::tanh(left * 0.82F);
    output[static_cast<std::size_t>(frame) * 2U + 1U] = std::tanh(right * 0.82F);
  }
}

std::vector<float> Engine::render_offline(float seconds) {
  const auto frames = static_cast<unsigned int>(std::max(0.01F, std::min(60.0F, seconds)) * kSampleRate);
  std::vector<float> output(static_cast<std::size_t>(frames) * 2U);
  stop();
  runtime_state_revision_ = 0; runtime_transport_revision_ = transport_revision_.load();
  global_step_ = 0; step_phase_ = 0.0; playing_.store(true);
  render(output.data(), frames);
  stop();
  return output;
}

std::string Engine::version() { return CONSOLESEQ_VERSION; }

#ifdef CONSOLESEQ_WITH_AUDIO
int Engine::audio_callback(void* output, void*, unsigned int frames, double,
                           RtAudioStreamStatus, void* user_data) {
  static_cast<Engine*>(user_data)->render(static_cast<float*>(output), frames);
  return 0;
}
#endif

}  // namespace consoleseq
