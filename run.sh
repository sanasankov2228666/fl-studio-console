#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -x "$ROOT_DIR/.venv-unix/bin/python" ]]; then
  echo "ConsoleSeq is not built. Run ./setup.sh first." >&2
  exit 1
fi
if ! "$ROOT_DIR/.venv-unix/bin/python" -c 'import sys' >/dev/null 2>&1; then
  echo "ConsoleSeq's Unix environment is broken. Run ./setup.sh to repair it." >&2
  exit 1
fi
exec "$ROOT_DIR/.venv-unix/bin/python" "$ROOT_DIR/main.py" "$@"
