# local-whisper-mic

Local **speech-to-text** from your microphone using [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (OpenAI Whisper weights). Text is printed in **chunk** windows (default ~2.5s), not sub-word streaming.

Works on **macOS** and **Linux** (Windows: install PortAudio + Python deps manually).

## Quick start

**Option A — virtualenv in the repo**

```bash
# macOS
brew install portaudio
# Debian/Ubuntu
# sudo apt install portaudio19-dev python3-venv

git clone <repository-url>
cd local-whisper-mic
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python transcribe_mic.py --list-devices
python transcribe_mic.py
```

**Option B — install on PATH (any clone location)**

```bash
pip install /path/to/local-whisper-mic
# or from repo root:
pip install .
transcribe-mic --list-devices
transcribe-mic
```

Double-click **`run.command`** (macOS) or run **`./run.sh`** after `chmod +x run.sh`.

## Configuration

Precedence: **built-in defaults → JSON files → `--config` file → environment variables → CLI flags.**

### JSON files (optional)

1. `~/.config/local-whisper-mic/config.json` — per-user defaults  
2. `local-whisper-mic.config.json` next to `transcribe_mic.py` — per-clone defaults  
3. **`--config /path/to.json`** — extra layer (team or machine-specific)

Copy [`config.example.json`](config.example.json) to one of the paths above and edit. Use `null` for `language` or `input_device` when you want auto defaults.

### Environment variables

| Variable | Maps to |
|----------|---------|
| `LOCAL_WHISPER_MIC_MODEL` | `--model` |
| `LOCAL_WHISPER_MIC_DEVICE` | `--device` (`cpu` or `cuda`) |
| `LOCAL_WHISPER_MIC_COMPUTE_TYPE` | `--compute-type` |
| `LOCAL_WHISPER_MIC_CHUNK_SECONDS` | `--chunk-seconds` |
| `LOCAL_WHISPER_MIC_LANGUAGE` | `--language` (empty = auto) |
| `LOCAL_WHISPER_MIC_INPUT_DEVICE` | `--input-device` (integer index) |
| `LOCAL_WHISPER_MIC_MIN_RMS` | `--min-rms` |

Inspect merged file + env defaults (before other CLI overrides):

```bash
transcribe-mic --print-config
LOCAL_WHISPER_MIC_MODEL=tiny transcribe-mic --print-config
```

## CLI highlights

| Flag | Purpose |
|------|---------|
| `--list-devices` | Show input/output device indices |
| `--input-device N` | Choose a specific microphone |
| `--model tiny` | Fastest / smallest download |
| `--chunk-seconds 1.5` | Shorter windows = snappier, noisier |

Stop with **Ctrl+C**. Grant **microphone** permission to Terminal, your IDE, or Shortcuts when prompted.

## macOS Shortcuts

Use absolute paths so the shortcut does not depend on your current directory:

```bash
PYTHON="$HOME/path/to/local-whisper-mic/.venv/bin/python"
SCRIPT="$HOME/path/to/local-whisper-mic/transcribe_mic.py"
"$PYTHON" "$SCRIPT"
```

After `pip install`, you can instead run `transcribe-mic` if its directory is on `PATH` inside the shortcut environment.

## Publish to GitHub

```bash
gh auth login
gh repo create local-whisper-mic --public --source=. --remote=origin --push
```

Empty repo on GitHub:

```bash
git remote add origin https://github.com/<you>/local-whisper-mic.git
git push -u origin main
```

## License

MIT — see [LICENSE](LICENSE).
