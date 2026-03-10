# Medical Dictation — German Clinical Summary Extractor

A small Python CLI that:
1. **Transcribes** a German medical audio file (WAV / MP3) using [OpenAI Whisper](https://github.com/openai/whisper) running locally.
2. **Extracts** a structured clinical summary from the transcript via the [Groq](https://console.groq.com) LLM API.
3. **Outputs** a clean JSON object with the following fields:

```json
{
  "patient_complaint": "...",
  "findings":          "...",
  "diagnosis":         "...",
  "next_steps":        "...",
  "transcript_language_detected": "Deutsch",
  "confidence_note":   "..."
}
```

---

## Project structure

```
medical-dictation/
├── src/
│   └── medical_dictation/
│       ├── __init__.py
│       ├── transcriber.py   # Whisper wrapper (German, local)
│       ├── extractor.py     # Groq LLM clinical extraction
│       └── main.py          # Click CLI entrypoint
├── tests/
│   └── test_pipeline.py     # Unit tests (mocked API)
├── pyproject.toml           # uv-compatible project manifest
├── Dockerfile
├── .env.example
└── README.md
```

---

## Prerequisites

| Tool | Purpose | Install |
|------|---------|---------|
| `uv` | Python dependency & venv management | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| `ffmpeg` | Audio decoding (required by Whisper) | see below |
| Groq API key | LLM extraction | [console.groq.com](https://console.groq.com) |

### Install ffmpeg

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt-get install ffmpeg

# Windows (winget)
winget install ffmpeg
```

---

## Local setup (uv)

### 1. Clone and enter the repo

```bash
git clone <your-repo-url>
cd medical-dictation
```

### 2. Create the virtual environment and install dependencies

```bash
uv sync
```

This reads `pyproject.toml`, creates `.venv/`, and installs all dependencies including PyTorch and Whisper.

> **Note on PyTorch size:** The first `uv sync` downloads ~800 MB for PyTorch (CPU build). Subsequent runs are instant.

### 3. Configure your API key

```bash
cp .env.example .env
# Edit .env and set GROQ_API_KEY=your_key_here
```

### 4. Run

```bash
# Activate the venv (optional — uv run works without it)
source .venv/bin/activate

# Basic usage
medical-dictation run path/to/dictation.wav

# Save result to a file
medical-dictation run path/to/dictation.mp3 --output result.json

# Use a larger Whisper model for better accuracy
medical-dictation run dictation.wav --model medium

# Only transcribe, skip LLM extraction
medical-dictation run dictation.wav --transcript-only

# Show all options
medical-dictation run --help
```

Or without activating the venv:

```bash
uv run medical-dictation run path/to/dictation.wav
```

---

## Docker setup

### 1. Build the image

```bash
docker build -t medical-dictation .
```

### 2. Run

```bash
docker run --rm \
  -e GROQ_API_KEY=your_key_here \
  -v "$(pwd)/audio:/audio" \
  medical-dictation run /audio/dictation.wav
```

Replace `$(pwd)/audio` with the directory containing your audio file.

#### Save output to a file

```bash
docker run --rm \
  -e GROQ_API_KEY=your_key_here \
  -v "$(pwd)/audio:/audio" \
  -v "$(pwd)/output:/output" \
  medical-dictation run /audio/dictation.wav --output /output/result.json
```

#### Cache Whisper model weights (avoids re-download)

```bash
docker run --rm \
  -e GROQ_API_KEY=your_key_here \
  -v "$(pwd)/audio:/audio" \
  -v whisper-cache:/app/.cache/whisper \
  medical-dictation run /audio/dictation.wav
```

Using the named volume `whisper-cache` means the model weights (~460 MB for `small`) are only downloaded once.

---

## CLI reference

```
Usage: medical-dictation run [OPTIONS] AUDIO_FILE

  Transcribe AUDIO_FILE and extract a structured clinical summary.

  AUDIO_FILE must be a WAV or MP3 file containing German medical dictation.

Options:
  --model TEXT       Whisper model size (tiny|base|small|medium|large)  [default: small]
  --llm-model TEXT   Groq chat model for extraction  [default: llama-3.3-70b-versatile]
  --api-key TEXT     Groq API key (falls back to GROQ_API_KEY env var)
  -o, --output PATH  Optional path to write JSON result
  --transcript-only  Only transcribe; skip LLM extraction
  -v, --verbose      Enable debug logs
  --help             Show this message and exit
```

---

## Running tests

```bash
uv run pytest tests/ -v
```

Tests mock the Groq API and Whisper, so no API key or GPU is required.

---

## Model notes

| Whisper model | Size | German WER | Recommended for |
|---------------|------|-----------|-----------------|
| `tiny`        | 39 M | ~20%      | Quick tests |
| `base`        | 74 M | ~15%      | Faster machines |
| `small`       | 244 M | ~8%      | **Default — good balance** |
| `medium`      | 769 M | ~5%      | Better accuracy |
| `large-v3`    | 1.5 G | ~4%      | Best accuracy, slow on CPU |

Whisper model weights are downloaded automatically on first run and cached in `~/.cache/whisper` (or `WHISPER_CACHE_DIR` in Docker).

---

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | Your Groq API key |
| `WHISPER_CACHE_DIR` | No | Override Whisper cache directory (Docker: `/app/.cache/whisper`) |

---

## License

MIT
