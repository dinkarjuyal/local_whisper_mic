# local-whisper-mic

Local **speech-to-text** from your Mac microphone using [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (OpenAI Whisper weights). Prints transcribed text in **chunk** windows (default ~2.5s), not sub-word streaming.

## Requirements

- macOS (tested with CoreAudio / built-in mic)
- Python 3.11+ recommended
- [Homebrew](https://brew.sh/) `portaudio` for `sounddevice`

## Setup

```bash
brew install portaudio
git clone <repository-url>
cd local-whisper-mic
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

First run downloads Whisper weights (size depends on `--model`).

## Usage

```bash
source .venv/bin/activate
python transcribe_mic.py --list-devices
python transcribe_mic.py --model small
```

Options: `--chunk-seconds`, `--input-device`, `--language en`, `--model tiny` (fastest). Stop with **Ctrl+C**.

Double-click **`run.command`** in Finder to open Terminal in this directory and start listening (after venv exists).

## macOS Shortcut

Shortcuts → **Run Shell Script** (shell `/bin/zsh`), set `REPO` to the clone path:

```bash
REPO="$HOME/src/local-whisper-mic"
source "$REPO/.venv/bin/activate" && python "$REPO/transcribe_mic.py"
```

Grant **Microphone** to Terminal or Shortcuts when prompted. For live scrolling output, run from Terminal; Shortcuts may only surface output when the shortcut finishes.

## License

MIT — see [LICENSE](LICENSE).
