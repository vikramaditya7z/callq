"""Analysis service for the Version 1 backend workflow."""

from __future__ import annotations

from pydantic import ValidationError

from backend.models.analysis import EarningsAnalysisResponse
from backend.prompts.analysis_prompt import build_version_1_analysis_prompt
from backend.services.gemini_schemas import GEMINI_ANALYSIS_RESPONSE_SCHEMA
from backend.services.gemini_service import (
    GeminiServiceError,
    generate_structured_response,
)


def analyze_transcript(transcript: str) -> EarningsAnalysisResponse:
    """Analyze a validated transcript using Gemini structured output."""
    prompt = build_version_1_analysis_prompt(transcript)
    gemini_output = generate_structured_response(
        prompt,
        GEMINI_ANALYSIS_RESPONSE_SCHEMA,
    )

    try:
        return EarningsAnalysisResponse.model_validate(gemini_output)
    except ValidationError as error:
        raise AnalysisServiceError("Gemini output failed response validation.") from error


class AnalysisServiceError(Exception):
    """Raised when analysis workflow output cannot be trusted."""


__all__ = [
    "AnalysisServiceError",
    "GeminiServiceError",
    "analyze_transcript",
]
