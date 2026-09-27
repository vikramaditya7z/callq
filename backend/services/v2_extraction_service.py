"""V2.1 extraction pipeline: Gemini output validated against source evidence."""

from __future__ import annotations

from typing import Sequence

from pydantic import ValidationError

from backend.models.v2_analysis import SourceDocument, V2ExtractionResponse
from backend.prompts.v2_extraction_prompt import build_v2_extraction_prompt
from backend.services.evidence_service import (
    EvidenceValidationError,
    validate_extraction_evidence,
)
from backend.services.gemini_service import GeminiServiceError, generate_structured_response
from backend.services.v2_gemini_schemas import V2_EXTRACTION_RESPONSE_SCHEMA


class V2ExtractionServiceError(Exception):
    """Raised when V2 extraction output cannot be trusted."""


def extract_v2_facts(
    source_documents: Sequence[SourceDocument],
) -> V2ExtractionResponse:
    """Extract V2.1 facts and resolve each exact evidence quote.

    This service is deliberately route-independent so later V2 stages can call
    it directly. It performs no calculations or investment reasoning.
    """
    if not source_documents:
        raise V2ExtractionServiceError("At least one source document is required.")

    prompt = build_v2_extraction_prompt(source_documents)
    gemini_output = generate_structured_response(prompt, V2_EXTRACTION_RESPONSE_SCHEMA)

    try:
        extraction = V2ExtractionResponse.model_validate(gemini_output)
    except ValidationError as error:
        raise V2ExtractionServiceError(
            "Gemini output failed V2 extraction validation."
        ) from error

    try:
        return validate_extraction_evidence(source_documents, extraction)
    except EvidenceValidationError as error:
        raise V2ExtractionServiceError(
            "Gemini output included unverifiable evidence."
        ) from error


__all__ = [
    "GeminiServiceError",
    "V2ExtractionServiceError",
    "extract_v2_facts",
]
