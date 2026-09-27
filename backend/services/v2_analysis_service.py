"""End-to-end V2.4 backend orchestration for verified financial analysis."""

from __future__ import annotations

import hashlib
import re
from typing import List, Sequence

from backend.models.v2_analysis import (
    Calculation,
    FinancialFact,
    SourceDocument,
    V2AnalysisRequest,
    V2AnalysisResponse,
    V2Coverage,
)
from backend.services.financial_calculations import (
    calculate_absolute_change,
    calculate_guidance_midpoint,
    calculate_guidance_range_width,
    calculate_margin_change,
    calculate_percentage_change,
)
from backend.services.v2_extraction_service import (
    V2ExtractionServiceError,
    extract_v2_facts,
)
from backend.services.v2_interpretation_service import (
    InterpretationValidationError,
    V2InterpretationServiceError,
    generate_v2_interpretation,
    validate_interpretation_references,
)


CURRENT_SOURCE_ID = "current"


class V2AnalysisServiceError(Exception):
    """Raised when a V2.4 pipeline stage cannot produce a trusted result."""


class V2CalculationPipelineError(V2AnalysisServiceError):
    """Raised when deterministic calculation orchestration unexpectedly fails."""


def run_v2_analysis(request: V2AnalysisRequest) -> V2AnalysisResponse:
    """Run V2.1 extraction, V2.2 calculations, and V2.3 interpretation."""
    source_documents = build_v2_source_documents(request)

    try:
        facts = extract_v2_facts(source_documents)
    except V2ExtractionServiceError as error:
        raise V2AnalysisServiceError("V2 extraction evidence validation failed.") from error

    try:
        calculations = build_v2_calculations(facts.financial_facts, facts.guidance)
    except Exception as error:
        raise V2CalculationPipelineError(
            "V2 deterministic calculation pipeline failed."
        ) from error

    try:
        thesis = generate_v2_interpretation(
            facts.financial_facts,
            facts.guidance,
            facts.qualitative_observations,
            calculations,
        )
        thesis = validate_interpretation_references(
            thesis,
            facts.financial_facts,
            facts.guidance,
            facts.qualitative_observations,
            calculations,
        )
    except (InterpretationValidationError, V2InterpretationServiceError) as error:
        raise V2AnalysisServiceError(
            "V2 interpretation reference validation failed."
        ) from error

    return V2AnalysisResponse(
        source_documents=source_documents,
        facts=facts,
        calculations=calculations,
        thesis=thesis,
        coverage=V2Coverage(
            source_count=len(source_documents),
            financial_fact_count=len(facts.financial_facts),
            guidance_count=len(facts.guidance),
            qualitative_observation_count=len(facts.qualitative_observations),
            valid_calculation_count=sum(
                calculation.status == "valid" for calculation in calculations
            ),
            unavailable_calculation_count=sum(
                calculation.status == "unavailable" for calculation in calculations
            ),
        ),
    )


def build_v2_source_documents(request: V2AnalysisRequest) -> List[SourceDocument]:
    """Assign deterministic source IDs to current and labeled historical inputs."""
    source_documents = [
        SourceDocument(
            source_id=CURRENT_SOURCE_ID,
            document_type="current_earnings_call_transcript",
            text=request.current_transcript,
        )
    ]

    for index, historical_transcript in enumerate(request.historical_transcripts, start=1):
        source_documents.append(
            SourceDocument(
                source_id=_historical_source_id(index, historical_transcript.label),
                document_type="historical_earnings_call_transcript",
                text=historical_transcript.transcript,
            )
        )

    return source_documents


def build_v2_calculations(
    financial_facts: Sequence[FinancialFact],
    guidance,
) -> List[Calculation]:
    """Build deterministic V2.2 calculations from already verified facts only."""
    current_facts = [
        fact for fact in financial_facts if fact.evidence.source_id == CURRENT_SOURCE_ID
    ]
    historical_facts = [
        fact for fact in financial_facts if fact.evidence.source_id != CURRENT_SOURCE_ID
    ]
    calculations: List[Calculation] = []

    for current_fact in current_facts:
        for historical_fact in historical_facts:
            if current_fact.metric_key != historical_fact.metric_key:
                continue
            calculations.extend(
                _comparison_calculations(current_fact, historical_fact)
            )

    for guidance_fact in guidance:
        calculations.extend(
            [
                calculate_guidance_midpoint(
                    _calculation_id("guidance_midpoint", [guidance_fact.fact_id]),
                    guidance_fact,
                ),
                calculate_guidance_range_width(
                    _calculation_id("guidance_range_width", [guidance_fact.fact_id]),
                    guidance_fact,
                ),
            ]
        )

    return calculations


def _comparison_calculations(
    current_fact: FinancialFact,
    historical_fact: FinancialFact,
) -> List[Calculation]:
    """Produce provenance-preserving comparison results for one metric pair."""
    input_fact_ids = [current_fact.fact_id, historical_fact.fact_id]
    calculations = [
        calculate_absolute_change(
            _calculation_id("absolute_change", input_fact_ids),
            current_fact,
            historical_fact,
        ),
        calculate_percentage_change(
            _calculation_id("percentage_change", input_fact_ids),
            current_fact,
            historical_fact,
        ),
    ]
    if current_fact.metric_key.lower().endswith("_margin"):
        calculations.append(
            calculate_margin_change(
                _calculation_id("margin_change", input_fact_ids),
                current_fact,
                historical_fact,
            )
        )
    return calculations


def _historical_source_id(index: int, label: str) -> str:
    """Create stable readable historical source IDs from request order and label."""
    normalized_label = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
    if not normalized_label:
        normalized_label = "transcript"
    return "historical_{}_{}".format(index, normalized_label[:60])


def _calculation_id(calculation_type: str, input_fact_ids: Sequence[str]) -> str:
    """Create stable compact IDs while preserving full provenance in the object."""
    digest = hashlib.sha256("|".join(input_fact_ids).encode("utf-8")).hexdigest()[:12]
    return "calc_{}_{}".format(calculation_type, digest)


__all__ = [
    "CURRENT_SOURCE_ID",
    "V2AnalysisServiceError",
    "V2CalculationPipelineError",
    "build_v2_calculations",
    "build_v2_source_documents",
    "run_v2_analysis",
]
