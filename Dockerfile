# syntax=docker/dockerfile:1
# ── Build stage ──────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency manifests first to leverage Docker layer cache
COPY pyproject.toml .
COPY src/ src/

# Install dependencies into a virtual environment inside the image.
# --no-cache keeps the image lean; --compile-bytecode speeds up startup.
RUN uv sync --no-cache --compile-bytecode

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# ffmpeg is required by Whisper to decode MP3 and other audio formats
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the virtual environment and application source from the builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

# Make the venv's binaries available on PATH
ENV PATH="/app/.venv/bin:$PATH"
# Whisper downloads model weights to this directory; mounting a volume here
# avoids re-downloading on every container start.
ENV WHISPER_CACHE_DIR="/app/.cache/whisper"

# Create cache dir and ensure it's writable
RUN mkdir -p /app/.cache/whisper

# The GROQ_API_KEY must be supplied at runtime via --env or an env file.
# We deliberately do NOT bake credentials into the image.
ENV GROQ_API_KEY=""

# Default entrypoint — users pass arguments after `docker run <image>`
ENTRYPOINT ["medical-dictation"]
CMD ["--help"]
