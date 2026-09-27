"""V2.3 grounded interpretation pipeline with deterministic reference checks."""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Sequence, Tuple

from pydantic import ValidationError

from backend.models.v2_analysis import (
    Calculation,
    EvidenceGap,
    EvidenceRef,
    FinancialFact,
    GuidanceFact,
    InterpretationItem,
    QualitativeObservation,
    V2InterpretationResponse,
)
from backend.prompts.v2_interpretation_prompt import build_v2_interpretation_prompt
from backend.services.gemini_service import GeminiServiceError, generate_structured_response
from backend.services.v2_interpretation_gemini_schema import (
    V2_INTERPRETATION_RESPONSE_SCHEMA,
)


_NUMERIC_TEXT_PATTERN = re.compile(r"\d")
_PROHIBITED_RECOMMENDATION_PATTERN = re.compile(
    r"\b(buy|sell|hold|price target|investment recommendation|portfolio advice)\b",
    re.IGNORECASE,
)


class InterpretationValidationError(Exception):
    """Raised when interpretation output is not grounded in verified inputs."""


class V2InterpretationServiceError(Exception):
    """Raised when the V2.3 interpretation workflow cannot be trusted."""


def generate_v2_interpretation(
    financial_facts: Sequence[FinancialFact],
    guidance: Sequence[GuidanceFact],
    qualitative_observations: Sequence[QualitativeObservation],
    calculations: Sequence[Calculation],
) -> V2InterpretationResponse:
    """Generate and validate interpretation from bounded verified V2 inputs."""
    prompt = build_v2_interpretation_prompt(
        financial_facts,
        guidance,
        qualitative_observations,
        calculations,
    )
    gemini_output = generate_structured_response(
        prompt,
        V2_INTERPRETATION_RESPONSE_SCHEMA,
    )

    try:
        interpretation = V2InterpretationResponse.model_validate(gemini_output)
    except ValidationError as error:
        raise V2InterpretationServiceError(
            "Gemini output failed V2 interpretation validation."
        ) from error

    try:
        return validate_interpretation_references(
            interpretation,
            financial_facts,
            guidance,
            qualitative_observations,
            calculations,
        )
    except InterpretationValidationError as error:
        raise V2InterpretationServiceError(
            "Gemini output included unsupported interpretation references."
        ) from error


def validate_interpretation_references(
    interpretation: V2InterpretationResponse,
    financial_facts: Sequence[FinancialFact],
    guidance: Sequence[GuidanceFact],
    qualitative_observations: Sequence[QualitativeObservation],
    calculations: Sequence[Calculation],
) -> V2InterpretationResponse:
    """Validate IDs and evidence, returning canonical verified evidence refs."""
    known_fact_ids, evidence_by_key = _verified_input_indexes(
        financial_facts,
        guidance,
        qualitative_observations,
    )
    known_calculation_ids = {calculation.calculation_id for calculation in calculations}
    validated_items = {
        "bull_items": _validate_items(
            interpretation.bull_items,
            known_fact_ids,
            known_calculation_ids,
            evidence_by_key,
        ),
        "bear_items": _validate_items(
            interpretation.bear_items,
            known_fact_ids,
            known_calculation_ids,
            evidence_by_key,
        ),
        "watch_items": _validate_items(
            interpretation.watch_items,
            known_fact_ids,
            known_calculation_ids,
            evidence_by_key,
        ),
    }
    evidence_gaps = _validate_evidence_gaps(
        interpretation.evidence_gaps,
        known_fact_ids,
        known_calculation_ids,
    )

    return interpretation.model_copy(
        update={**validated_items, "evidence_gaps": evidence_gaps}
    )


