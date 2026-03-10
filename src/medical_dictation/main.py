"""CLI entrypoint for the German medical dictation pipeline."""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text

from medical_dictation.extractor import ClinicalExtractor, ExtractionError
from medical_dictation.transcriber import TranscriptionError, Transcriber

load_dotenv()

console = Console()


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def _get_api_key(api_key_option: str | None) -> str:
    """Resolve Groq API key from CLI option → env var → error."""
    key = api_key_option or os.getenv("GROQ_API_KEY", "")
    if not key:
        console.print(
            "[bold red]Error:[/] GROQ_API_KEY is not set. "
            "Pass --api-key or set the GROQ_API_KEY environment variable.",
            highlight=False,
        )
        sys.exit(1)
    return key


# ---------------------------------------------------------------------------
# CLI definition
# ---------------------------------------------------------------------------


@click.group()
def cli() -> None:
    """German medical dictation → structured clinical summary (JSON)."""


@cli.command("run")
@click.argument("audio_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--model",
    default="small",
    show_default=True,
    help="Whisper model size (tiny | base | small | medium | large).",
)
@click.option(
    "--llm-model",
    default="llama-3.3-70b-versatile",
    show_default=True,
    help="Groq chat model to use for extraction.",
)
@click.option(
    "--api-key",
    envvar="GROQ_API_KEY",
    default=None,
    help="Groq API key (falls back to GROQ_API_KEY env var).",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Optional path to write the JSON result to a file.",
)
@click.option(
    "--transcript-only",
    is_flag=True,
    default=False,
    help="Only transcribe; skip LLM extraction.",
)
@click.option("--verbose", "-v", is_flag=True, default=False, help="Enable debug logs.")
def run_command(
    audio_file: Path,
    model: str,
    llm_model: str,
    api_key: str | None,
    output: Path | None,
    transcript_only: bool,
    verbose: bool,
) -> None:
    """Transcribe AUDIO_FILE and extract a structured clinical summary.

    AUDIO_FILE must be a WAV or MP3 file containing German medical dictation.

    Example:

    \b
        medical-dictation run dictation.wav
        medical-dictation run dictation.mp3 --model medium --output result.json
    """
    _setup_logging(verbose)

    api_key = _get_api_key(None if transcript_only else api_key)

    # ── Step 1: Transcription ────────────────────────────────────────────────
    console.print()
    console.rule("[bold blue]Step 1 — Transcription[/]")

    transcriber = Transcriber(model_name=model)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(
            f"Transcribing with Whisper [bold]{model}[/] …", total=None
        )
        try:
            transcript = transcriber.transcribe(audio_file)
        except (FileNotFoundError, ValueError, TranscriptionError) as exc:
            progress.stop()
            console.print(f"[bold red]Transcription error:[/] {exc}")
            sys.exit(1)
        finally:
            progress.remove_task(task)

    console.print(
        Panel(
            Text(transcript, overflow="fold"),
            title="[green]Transcript[/]",
            border_style="green",
        )
    )

    if transcript_only:
        console.print("\n[dim]--transcript-only flag set. Skipping LLM extraction.[/]")
        _maybe_write_output({"transcript": transcript}, output)
        return

    # ── Step 2: Clinical extraction ──────────────────────────────────────────
    console.print()
    console.rule("[bold blue]Step 2 — Clinical Summary Extraction[/]")

    extractor = ClinicalExtractor(api_key=api_key, model=llm_model)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(
            f"Extracting summary via [bold]{llm_model}[/] …", total=None
        )
        try:
            summary = extractor.extract(transcript)
        except (ExtractionError, ValueError) as exc:
            progress.stop()
            console.print(f"[bold red]Extraction error:[/] {exc}")
            sys.exit(1)
        finally:
            progress.remove_task(task)

    result = summary.to_dict()

    # ── Output ───────────────────────────────────────────────────────────────
    console.print()
    console.print(
        Panel(
            JSON(json.dumps(result, ensure_ascii=False, indent=2)),
            title="[bold green]Clinical Summary[/]",
            border_style="green",
        )
    )

    _maybe_write_output(result, output)


def _maybe_write_output(data: dict, output_path: Path | None) -> None:
    """Write *data* as JSON to *output_path* if provided."""
    if output_path is None:
        return
    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    console.print(f"\n[dim]Result written to:[/] [bold]{output_path}[/]")


# Allow running as `python -m medical_dictation.main`
if __name__ == "__main__":
    cli()
