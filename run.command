#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
if [[ -f .venv/bin/activate ]]; then
  # shellcheck source=/dev/null
  source .venv/bin/activate
  exec python3 transcribe_mic.py "$@"
fi
if command -v transcribe-mic >/dev/null 2>&1; then
  exec transcribe-mic "$@"
fi
echo "Create a venv or install the package:" >&2
echo "  python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt" >&2
echo "  pip install /path/to/local-whisper-mic" >&2
exit 1