def _verified_input_indexes(
    financial_facts: Sequence[FinancialFact],
    guidance: Sequence[GuidanceFact],
    qualitative_observations: Sequence[QualitativeObservation],
) -> Tuple[set[str], Dict[Tuple[str, str], EvidenceRef]]:
    known_fact_ids: set[str] = set()
    evidence_by_key: Dict[Tuple[str, str], EvidenceRef] = {}

    for item, item_id in _source_items(
        financial_facts,
        guidance,
        qualitative_observations,
    ):
        if item_id in known_fact_ids:
            raise InterpretationValidationError("Verified input contains duplicate IDs.")
        known_fact_ids.add(item_id)
        evidence = item.evidence
        if evidence.start_offset is None or evidence.end_offset is None:
            raise InterpretationValidationError(
                "Interpretation inputs must contain resolved verified evidence."
            )
        evidence_by_key[(evidence.source_id, evidence.exact_quote)] = evidence

    return known_fact_ids, evidence_by_key


def _source_items(
    financial_facts: Sequence[FinancialFact],
    guidance: Sequence[GuidanceFact],
    qualitative_observations: Sequence[QualitativeObservation],
) -> Iterable[Tuple[object, str]]:
    for fact in financial_facts:
        yield fact, fact.fact_id
    for fact in guidance:
        yield fact, fact.fact_id
    for observation in qualitative_observations:
        yield observation, observation.observation_id


def _validate_items(
    items: Sequence[InterpretationItem],
    known_fact_ids: set[str],
    known_calculation_ids: set[str],
    evidence_by_key: Dict[Tuple[str, str], EvidenceRef],
) -> List[InterpretationItem]:
    return [
        _validate_item(item, known_fact_ids, known_calculation_ids, evidence_by_key)
        for item in items
    ]


def _validate_item(
    item: InterpretationItem,
    known_fact_ids: set[str],
    known_calculation_ids: set[str],
    evidence_by_key: Dict[Tuple[str, str], EvidenceRef],
) -> InterpretationItem:
    if not item.supporting_fact_ids and not item.calculation_ids:
        raise InterpretationValidationError(
            "Interpretation item must reference a fact or calculation."
        )
    _validate_known_ids(item.supporting_fact_ids, known_fact_ids, "fact")
    _validate_known_ids(item.calculation_ids, known_calculation_ids, "calculation")

    combined_text = "{} {}".format(item.claim, item.why_it_matters)
    if _NUMERIC_TEXT_PATTERN.search(combined_text) and not item.calculation_ids:
        raise InterpretationValidationError(
            "Numeric interpretation claims require a calculation reference."
        )
    if _PROHIBITED_RECOMMENDATION_PATTERN.search(combined_text):
        raise InterpretationValidationError(
            "Investment recommendations are not permitted in V2.3 interpretation."
        )

    resolved_evidence = [
        _canonical_evidence(evidence, evidence_by_key) for evidence in item.evidence_refs
    ]
    return item.model_copy(update={"evidence_refs": resolved_evidence})


def _validate_evidence_gaps(
    evidence_gaps: Sequence[EvidenceGap],
    known_fact_ids: set[str],
    known_calculation_ids: set[str],
) -> List[EvidenceGap]:
    for evidence_gap in evidence_gaps:
        _validate_known_ids(evidence_gap.related_fact_ids, known_fact_ids, "fact")
        _validate_known_ids(
            evidence_gap.related_calculation_ids,
            known_calculation_ids,
            "calculation",
        )
    return list(evidence_gaps)


def _validate_known_ids(
    candidate_ids: Sequence[str],
    known_ids: set[str],
    label: str,
) -> None:
    unknown_ids = sorted(set(candidate_ids) - known_ids)
    if unknown_ids:
        raise InterpretationValidationError(
            "Interpretation references unknown {} IDs: {}.".format(
                label,
                ", ".join(unknown_ids),
            )
        )


def _canonical_evidence(
    evidence: EvidenceRef,
    evidence_by_key: Dict[Tuple[str, str], EvidenceRef],
) -> EvidenceRef:
    verified_evidence = evidence_by_key.get((evidence.source_id, evidence.exact_quote))
    if verified_evidence is None:
        raise InterpretationValidationError(
            "Interpretation references evidence that is not in verified inputs."
        )
    return verified_evidence


__all__ = [
    "GeminiServiceError",
    "InterpretationValidationError",
    "V2InterpretationServiceError",
    "generate_v2_interpretation",
    "validate_interpretation_references",
]
