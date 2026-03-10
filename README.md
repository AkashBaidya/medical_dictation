# Medical Dictation — German Clinical Summary Extractor

A Python CLI that turns a German medical audio recording into a structured clinical JSON summary.

**Pipeline:**
1. Transcribe audio locally with [OpenAI Whisper](https://github.com/openai/whisper) (German, runs on CPU)
2. Extract structured fields via [Groq](https://console.groq.com) LLM API
3. Output clean JSON

```json
{
  "patient_complaint": "Schmerzen im linken Knie seit drei Wochen",
  "findings": "Schwellung des linken Kniegelenks, Druckschmerz im medialen Kompartiment",
  "diagnosis": "Verdacht auf mediale Gonarthrose links, Grad 2 bis 3",
  "next_steps": "Röntgenaufnahme, Ibuprofen 400mg, Physiotherapie",
  "transcript_language_detected": "Deutsch",
  "confidence_note": "Extraktion mit hoher Sicherheit"
}
```

---

## Project structure

```
medical-dictation/
├── src/medical_dictation/
│   ├── transcriber.py        # Whisper wrapper (German, local, CPU)
│   ├── extractor.py          # Groq LLM → structured JSON
│   └── main.py               # Click CLI entrypoint
├── sample/
│   ├── generate_sample.py    # Generates a 53s test WAV via edge-tts
│   └── dictation_sample.wav  # Pre-generated German dictation (ready to use)
├── tests/
│   └── test_pipeline.py      # Unit tests (fully mocked, no API key needed)
├── pyproject.toml
├── Dockerfile
└── .env.example
```

---

## Prerequisites

| Tool | Purpose | Install |
|------|---------|---------|
| `uv` | Dependency & venv management | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| `ffmpeg` | Audio decoding (required by Whisper) | see below |
| Groq API key | LLM extraction | [console.groq.com](https://console.groq.com) |

### Install ffmpeg

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt-get install ffmpeg

# Windows
winget install Gyan.FFmpeg   # then restart your terminal
```

---

## Local setup (uv)

```bash
# 1. Clone
git clone <your-repo-url>
cd medical-dictation

# 2. Install dependencies (~800 MB first run — PyTorch CPU build)
uv sync

# 3. Set your Groq API key
cp .env.example .env
# Edit .env and set GROQ_API_KEY=your_key_here
```

---

## Generating the sample audio file

A pre-generated 53-second German medical dictation is included at `sample/dictation_sample.wav` — **you can skip this step and use it directly**.

To regenerate it yourself (requires internet for TTS):

```bash
uv run --with edge-tts python sample/generate_sample.py
```

**What it does:**
- Uses Microsoft Edge TTS (`de-DE-KatjaNeural` voice) to synthesise a realistic German medical dictation
- Converts the output to 16 kHz mono WAV — the format Whisper expects
- Overwrites `sample/dictation_sample.wav`

The dictation text covers a knee pain case: patient complaint, clinical findings, diagnosis, and recommended next steps — making it a good end-to-end test for the full pipeline.

---

## Running the pipeline

```bash
# Basic — transcribe and extract
uv run medical-dictation run sample/dictation_sample.wav

# Save the JSON result to a file
uv run medical-dictation run sample/dictation_sample.wav --output result.json

# Use a larger Whisper model for better accuracy
uv run medical-dictation run sample/dictation_sample.wav --model medium

# Transcribe only, skip LLM extraction
uv run medical-dictation run sample/dictation_sample.wav --transcript-only

# All options
uv run medical-dictation run --help
```

---

## Running tests

```bash
uv run --group dev pytest tests/ -v
```

All 7 tests mock Whisper and Groq — no API key or audio file required.

```
tests/test_pipeline.py::TestClinicalExtractor::test_extract_valid_json          PASSED
tests/test_pipeline.py::TestClinicalExtractor::test_extract_strips_markdown_fences PASSED
tests/test_pipeline.py::TestClinicalExtractor::test_extract_raises_on_invalid_json PASSED
tests/test_pipeline.py::TestClinicalExtractor::test_extract_raises_on_empty_transcript PASSED
tests/test_pipeline.py::TestClinicalExtractor::test_to_dict_has_expected_keys   PASSED
tests/test_pipeline.py::TestTranscriber::test_raises_file_not_found             PASSED
tests/test_pipeline.py::TestTranscriber::test_raises_on_unsupported_extension   PASSED
```

---

## Docker setup

### Build

```bash
docker build -t medical-dictation .
```

### Run

```bash
docker run --rm \
  -e GROQ_API_KEY=your_key_here \
  -v "$(pwd)/audio:/audio" \
  medical-dictation run /audio/dictation.wav
```

Replace `$(pwd)/audio` with the directory containing your audio file.

### Save output to a file

```bash
docker run --rm \
  -e GROQ_API_KEY=your_key_here \
  -v "$(pwd)/audio:/audio" \
  -v "$(pwd)/output:/output" \
  medical-dictation run /audio/dictation.wav --output /output/result.json
```

### Cache Whisper model weights (avoids re-download on each run)

```bash
docker run --rm \
  -e GROQ_API_KEY=your_key_here \
  -v "$(pwd)/audio:/audio" \
  -v whisper-cache:/app/.cache \
  medical-dictation run /audio/dictation.wav
```

The named volume `whisper-cache` persists the ~244 MB Whisper `small` model across runs.

---

## CLI reference

```
Usage: medical-dictation run [OPTIONS] AUDIO_FILE

  Transcribe AUDIO_FILE and extract a structured clinical summary.
  AUDIO_FILE must be a WAV or MP3 file containing German medical dictation.

Options:
  --model TEXT       Whisper model size: tiny|base|small|medium|large  [default: small]
  --llm-model TEXT   Groq model for extraction  [default: llama-3.3-70b-versatile]
  --api-key TEXT     Groq API key (falls back to GROQ_API_KEY env var)
  -o, --output PATH  Write JSON result to this file
  --transcript-only  Transcribe only, skip LLM extraction
  -v, --verbose      Enable debug logs
  --help             Show this message and exit
```

---

## Whisper model sizes

| Model | Size | Recommended for |
|-------|------|-----------------|
| `tiny` | 39 MB | Quick tests |
| `base` | 74 MB | Fast machines |
| `small` | 244 MB | **Default — good balance** |
| `medium` | 769 MB | Better accuracy |
| `large-v3` | 1.5 GB | Best accuracy, slow on CPU |

Model weights are downloaded on first run and cached in `~/.cache/whisper`.

---

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | Your Groq API key |
| `XDG_CACHE_HOME` | No | Override cache directory (set automatically in Docker) |

---

## License

MIT
