"""Unit tests for the medical dictation pipeline."""

import json
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from medical_dictation.extractor import ClinicalExtractor, ClinicalSummary, ExtractionError
from medical_dictation.transcriber import Transcriber, TranscriptionError


# ── Extractor tests ────────────────────────────────────────────────────────

SAMPLE_JSON = {
    "patient_complaint": "Schmerzen im linken Knie seit drei Wochen",
    "findings": "Schwellung und Druckschmerz im medialen Kompartiment",
    "diagnosis": "Verdacht auf mediale Gonarthrose",
    "next_steps": "Röntgenaufnahme Knie beidseits, Ibuprofen 400mg bei Bedarf",
    "transcript_language_detected": "Deutsch",
    "confidence_note": "Klare Befunde, hohe Konfidenz",
}

SAMPLE_TRANSCRIPT = (
    "Patient klagt über Schmerzen im linken Knie seit drei Wochen. "
    "Befund zeigt Schwellung und Druckschmerz. Diagnose: Verdacht auf Gonarthrose."
)


class TestClinicalExtractor:
    def _make_extractor(self) -> ClinicalExtractor:
        return ClinicalExtractor(api_key="test-key")

    def _mock_response(self, content: str):
        mock_choice = MagicMock()
        mock_choice.message.content = content
        mock_resp = MagicMock()
        mock_resp.choices = [mock_choice]
        return mock_resp

    def test_extract_valid_json(self):
        extractor = self._make_extractor()
        with patch.object(
            extractor._client.chat.completions,
            "create",
            return_value=self._mock_response(json.dumps(SAMPLE_JSON)),
        ):
            summary = extractor.extract(SAMPLE_TRANSCRIPT)

        assert isinstance(summary, ClinicalSummary)
        assert summary.patient_complaint == SAMPLE_JSON["patient_complaint"]
        assert summary.diagnosis == SAMPLE_JSON["diagnosis"]

    def test_extract_strips_markdown_fences(self):
        extractor = self._make_extractor()
        fenced = f"```json\n{json.dumps(SAMPLE_JSON)}\n```"
        with patch.object(
            extractor._client.chat.completions,
            "create",
            return_value=self._mock_response(fenced),
        ):
            summary = extractor.extract(SAMPLE_TRANSCRIPT)
        assert summary.findings == SAMPLE_JSON["findings"]

    def test_extract_raises_on_invalid_json(self):
        extractor = self._make_extractor()
        with patch.object(
            extractor._client.chat.completions,
            "create",
            return_value=self._mock_response("This is not JSON at all."),
        ):
            with pytest.raises(ExtractionError, match="invalid JSON"):
                extractor.extract(SAMPLE_TRANSCRIPT)

    def test_extract_raises_on_empty_transcript(self):
        extractor = self._make_extractor()
        with pytest.raises(ValueError, match="empty"):
            extractor.extract("   ")

    def test_to_dict_has_expected_keys(self):
        summary = ClinicalSummary(
            patient_complaint="x",
            findings="y",
            diagnosis="z",
            next_steps="w",
        )
        d = summary.to_dict()
        assert set(d.keys()) == {
            "patient_complaint",
            "findings",
            "diagnosis",
            "next_steps",
            "transcript_language_detected",
            "confidence_note",
        }


# ── Transcriber tests ──────────────────────────────────────────────────────

class TestTranscriber:
    def test_raises_file_not_found(self):
        t = Transcriber()
        with pytest.raises(FileNotFoundError):
            t.transcribe(Path("/nonexistent/file.wav"))

    def test_raises_on_unsupported_extension(self, tmp_path):
        bad_file = tmp_path / "audio.txt"
        bad_file.write_text("not audio")
        t = Transcriber()
        with pytest.raises(ValueError, match="Unsupported file type"):
            t.transcribe(bad_file)
