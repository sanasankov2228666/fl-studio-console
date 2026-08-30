#include "console_seq.hpp"

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;
using namespace consoleseq;

PYBIND11_MODULE(console_seq_core, module) {
  module.doc() = "ConsoleSeq C++ audio engine and project model";
  module.attr("SAMPLE_RATE") = kSampleRate;
  module.attr("BUFFER_FRAMES") = kDefaultBufferFrames;
  module.attr("__version__") = Engine::version();

  py::enum_<ChannelType>(module, "ChannelType")
      .value("DRUM", ChannelType::Drum)
      .value("PIANO", ChannelType::Piano)
      .value("BASS", ChannelType::Bass)
      .value("SYNTH", ChannelType::Synth)
      .value("SOUNDFONT", ChannelType::SoundFont)
      .export_values();

  py::enum_<Oscillator>(module, "Oscillator")
      .value("SINE", Oscillator::Sine)
      .value("SQUARE", Oscillator::Square)
      .value("SAW", Oscillator::Saw)
      .value("TRIANGLE", Oscillator::Triangle)
      .export_values();

  py::class_<Pattern>(module, "Pattern")
      .def(py::init<int, int, std::string>(), py::arg("channel_count") = 5,
           py::arg("step_count") = kDefaultSteps, py::arg("name") = "Pattern 1")
      .def("set_step", &Pattern::set_step)
      .def("get_step", &Pattern::get_step)
      .def("set_note", &Pattern::set_note)
      .def("get_note", &Pattern::get_note)
      .def("set_velocity", &Pattern::set_velocity)
      .def("get_velocity", &Pattern::get_velocity)
      .def("set_duration", &Pattern::set_duration)
      .def("get_duration", &Pattern::get_duration)
      .def("clear", &Pattern::clear)
      .def("resize_steps", &Pattern::resize_steps)
      .def_property_readonly("channel_count", &Pattern::channel_count)
      .def_property_readonly("step_count", &Pattern::step_count)
      .def_property("name", &Pattern::name, &Pattern::set_name);

  py::class_<Channel>(module, "Channel")
      .def(py::init<std::string, ChannelType>(), py::arg("name") = "Channel",
           py::arg("type") = ChannelType::Synth)
      .def_property("name", &Channel::name, &Channel::set_name)
      .def_property("type", &Channel::type, &Channel::set_type)
      .def_property("volume", &Channel::volume, &Channel::set_volume)
      .def_property("pan", &Channel::pan, &Channel::set_pan)
      .def_property("mute", &Channel::muted, &Channel::set_mute)
      .def_property("solo", &Channel::soloed, &Channel::set_solo)
      .def_property("base_note", &Channel::base_note, &Channel::set_base_note)
      .def_property("oscillator", &Channel::oscillator, &Channel::set_oscillator)
      .def_property_readonly("adsr", &Channel::adsr)
      .def_property("tone", &Channel::tone, &Channel::set_tone)
      .def_property("drive", &Channel::drive, &Channel::set_drive)
      .def_property_readonly("sample_path", &Channel::sample_path)
      .def_property("builtin_id", &Channel::builtin_id, &Channel::set_builtin_id)
      .def_property_readonly("soundfont_bank", &Channel::soundfont_bank)
      .def_property_readonly("soundfont_program", &Channel::soundfont_program)
      .def("set_adsr", &Channel::set_adsr)
      .def("set_sample", &Channel::set_sample)
      .def("set_synth_param", &Channel::set_synth_param);

  py::class_<Song>(module, "Song")
      .def(py::init<int, int>(), py::arg("channel_count") = 5,
           py::arg("slots") = kDefaultSongSlots)
      .def("set_pattern_at", &Song::set_pattern_at)
      .def("get_pattern_at", &Song::get_pattern_at)
      .def("clear", &Song::clear)
      .def("resize_slots", &Song::resize_slots)
      .def_property_readonly("channel_count", &Song::channel_count)
      .def_property_readonly("slot_count", &Song::slot_count);

  py::class_<Engine>(module, "Engine")
      .def(py::init<>())
      .def("start", &Engine::start, py::call_guard<py::gil_scoped_release>())
      .def("shutdown", &Engine::shutdown, py::call_guard<py::gil_scoped_release>())
      .def("play", &Engine::play)
      .def("pause", &Engine::pause)
      .def("stop", &Engine::stop)
      .def("is_playing", &Engine::is_playing)
      .def("audio_available", &Engine::audio_available)
      .def("audio_status", &Engine::audio_status)
      .def("new_project", &Engine::new_project)
      .def("save_project", &Engine::save_project)
      .def("load_project", &Engine::load_project)
      .def("last_error", &Engine::last_error)
      .def("bpm", &Engine::bpm)
      .def("set_bpm", &Engine::set_bpm)
      .def("loop", &Engine::loop)
      .def("set_loop", &Engine::set_loop)
      .def("song_mode", &Engine::song_mode)
      .def("set_song_mode", &Engine::set_song_mode)
      .def("current_pattern", &Engine::current_pattern)
      .def("set_current_pattern", &Engine::set_current_pattern)
      .def("current_step", &Engine::current_step)
      .def("current_song_slot", &Engine::current_song_slot)
      .def("channel_count", &Engine::channel_count)
      .def("pattern_count", &Engine::pattern_count)
      .def("step_count", &Engine::step_count)
      .def("song_slot_count", &Engine::song_slot_count)
      .def("set_step_count", &Engine::set_step_count)
      .def("set_song_slot_count", &Engine::set_song_slot_count)
      .def("get_channel", &Engine::get_channel)
      .def("get_pattern", &Engine::get_pattern)
      .def("get_song", &Engine::get_song)
      .def("get_step", &Engine::get_step)
      .def("set_step", &Engine::set_step)
      .def("get_note", &Engine::get_note)
      .def("set_note", &Engine::set_note)
      .def("get_velocity", &Engine::get_velocity)
      .def("set_velocity", &Engine::set_velocity)
      .def("get_duration", &Engine::get_duration)
      .def("set_duration", &Engine::set_duration)
      .def("clear_pattern", &Engine::clear_pattern)
      .def("add_pattern", &Engine::add_pattern, py::arg("name") = "")
      .def("add_pattern_bank", &Engine::add_pattern_bank, py::arg("count") = 16)
      .def("duplicate_pattern", &Engine::duplicate_pattern)
      .def("remove_pattern", &Engine::remove_pattern)
      .def("set_pattern_name", &Engine::set_pattern_name)
      .def("set_pattern_at", &Engine::set_pattern_at)
      .def("get_pattern_at", &Engine::get_pattern_at)
      .def("add_channel", &Engine::add_channel, py::arg("preset_id"), py::arg("name") = "")
      .def("duplicate_channel", &Engine::duplicate_channel)
      .def("remove_channel", &Engine::remove_channel)
      .def("set_channel_preset", &Engine::set_channel_preset)
      .def("set_channel_name", &Engine::set_channel_name)
      .def("set_channel_volume", &Engine::set_channel_volume)
      .def("set_channel_pan", &Engine::set_channel_pan)
      .def("set_channel_mute", &Engine::set_channel_mute)
      .def("set_channel_solo", &Engine::set_channel_solo)
      .def("set_channel_base_note", &Engine::set_channel_base_note)
      .def("set_channel_sample", &Engine::set_channel_sample)
      .def("set_asset_root", &Engine::set_asset_root)
      .def("set_soundfont", &Engine::set_soundfont)
      .def("soundfont_available", &Engine::soundfont_available)
      .def("soundfont_status", &Engine::soundfont_status)
      .def("set_synth_param", &Engine::set_synth_param)
      .def("render_offline", &Engine::render_offline)
      .def_static("version", &Engine::version)
      .def_static("preset_ids", &Engine::preset_ids)
      .def_static("preset_catalog", &Engine::preset_catalog);
}
