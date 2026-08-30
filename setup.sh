#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$ROOT_DIR/build-unix"
VENV_DIR="$ROOT_DIR/.venv-unix"

install_linux_packages() {
  local missing=()
  command -v cmake >/dev/null 2>&1 || missing+=(cmake)
  command -v g++ >/dev/null 2>&1 || missing+=(g++)
  command -v python3 >/dev/null 2>&1 || missing+=(python3 python3-venv python3-dev)
  if command -v python3 >/dev/null 2>&1; then
    local python_include
    python_include="$(python3 -c 'import sysconfig; print(sysconfig.get_paths()["include"])')"
    [[ -f "$python_include/Python.h" ]] || missing+=(python3-dev)
  fi
  if ! command -v pkg-config >/dev/null 2>&1; then
    missing+=(pkg-config libasound2-dev)
  elif ! pkg-config --exists alsa 2>/dev/null; then
    missing+=(libasound2-dev)
  fi
  if ! command -v pkg-config >/dev/null 2>&1 || ! pkg-config --exists fluidsynth 2>/dev/null; then
    missing+=(libfluidsynth-dev)
  fi
  if ((${#missing[@]})); then
    echo "Installing required system packages: ${missing[*]}"
    if command -v sudo >/dev/null 2>&1; then
      sudo apt-get update
      sudo apt-get install -y build-essential python3 python3-venv python3-dev \
        cmake pkg-config libasound2-dev libpulse-dev
      sudo apt-get install -y libfluidsynth-dev
    else
      apt-get update
      apt-get install -y build-essential python3 python3-venv python3-dev \
        cmake pkg-config libasound2-dev libpulse-dev
      apt-get install -y libfluidsynth-dev
    fi
  fi
}

install_macos_packages() {
  if ! command -v brew >/dev/null 2>&1; then
    echo "Homebrew is required to auto-install CMake and Python on macOS." >&2
    echo "Install it from https://brew.sh and run setup.sh again." >&2
    exit 1
  fi
  local packages=()
  command -v cmake >/dev/null 2>&1 || packages+=(cmake)
  command -v python3 >/dev/null 2>&1 || packages+=(python)
  command -v fluidsynth >/dev/null 2>&1 || packages+=(fluid-synth)
  command -v clang++ >/dev/null 2>&1 || xcode-select --install || true
  if ((${#packages[@]})); then brew install "${packages[@]}"; fi
}

case "$(uname -s)" in
  Linux*) install_linux_packages ;;
  Darwin*) install_macos_packages ;;
  *) echo "Use setup.ps1 on Windows." >&2; exit 1 ;;
esac

soundfont_dir="$ROOT_DIR/assets/soundfonts"
soundfont_file="$soundfont_dir/GeneralUser-GS.sf2"
soundfont_license="$soundfont_dir/GeneralUser-GS-LICENSE.txt"
mkdir -p "$soundfont_dir"
if [[ ! -f "$soundfont_file" ]] || [[ "$(wc -c < "$soundfont_file")" -lt 20000000 ]]; then
  echo "Downloading GeneralUser GS SoundFont..."
  curl -fL --retry 3 -o "$soundfont_file" \
    https://raw.githubusercontent.com/mrbumpy409/GeneralUser-GS/main/GeneralUser-GS.sf2
fi
if [[ ! -f "$soundfont_license" ]]; then
  curl -fL --retry 3 -o "$soundfont_license" \
    https://raw.githubusercontent.com/mrbumpy409/GeneralUser-GS/main/documentation/LICENSE.txt
fi

python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install -r "$ROOT_DIR/requirements.txt"

cmake -S "$ROOT_DIR" -B "$BUILD_DIR" \
  -DCMAKE_BUILD_TYPE=Release \
  -DPython_EXECUTABLE="$VENV_DIR/bin/python"
cmake --build "$BUILD_DIR" --config Release --parallel

native_module="$(find "$BUILD_DIR/python" -maxdepth 2 -type f \
  \( -name 'console_seq_core*.so' -o -name 'console_seq_core*.dylib' \) -print -quit)"
if [[ -z "$native_module" ]]; then
  echo "The built Python module was not found." >&2
  exit 1
fi
cp "$native_module" "$ROOT_DIR/console_seq/"

ctest --test-dir "$BUILD_DIR" -C Release --output-on-failure
"$VENV_DIR/bin/python" "$ROOT_DIR/main.py" --smoke-test \
  --smoke-output "$BUILD_DIR/setup_smoke.cseq"
"$VENV_DIR/bin/python" -m unittest discover -s "$ROOT_DIR/tests" -p 'test_python.py' -v

echo
echo "ConsoleSeq is ready. Run:"
echo "  $VENV_DIR/bin/python $ROOT_DIR/main.py"
