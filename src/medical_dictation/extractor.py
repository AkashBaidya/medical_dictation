"""Structured clinical summary extraction via the Groq LLM API."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field

from groq import Groq  # type: ignore

logger = logging.getLogger(__name__)

# A modern, fast model available on Groq that handles German text well.
DEFAULT_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """\
You are a medical documentation assistant specialised in German clinical language.
Your task is to analyse a German medical dictation transcript and extract a structured
clinical summary.

Return ONLY a valid JSON object with exactly these keys (all values in German):

{
  "patient_complaint": "Chief complaint / reason for visit (Hauptbeschwerde)",
  "findings": "Clinical findings from examination or diagnostics (Befunde)",
  "diagnosis": "Diagnosis or differential diagnoses (Diagnose)",
  "next_steps": "Recommended next steps, therapies, or follow-up (Weiteres Vorgehen)",
  "transcript_language_detected": "Language detected in the transcript",
  "confidence_note": "Brief note on extraction confidence or any ambiguities"
}

Rules:
- Do NOT include markdown code fences or any text outside the JSON object.
- If a field cannot be determined from the transcript, set its value to null.
- Keep values concise but clinically precise.
- Preserve German medical terminology as-is.
"""

USER_PROMPT_TEMPLATE = """\
Please extract the structured clinical summary from the following German medical \
dictation transcript:

--- TRANSCRIPT START ---
{transcript}
--- TRANSCRIPT END ---
"""


@dataclass
class ClinicalSummary:
    """Structured output of the clinical summary extraction."""

    patient_complaint: str | None
    findings: str | None
    diagnosis: str | None
    next_steps: str | None
    transcript_language_detected: str | None = None
    confidence_note: str | None = None
    raw_transcript: str = field(default="", repr=False)

    def to_dict(self) -> dict:
        return {
            "patient_complaint": self.patient_complaint,
            "findings": self.findings,
            "diagnosis": self.diagnosis,
            "next_steps": self.next_steps,
            "transcript_language_detected": self.transcript_language_detected,
            "confidence_note": self.confidence_note,
        }


class ExtractionError(Exception):
    """Raised when clinical summary extraction fails."""


class ClinicalExtractor:
    """Calls the Groq API to extract a structured summary from a transcript."""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
        self.model = model
        self._client = Groq(api_key=api_key)

    def extract(self, transcript: str) -> ClinicalSummary:
        """Extract a structured clinical summary from *transcript*.

        Args:
            transcript: Raw German medical dictation text.

        Returns:
            A :class:`ClinicalSummary` dataclass instance.

        Raises:
            ExtractionError: If the API call fails or the response cannot be parsed.
        """
        if not transcript.strip():
            raise ValueError("Transcript is empty — nothing to extract.")

        logger.info("Sending transcript to Groq (%s) …", self.model)

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": USER_PROMPT_TEMPLATE.format(transcript=transcript),
                    },
                ],
                temperature=0.1,   # Low temperature for deterministic, factual output
                max_tokens=1024,
            )
        except Exception as exc:
            raise ExtractionError(f"Groq API call failed: {exc}") from exc

        raw_content = response.choices[0].message.content or ""
        logger.debug("Raw LLM response:\n%s", raw_content)

        data = self._parse_json(raw_content)

        return ClinicalSummary(
            patient_complaint=data.get("patient_complaint"),
            findings=data.get("findings"),
            diagnosis=data.get("diagnosis"),
            next_steps=data.get("next_steps"),
            transcript_language_detected=data.get("transcript_language_detected"),
            confidence_note=data.get("confidence_note"),
            raw_transcript=transcript,
        )

    @staticmethod
    def _parse_json(text: str) -> dict:
        """Parse JSON from LLM output, stripping any accidental markdown fences."""
        # Strip optional ```json ... ``` fences the model may add despite instructions
        cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ExtractionError(
                f"LLM returned invalid JSON.\nRaw response:\n{text}\nError: {exc}"
            ) from exc
