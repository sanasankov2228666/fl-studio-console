cmake_minimum_required(VERSION 3.18)

project(ConsoleSeq VERSION 1.2.0 LANGUAGES CXX)

option(CONSOLESEQ_WITH_AUDIO "Build RtAudio real-time output" ON)
option(CONSOLESEQ_WITH_SNDFILE "Build libsndfile sample loading" ON)
option(CONSOLESEQ_BUILD_TESTS "Build the native test executable" ON)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set(BUILD_SHARED_LIBS OFF CACHE BOOL "Build dependencies as static libraries" FORCE)

include(FetchContent)

set(PYBIND11_FINDPYTHON ON)
FetchContent_Declare(
  pybind11
  URL https://github.com/pybind/pybind11/archive/refs/tags/v2.13.6.tar.gz
  DOWNLOAD_EXTRACT_TIMESTAMP TRUE
)
FetchContent_Declare(
  nlohmann_json
  URL https://github.com/nlohmann/json/archive/refs/tags/v3.11.3.tar.gz
  DOWNLOAD_EXTRACT_TIMESTAMP TRUE
)
FetchContent_MakeAvailable(pybind11 nlohmann_json)

FetchContent_Declare(
  dr_libs
  URL https://github.com/mackron/dr_libs/archive/refs/tags/mp3-0.7.3.tar.gz
  DOWNLOAD_EXTRACT_TIMESTAMP TRUE
)
FetchContent_MakeAvailable(dr_libs)

if(CONSOLESEQ_WITH_AUDIO)
  set(RTAUDIO_BUILD_TESTING OFF CACHE BOOL "" FORCE)
  set(RTAUDIO_BUILD_STATIC_LIBS ON CACHE BOOL "" FORCE)
  set(RTAUDIO_BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)
  FetchContent_Declare(
    rtaudio
    URL https://github.com/thestk/rtaudio/archive/refs/tags/6.0.1.tar.gz
    DOWNLOAD_EXTRACT_TIMESTAMP TRUE
  )
  FetchContent_MakeAvailable(rtaudio)
endif()

if(CONSOLESEQ_WITH_SNDFILE)
  set(BUILD_PROGRAMS OFF CACHE BOOL "" FORCE)
  set(BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
  set(BUILD_REGTEST OFF CACHE BOOL "" FORCE)
  set(BUILD_TESTING OFF CACHE BOOL "" FORCE)
  set(ENABLE_EXTERNAL_LIBS OFF CACHE BOOL "" FORCE)
  set(ENABLE_MPEG OFF CACHE BOOL "" FORCE)
  set(ENABLE_CPACK OFF CACHE BOOL "" FORCE)
  FetchContent_Declare(
    libsndfile
    URL https://github.com/libsndfile/libsndfile/archive/refs/tags/1.2.2.tar.gz
    DOWNLOAD_EXTRACT_TIMESTAMP TRUE
  )
  FetchContent_MakeAvailable(libsndfile)
endif()

add_library(console_seq_engine STATIC
  src/console_seq.cpp
  src/instrument_presets.cpp
)
target_include_directories(console_seq_engine PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/src)
target_include_directories(console_seq_engine PRIVATE ${dr_libs_SOURCE_DIR})
target_link_libraries(console_seq_engine PUBLIC nlohmann_json::nlohmann_json)
target_compile_definitions(console_seq_engine PUBLIC CONSOLESEQ_VERSION="${PROJECT_VERSION}")

if(CONSOLESEQ_WITH_AUDIO)
  target_compile_definitions(console_seq_engine PUBLIC CONSOLESEQ_WITH_AUDIO=1)
  target_link_libraries(console_seq_engine PUBLIC rtaudio)
endif()

if(CONSOLESEQ_WITH_SNDFILE)
  target_compile_definitions(console_seq_engine PUBLIC CONSOLESEQ_WITH_SNDFILE=1)
  if(TARGET SndFile::sndfile)
    target_link_libraries(console_seq_engine PUBLIC SndFile::sndfile)
  elseif(TARGET sndfile)
    target_link_libraries(console_seq_engine PUBLIC sndfile)
  endif()
endif()

if(MSVC)
  target_compile_options(console_seq_engine PRIVATE /W4 /permissive-)
else()
  target_compile_options(console_seq_engine PRIVATE -Wall -Wextra -Wpedantic)
endif()

pybind11_add_module(console_seq_core MODULE src/bindings.cpp)
target_link_libraries(console_seq_core PRIVATE console_seq_engine)
set_target_properties(console_seq_core PROPERTIES
  LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/python
  RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/python
)

if(CONSOLESEQ_BUILD_TESTS)
  enable_testing()
  add_executable(console_seq_native_tests tests/native_tests.cpp)
  target_link_libraries(console_seq_native_tests PRIVATE console_seq_engine)
  add_test(NAME console_seq_native_tests COMMAND console_seq_native_tests)
endif()
