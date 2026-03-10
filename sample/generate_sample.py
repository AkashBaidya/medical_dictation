#!/usr/bin/env python3
"""
generate_sample.py — generates a realistic German medical dictation WAV file
using Microsoft Edge TTS (de-DE-KatjaNeural, requires internet access).

Run with:
    uv run --with edge-tts python sample/generate_sample.py

Output:
    sample/dictation_sample.wav  (16 kHz mono PCM — ready for Whisper)
"""

from __future__ import annotations

import asyncio
import shutil
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Sample German medical dictation text
# ---------------------------------------------------------------------------
DICTATION_TEXT = """\
Patient Müller, 58 Jahre, männlich. Vorstellungsgrund: Schmerzen im linken Knie \
seit drei Wochen, zunehmend bei Belastung.

Befund: Mäßige Schwellung des linken Kniegelenks. Druckschmerz im medialen \
Kompartiment. Bewegungseinschränkung bei Flexion auf 90 Grad. Keine ligamentäre \
Instabilität tastbar.

Diagnose: Verdacht auf mediale Gonarthrose links, Grad zwei bis drei.

Weiteres Vorgehen: Röntgenaufnahme des linken Kniegelenks in zwei Ebenen stehend. \
Ibuprofen 400 Milligramm bei Bedarf, maximal dreimal täglich. Physiotherapie zur \
Kräftigung der Oberschenkelmuskulatur verordnet. Wiedervorstellung in vier Wochen \
oder früher bei Beschwerdezunahme.\
"""

VOICE = "de-DE-KatjaNeural"   # High-quality German female voice
OUTPUT = Path(__file__).parent / "dictation_sample.wav"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_edge_tts() -> None:
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        print("edge-tts not found — installing …")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "edge-tts"],
            stdout=subprocess.DEVNULL,
        )
        print("edge-tts installed.")


def _require_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        sys.exit(
            "Error: ffmpeg is not on PATH.\n"
            "  Windows: winget install Gyan.FFmpeg  (then restart your terminal)\n"
            "  macOS:   brew install ffmpeg\n"
            "  Linux:   sudo apt-get install ffmpeg"
        )


async def _generate(text: str, output: Path) -> None:
    import edge_tts

    mp3_path = output.with_suffix(".mp3")

    print(f"Synthesising speech with voice '{VOICE}' …")
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(str(mp3_path))

    print("Converting MP3 -> WAV (16 kHz mono) ...")
    result = subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(mp3_path),
            "-ar", "16000",   # 16 kHz — Whisper's native sample rate
            "-ac", "1",       # mono
            str(output),
        ],
        capture_output=True,
        text=True,
    )
    mp3_path.unlink(missing_ok=True)

    if result.returncode != 0:
        sys.exit(f"ffmpeg conversion failed:\n{result.stderr}")

    duration = _wav_duration(output)
    print(f"\nWritten: {output}  ({duration:.1f}s, 16 kHz mono PCM)")
    print("\nDictation text used:")
    print("-" * 60)
    print(text)
    print("-" * 60)
    print("\nRun the pipeline with:")
    print(f"  uv run medical-dictation run {output}")


def _wav_duration(path: Path) -> float:
    import wave
    with wave.open(str(path)) as wf:
        return wf.getnframes() / wf.getframerate()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    _require_ffmpeg()
    _require_edge_tts()
    asyncio.run(_generate(DICTATION_TEXT, OUTPUT))
