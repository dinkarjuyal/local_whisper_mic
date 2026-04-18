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

Stop with **Ctrl+C**. Grant **Microphone** to the app that runs the script (Terminal, **Shortcuts**, or the **Automator**/`bash` helper shown in the privacy prompt).

## Keyboard shortcut

Use **absolute paths** in every method below so it works no matter which app is focused.

Pick your Python entrypoint once and paste it into the script (examples use a venv; adjust if you use `pip install` + `transcribe-mic` on `PATH`):

```bash
PYTHON="$HOME/path/to/local-whisper-mic/.venv/bin/python"
SCRIPT="$HOME/path/to/local-whisper-mic/transcribe_mic.py"
"$PYTHON" "$SCRIPT"
```

If `transcribe-mic` is on `PATH` inside the runner’s environment:

```bash
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
transcribe-mic
```

### macOS — Shortcuts (menu bar / Siri, not always a global key)

1. Open **Shortcuts** → **+** → add **Run Shell Script**.
2. Shell **/bin/zsh**, pass input **to stdin** or **as arguments** (either is fine if the script body is only the lines above).
3. Paste the three-line `PYTHON` / `SCRIPT` block (or the `transcribe-mic` block).
4. Name the shortcut (e.g. **Local dictation**).
5. Shortcut **…** or **ⓘ** → enable **Pin in Menu Bar** (or **Show in Share Sheet** if you prefer). Run it from the menu bar when you need dictation.

Stock macOS does **not** assign an arbitrary global hotkey to every Shortcut reliably; for a **system-wide keyboard shortcut**, use Automator below or a launcher (Raycast, Alfred) with a hotkey.

### macOS — Automator Quick Action + real keyboard shortcut (recommended for a hotkey)

1. Open **Automator** → **New** → **Quick Action**.
2. **Workflow receives** → **no input**; **in** → **any application**.
3. Add **Run Shell Script**; shell **/bin/zsh**; pass input **as arguments**.
4. Paste the same command block (`PYTHON`/`SCRIPT` or `transcribe-mic`).
5. **File → Save** (e.g. **Local Whisper dictation**).
6. Open **System Settings → Keyboard → Keyboard Shortcuts → Services** (or **Shortcuts** / **Quick Actions**, depending on macOS version).
7. Find your Quick Action (often under **General** or **Text**), click the **none** column, and press your desired key combination (e.g. **⌃⌥D**).

The first run may prompt for **Microphone** for the small helper that runs your shell script.

### macOS — open a Terminal tab instead (good for scrolling transcript)

Use **Run AppleScript** in Shortcuts or Automator:

```applescript
tell application "Terminal"
    do script "cd /path/to/local-whisper-mic && source .venv/bin/activate && python3 transcribe_mic.py"
end tell
```

Assign a shortcut the same way (Automator Quick Action, or Shortcuts pinned to menu bar). Stop dictation with **Ctrl+C** in that tab.

### Linux (GNOME example)

**Settings → Keyboard → Keyboard Shortcuts → Custom Shortcuts** → add a command such as:

```bash
/home/you/path/to/local-whisper-mic/.venv/bin/python /home/you/path/to/local-whisper-mic/transcribe_mic.py
```

Bind a key; allow the terminal or wrapper app microphone access if prompted.

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
