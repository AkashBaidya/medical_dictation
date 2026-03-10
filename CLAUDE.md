# Coding Challenge Task

Build a small Python application (CLI or Streamlit) that:

1. Takes an audio file (WAV or MP3) of a German medical dictation as input
2. Transcribes it using a local speech-to-text model suitable for German medical language (e.g. a small Whisper variant or similar)
3. Sends the transcript to an LLM (local or API) with a prompt to extract a structured clinical summary (patient complaint, findings, diagnosis, next steps) as JSON
4. Outputs the structured JSON result

## Requirements

- Use **uv** for Python dependency management
- Include a **Dockerfile** so the app can be run via `docker build` + `docker run`
- Include a **README** with setup instructions for both local (uv) and Docker usage
- Use **Groq API** for the LLM step

## Implementation

- CLI built with Click (`medical-dictation run <audio_file>`)
- Whisper `small` model for local German transcription
- Groq `llama-3.3-70b-versatile` for clinical JSON extraction
- Structured output: `patient_complaint`, `findings`, `diagnosis`, `next_steps`, `transcript_language_detected`, `confidence_note`

## Key files

- `src/medical_dictation/transcriber.py` — Whisper wrapper (German, local, checks for ffmpeg)
- `src/medical_dictation/extractor.py` — Groq LLM extraction to structured JSON
- `src/medical_dictation/main.py` — Click CLI entrypoint
- `Dockerfile` — multi-stage build with ffmpeg
- `README.md` — local (uv) and Docker setup instructions
- `tests/test_pipeline.py` — unit tests (mocked, no API key required)

## Running

```bash
# Local
uv run medical-dictation run path/to/dictation.wav

# Docker
docker build -t medical-dictation .
docker run --rm -e GROQ_API_KEY=your_key -v "$(pwd)/audio:/audio" medical-dictation run /audio/dictation.wav
```
