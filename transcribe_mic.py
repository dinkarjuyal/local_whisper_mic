#!/usr/bin/env python3
"""
Local mic -> text using faster-whisper (OpenAI Whisper weights).

Near real-time: transcribes fixed-length windows as you speak (not true
word-by-word streaming; lower --chunk-seconds for snappier updates).

macOS Shortcut (recommended):
  1. Install deps (see below).
  2. Shortcuts app → New Shortcut → Add Action "Run Shell Script"
     Shell: /bin/zsh
     Pass input: as arguments
     Script (set REPO to this folder’s absolute path):
       REPO="$HOME/src/local-whisper-mic"
       source "$REPO/.venv/bin/activate" && python "$REPO/transcribe_mic.py"
  3. Shortcut name e.g. "Dictate local"
  4. System Settings → Keyboard → Keyboard Shortcuts → Services (or App Shortcuts)
     and assign a key to the shortcut if offered; or add shortcut to menu bar.

First run downloads the model (~hundreds MB for "small"). Grant Terminal (or
your runner) Microphone when macOS prompts.

Prereq on macOS for sounddevice:
  brew install portaudio
  python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
"""

from __future__ import annotations

import argparse
import queue
import sys
import time
from typing import List

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Local mic speech-to-text (Whisper)")
    p.add_argument(
        "--model",
        default="small",
        help="Whisper model id (tiny, base, small, medium, large-v3, ...)",
    )
    p.add_argument(
        "--device",
        default="cpu",
        choices=("cpu", "cuda"),
        help="Inference device (use cpu on Apple Silicon unless you use CUDA builds)",
    )
    p.add_argument(
        "--compute-type",
        default="int8",
        help="e.g. int8 (cpu), float16 (cuda)",
    )
    p.add_argument(
        "--chunk-seconds",
        type=float,
        default=2.5,
        help="Audio window per transcription (smaller = faster updates, rougher)",
    )
    p.add_argument(
        "--language",
        default=None,
        help="Force language code (e.g. en). Default: auto",
    )
    p.add_argument(
        "--list-devices",
        action="store_true",
        help="Print audio devices and exit",
    )
    p.add_argument(
        "--input-device",
        type=int,
        default=None,
        help="sounddevice input device index (see --list-devices)",
    )
    p.add_argument(
        "--min-rms",
        type=float,
        default=0.002,
        help="Skip chunks quieter than this RMS (reduce junk prints)",
    )
    return p.parse_args()


def list_devices() -> None:
    print(sd.query_devices())


def main() -> None:
    args = parse_args()
    if args.list_devices:
        list_devices()
        return

    infer_device = args.device

    print("Loading model (first time may download weights)...", file=sys.stderr)
    model = WhisperModel(
        args.model,
        device=infer_device,
        compute_type=args.compute_type,
    )

    chunk_samples = max(int(SAMPLE_RATE * args.chunk_seconds), int(SAMPLE_RATE * 0.5))
    block = int(SAMPLE_RATE * 0.1)

    raw_q: queue.Queue[np.ndarray] = queue.Queue(maxsize=200)
    buf: List[np.ndarray] = []
    acc = 0

    def callback(indata, frames, t, status) -> None:  # type: ignore[no-untyped-def]
        if status:
            print(status, file=sys.stderr)
        try:
            raw_q.put(indata[:, 0].astype(np.float32).copy(), block=False)
        except queue.Full:
            pass

    print(
        f"Listening at {SAMPLE_RATE} Hz, chunks ~{args.chunk_seconds}s. Ctrl+C to stop.\n",
        file=sys.stderr,
    )

    try:
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            blocksize=block,
            callback=callback,
            device=args.input_device,
        ):
            while True:
                try:
                    block_audio = raw_q.get(timeout=0.2)
                except queue.Empty:
                    continue
                buf.append(block_audio)
                acc += len(block_audio)
                while acc >= chunk_samples:
                    chunk = np.concatenate(buf, axis=0)
                    if len(chunk) > chunk_samples:
                        carry = chunk[chunk_samples:]
                        chunk = chunk[:chunk_samples]
                        buf = [carry]
                        acc = len(carry)
                    else:
                        buf = []
                        acc = 0

                    rms = float(np.sqrt(np.mean(chunk**2)))
                    if rms < args.min_rms:
                        continue

                    segments, _ = model.transcribe(
                        chunk,
                        language=args.language,
                        vad_filter=True,
                        beam_size=5,
                    )
                    parts = [s.text.strip() for s in segments]
                    line = " ".join(p for p in parts if p).strip()
                    if line:
                        print(line, flush=True)
    except KeyboardInterrupt:
        print("\nStopped.", file=sys.stderr)


if __name__ == "__main__":
    main()
