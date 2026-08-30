#pragma once

#include <array>
#include <atomic>
#include <cstdint>
#include <memory>
#include <mutex>
#include <string>
#include <thread>
#include <vector>

#ifdef CONSOLESEQ_WITH_AUDIO
#include <RtAudio.h>
#endif

namespace consoleseq {

constexpr unsigned int kSampleRate = 44100;
constexpr unsigned int kDefaultBufferFrames = 512;
constexpr int kDefaultSteps = 16;
constexpr int kDefaultSongSlots = 16;

enum class ChannelType { Drum, Piano, Bass, Synth };
enum class Oscillator { Sine, Square, Saw };

struct Step {
  bool active{false};
  int note{60};
  float velocity{1.0F};
};

class Pattern {
 public:
  Pattern(int channel_count = 5, int step_count = kDefaultSteps,
          std::string name = "Pattern 1");

  void set_step(int channel, int step, bool value);
  bool get_step(int channel, int step) const;
  void set_note(int channel, int step, int midi_note);
  int get_note(int channel, int step) const;
  void set_velocity(int channel, int step, float velocity);
  float get_velocity(int channel, int step) const;
  void clear();
  void resize_channels(int count);
  void resize_steps(int count);
  int channel_count() const;
  int step_count() const;
  const std::string& name() const;
  void set_name(const std::string& name);
  const Step& at(int channel, int step) const;

 private:
  void check_index(int channel, int step) const;
  std::string name_;
  int steps_;
  std::vector<std::vector<Step>> grid_;

  friend class Engine;
};

class Channel {
 public:
  Channel(std::string name = "Channel", ChannelType type = ChannelType::Synth);

  const std::string& name() const;
  void set_name(const std::string& value);
  ChannelType type() const;
  void set_type(ChannelType value);
  float volume() const;
  void set_volume(float value);
  float pan() const;
  void set_pan(float value);
  bool muted() const;
  void set_mute(bool value);
  bool soloed() const;
  void set_solo(bool value);
  int base_note() const;
  void set_base_note(int value);
  Oscillator oscillator() const;
  void set_oscillator(Oscillator value);
  void set_adsr(float attack, float decay, float sustain, float release);
  std::array<float, 4> adsr() const;
  float tone() const;
  void set_tone(float value);
  float drive() const;
  void set_drive(float value);
  const std::string& sample_path() const;
  const std::string& builtin_id() const;
  bool set_sample(const std::string& filename);
  void set_builtin_id(const std::string& value);
  void set_synth_param(const std::string& parameter, float value);

 private:
  std::string name_;
  ChannelType type_;
  float volume_{0.8F};
  float pan_{0.0F};
  bool mute_{false};
  bool solo_{false};
  int base_note_{60};
  Oscillator oscillator_{Oscillator::Sine};
  float attack_{0.005F};
  float decay_{0.18F};
  float sustain_{0.25F};
  float release_{0.15F};
  float tone_{0.75F};
  float drive_{0.0F};
  std::string sample_path_;
  std::string builtin_id_;
  std::shared_ptr<const std::vector<float>> sample_;

  friend class Engine;
};

class Song {
 public:
  Song(int channel_count = 5, int slots = kDefaultSongSlots);
  void set_pattern_at(int channel, int slot, int pattern_id);
  int get_pattern_at(int channel, int slot) const;
  void clear();
  void resize_channels(int count);
  int channel_count() const;
  int slot_count() const;

 private:
  void check_index(int channel, int slot) const;
  std::vector<std::vector<int>> arrangement_;

  friend class Engine;
};

struct ProjectState {
  float bpm{120.0F};
  bool loop{true};
  bool song_mode{false};
  int current_pattern{0};
  std::vector<Channel> channels;
  std::vector<Pattern> patterns;
  Song song;
  std::uint64_t revision{0};
};

class Engine {
 public:
  Engine();
  ~Engine();
  Engine(const Engine&) = delete;
  Engine& operator=(const Engine&) = delete;

  bool start();
  void shutdown();
  void play();
  void pause();
  void stop();
  bool is_playing() const;
  bool audio_available() const;
  const std::string& audio_status() const;

