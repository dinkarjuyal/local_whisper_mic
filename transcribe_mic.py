#!/usr/bin/env python3
"""
Local mic -> text using faster-whisper (OpenAI Whisper weights).

Near real-time: transcribes fixed-length windows as you speak (not true
word-by-word streaming; lower chunk-seconds for snappier updates).

Configuration precedence: built-in defaults < JSON config files <
optional --config file < environment variables < CLI flags.
See README.md for paths and env var names.

macOS / Linux: install deps, then run from any directory:

  python /path/to/transcribe_mic.py
  # or after pip install:
  transcribe-mic

macOS Shortcut example (repo-agnostic if you use absolute path to script):

  /path/to/.venv/bin/python /path/to/transcribe_mic.py
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import sys
import time
from pathlib import Path
from typing import Any, List, Mapping, MutableMapping

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000

SCRIPT_DIR = Path(__file__).resolve().parent
GLOBAL_CONFIG = Path.home() / ".config" / "local-whisper-mic" / "config.json"
REPO_CONFIG = SCRIPT_DIR / "local-whisper-mic.config.json"

_ENV_KEYS: dict[str, str] = {
    "model": "LOCAL_WHISPER_MIC_MODEL",
    "device": "LOCAL_WHISPER_MIC_DEVICE",
    "compute_type": "LOCAL_WHISPER_MIC_COMPUTE_TYPE",
    "chunk_seconds": "LOCAL_WHISPER_MIC_CHUNK_SECONDS",
    "language": "LOCAL_WHISPER_MIC_LANGUAGE",
    "input_device": "LOCAL_WHISPER_MIC_INPUT_DEVICE",
    "min_rms": "LOCAL_WHISPER_MIC_MIN_RMS",
}
KNOWN_KEYS = frozenset(_ENV_KEYS.keys())


def _merge_file(cfg: MutableMapping[str, Any], data: Mapping[str, Any]) -> None:
    for k, v in data.items():
        if k in KNOWN_KEYS:
            cfg[k] = v


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error reading config {path}: {e}", file=sys.stderr)
        raise SystemExit(2) from e
    if not isinstance(data, dict):
        print(f"Config must be a JSON object: {path}", file=sys.stderr)
        raise SystemExit(2)
    return data


def _coerce_env(key: str, raw: str) -> Any:
    if key in ("chunk_seconds", "min_rms"):
        return float(raw)
    if key == "input_device":
        return int(raw)
    if key == "language" and raw.strip() == "":
        return None
    return raw


def _apply_env(cfg: MutableMapping[str, Any]) -> None:
    for key, env_name in _ENV_KEYS.items():
        raw = os.environ.get(env_name)
        if raw is None or raw.strip() == "":
            continue
        try:
            cfg[key] = _coerce_env(key, raw)
        except ValueError as e:
            print(f"Invalid value for {env_name}={raw!r}: {e}", file=sys.stderr)
            raise SystemExit(2) from e


def _normalize_cfg(cfg: MutableMapping[str, Any]) -> None:
    for k in ("chunk_seconds", "min_rms"):
        if k in cfg and cfg[k] is not None:
            cfg[k] = float(cfg[k])
    if cfg.get("input_device") is not None:
        cfg["input_device"] = int(cfg["input_device"])
    if cfg.get("language") == "":
        cfg["language"] = None


def build_config_defaults(explicit_config: Path | None) -> dict[str, Any]:
    """Merge file-based config then environment (CLI not applied here)."""
    cfg: dict[str, Any] = {
        "model": "small",
        "device": "cpu",
        "compute_type": "int8",
        "chunk_seconds": 2.5,
        "language": None,
        "input_device": None,
        "min_rms": 0.002,
    }
    for path in (GLOBAL_CONFIG, REPO_CONFIG):
        if path.is_file():
            _merge_file(cfg, _load_json(path))
    if explicit_config is not None:
        if not explicit_config.is_file():
            print(f"Config file not found: {explicit_config}", file=sys.stderr)
            raise SystemExit(2)
        _merge_file(cfg, _load_json(explicit_config))
    _apply_env(cfg)
    _normalize_cfg(cfg)
    return cfg


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    argv = list(sys.argv[1:] if argv is None else argv)
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--config", type=Path, default=None)
    known, _ = pre.parse_known_args(argv)
    merged = build_config_defaults(known.config)

    epilog = (
        "Environment variables (override JSON; CLI overrides env):\n  "
        + "\n  ".join(f"{v} → {k}" for k, v in _ENV_KEYS.items())
    )
    p = argparse.ArgumentParser(
        description="Local mic speech-to-text (Whisper).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog,
    )
    p.add_argument(
        "--config",
        type=Path,
        default=known.config,
        metavar="PATH",
        help=f"Extra JSON config (merged after {GLOBAL_CONFIG} and {REPO_CONFIG.name})",
    )
    p.add_argument(
        "--model",
        default=merged["model"],
        help="Whisper model id (tiny, base, small, medium, large-v3, ...)",
    )
    p.add_argument(
        "--device",
        default=merged["device"],
        choices=("cpu", "cuda"),
        help="Inference device",
    )
    p.add_argument(
        "--compute-type",
        default=merged["compute_type"],
        dest="compute_type",
        help="e.g. int8 (cpu), float16 (cuda)",
    )
    p.add_argument(
        "--chunk-seconds",
        type=float,
        default=merged["chunk_seconds"],
        dest="chunk_seconds",
        help="Audio window per transcription",
    )
    p.add_argument(
        "--language",
        default=merged["language"],
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
        default=merged["input_device"],
        dest="input_device",
        metavar="N",
        help="sounddevice input device index (see --list-devices)",
    )
    p.add_argument(
        "--min-rms",
        type=float,
        default=merged["min_rms"],
        dest="min_rms",
        help="Skip chunks quieter than this RMS",
    )
    p.add_argument(
        "--print-config",
        action="store_true",
        help="Print merged defaults from files + env (not CLI) and exit",
    )
    return p.parse_args(argv)


def list_devices() -> None:
    print(sd.query_devices())


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.print_config:
        merged = build_config_defaults(args.config)
        print("Merged defaults (files + env; CLI overrides these at runtime):", file=sys.stderr)
        for k in (
            "model",
            "device",
            "compute_type",
            "chunk_seconds",
            "language",
            "input_device",
            "min_rms",
        ):
            print(f"  {k}: {merged[k]!r}", file=sys.stderr)
        return
    if args.list_devices:
        list_devices()
        return

    from faster_whisper import WhisperModel

    print("Loading model (first time may download weights)...", file=sys.stderr)
    model = WhisperModel(
        args.model,
        device=args.device,
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
