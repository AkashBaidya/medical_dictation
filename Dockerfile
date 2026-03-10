# syntax=docker/dockerfile:1
# ── Build stage ───────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy manifests first — Docker cache skips reinstall if they haven't changed
COPY pyproject.toml uv.lock README.md ./
COPY src/ src/

# Install only runtime dependencies (no dev group) into the project venv
RUN uv sync --frozen --no-cache --compile-bytecode --no-group dev

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# ffmpeg is required by Whisper to decode audio files
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the virtual environment and source from the builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

# Put the venv on PATH
ENV PATH="/app/.venv/bin:$PATH"

# Whisper respects XDG_CACHE_HOME for model weight storage.
# Mount a volume here to avoid re-downloading on every container start:
#   docker run -v whisper-cache:/app/.cache ...
ENV XDG_CACHE_HOME="/app/.cache"
RUN mkdir -p /app/.cache/whisper

# Groq API key must be supplied at runtime — never baked into the image
ENV GROQ_API_KEY=""

ENTRYPOINT ["medical-dictation"]
CMD ["--help"]