  void new_project();
  bool save_project(const std::string& filename) const;
  bool load_project(const std::string& filename);
  std::string last_error() const;

  float bpm() const;
  void set_bpm(float value);
  bool loop() const;
  void set_loop(bool value);
  bool song_mode() const;
  void set_song_mode(bool value);
  int current_pattern() const;
  void set_current_pattern(int value);
  int current_step() const;
  int current_song_slot() const;

  int channel_count() const;
  int pattern_count() const;
  int step_count() const;
  int song_slot_count() const;
  void set_step_count(int count);
  Channel get_channel(int index) const;
  Pattern get_pattern(int index) const;
  Song get_song() const;

  bool get_step(int pattern, int channel, int step) const;
  void set_step(int pattern, int channel, int step, bool value);
  int get_note(int pattern, int channel, int step) const;
  void set_note(int pattern, int channel, int step, int note);
  float get_velocity(int pattern, int channel, int step) const;
  void set_velocity(int pattern, int channel, int step, float velocity);
  void clear_pattern(int pattern);
  int add_pattern(const std::string& name = "");
  int duplicate_pattern(int pattern);
  void remove_pattern(int pattern);
  void set_pattern_name(int pattern, const std::string& name);

  void set_pattern_at(int channel, int slot, int pattern_id);
  int get_pattern_at(int channel, int slot) const;
  int add_channel(const std::string& preset_id, const std::string& name = "");
  int duplicate_channel(int channel);
  void remove_channel(int channel);
  void set_channel_preset(int channel, const std::string& preset_id);
  void set_channel_name(int channel, const std::string& name);
  void set_channel_volume(int channel, float value);
  void set_channel_pan(int channel, float value);
  void set_channel_mute(int channel, bool value);
  void set_channel_solo(int channel, bool value);
  void set_channel_base_note(int channel, int value);
  bool set_channel_sample(int channel, const std::string& filename);
  void set_synth_param(int channel, const std::string& parameter, float value);

  std::vector<float> render_offline(float seconds);
  static std::string version();
  static std::vector<std::string> preset_ids();

 private:
  struct Voice {
    bool active{false};
    std::shared_ptr<const std::vector<float>> sample;
    std::size_t sample_position{0};
    double phase{0.0};
    double age{0.0};
    double release_at{0.0};
    float velocity{1.0F};
    int note{60};
    float filter_state{0.0F};
  };
  struct RuntimeChannel { std::array<Voice, 8> voices{}; };

  void publish_locked();
  static Channel make_preset_channel(const std::string& preset_id);
  static std::shared_ptr<const std::vector<float>> generate_builtin(const std::string& id);
  static std::shared_ptr<const std::vector<float>> load_audio_file(const std::string& filename);
  static double midi_frequency(int note);
  void render(float* output, unsigned int frames);
  void reset_runtime_if_needed(const std::shared_ptr<const ProjectState>& state);
  void trigger_step(const std::shared_ptr<const ProjectState>& state, int global_step);
  void trigger_voice(RuntimeChannel& runtime, const Channel& channel, const Step& step);
  float render_voice(Voice& voice, const Channel& channel);
  void silent_loop();

#ifdef CONSOLESEQ_WITH_AUDIO
  static int audio_callback(void* output, void* input, unsigned int frames,
                            double stream_time, RtAudioStreamStatus status,
                            void* user_data);
  std::unique_ptr<RtAudio> audio_;
#endif

  mutable std::mutex state_mutex_;
  ProjectState editable_;
  std::shared_ptr<const ProjectState> published_;
  std::atomic<bool> playing_{false};
  std::atomic<bool> paused_{false};
  std::atomic<bool> running_{false};
  std::atomic<bool> audio_available_{false};
  std::atomic<int> current_step_atomic_{0};
  std::atomic<int> current_song_slot_atomic_{0};
  std::atomic<std::uint64_t> transport_revision_{0};
  std::thread silent_thread_;
  std::vector<RuntimeChannel> runtime_;
  std::uint64_t runtime_state_revision_{0};
  std::uint64_t runtime_transport_revision_{0};
  double step_phase_{0.0};
  int global_step_{0};
  mutable std::string last_error_;
  std::string audio_status_{"not started"};
};

}  // namespace consoleseq
