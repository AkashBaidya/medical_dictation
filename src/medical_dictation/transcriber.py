"""Audio transcription using OpenAI Whisper with German language support."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".flac"}

# "small" gives a good balance of speed and accuracy for medical German.
# Use "medium" for better accuracy at the cost of ~2x inference time.
DEFAULT_MODEL = "small"


class TranscriptionError(Exception):
    """Raised when audio transcription fails."""


class Transcriber:
    """Wraps Whisper to transcribe German medical audio files."""

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        self.model_name = model_name
        self._model = None  # Lazy-load so startup is fast

    def _load_model(self):
        """Load the Whisper model on first use."""
        if self._model is None:
            import whisper  # type: ignore

            logger.info("Loading Whisper model '%s' …", self.model_name)
            self._model = whisper.load_model(self.model_name)
            logger.info("Model loaded.")
        return self._model

    def transcribe(self, audio_path: Path) -> str:
        """Transcribe *audio_path* and return the German transcript as a string.

        Args:
            audio_path: Path to a WAV or MP3 file.

        Returns:
            The full transcript text.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file extension is not supported.
            TranscriptionError: If Whisper encounters an error.
        """
        audio_path = Path(audio_path)

        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        if audio_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type '{audio_path.suffix}'. "
                f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
            )

        # Whisper uses ffmpeg to decode audio files. Check early and fail with
        # an actionable message instead of a generic WinError from subprocess.
        if shutil.which("ffmpeg") is None:
            raise TranscriptionError(
                "ffmpeg was not found on PATH. Install ffmpeg and restart your terminal. "
                "On Windows, for example: 'winget install Gyan.FFmpeg'."
            )

        model = self._load_model()

        try:
            logger.info("Transcribing '%s' …", audio_path.name)
            result = model.transcribe(
                str(audio_path),
                language="de",  # Force German — avoids mis-detection
                task="transcribe",  # Keep as German, don't translate
                fp16=False,  # fp32 for CPU compatibility
                verbose=False,
            )
        except Exception as exc:
            raise TranscriptionError(f"Whisper transcription failed: {exc}") from exc

        transcript: str = result["text"].strip()
        logger.info("Transcription complete (%d characters).", len(transcript))
        return transcript
