# Medical Dictation Project

## Task
Coding challenge: German medical dictation CLI → structured JSON via Whisper + Groq API.

## Project structure
- `src/medical_dictation/transcriber.py` — Whisper wrapper, forces German, checks ffmpeg on PATH
- `src/medical_dictation/extractor.py` — Groq LLM extraction, returns ClinicalSummary dataclass
- `src/medical_dictation/main.py` — Click CLI (`medical-dictation run <audio_file>`)
- `tests/test_pipeline.py` — unit tests, fully mocked
- `Dockerfile` — multi-stage, installs ffmpeg, mounts whisper cache at `/app/.cache/whisper`
- `sample/dictation_sample.wav` — silent placeholder (3s); use a real recording

## Key decisions
- Whisper `small` model (244MB), fp16=False for CPU compatibility
- Groq model: `llama-3.3-70b-versatile`
- JSON fields: patient_complaint, findings, diagnosis, next_steps, transcript_language_detected, confidence_note
- `dependency-groups.dev` (not deprecated `tool.uv.dev-dependencies`)

## Runtime requirements
- ffmpeg must be on PATH (winget install Gyan.FFmpeg on Windows; restart terminal after)
- GROQ_API_KEY env var required

## Known issues
- Sample WAV is silent — Whisper returns empty transcript → extraction errors
- Must use a real German medical recording for meaningful output
