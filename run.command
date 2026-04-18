#!/bin/bash
cd "$(dirname "$0")"
if [[ ! -f .venv/bin/activate ]]; then
  echo "Create venv first: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt" >&2
  exit 1
fi
source .venv/bin/activate
exec python transcribe_mic.py "$@"
