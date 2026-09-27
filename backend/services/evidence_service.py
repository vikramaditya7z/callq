"""Exact-match evidence validation for V2 extraction results."""

from __future__ import annotations

from typing import Dict, List, Sequence

from backend.models.v2_analysis import (
    EvidenceRef,
    FinancialFact,
    GuidanceFact,
    QualitativeObservation,
    SourceDocument,
    V2ExtractionResponse,
)


class EvidenceValidationError(Exception):
    """Raised when extracted evidence cannot be resolved to a source document."""


def resolve_evidence(
    source_documents: Sequence[SourceDocument],
    evidence: EvidenceRef,
) -> EvidenceRef:
    """Resolve an evidence quote to deterministic offsets in its source text.

    Exact matching is intentionally case- and whitespace-sensitive. When an
    exact quote appears more than once, the first occurrence in source order is
    selected with ``str.find``. Any incoming offsets are ignored and replaced.
    """
    documents_by_id = _index_source_documents(source_documents)
    source_document = documents_by_id.get(evidence.source_id)

    if source_document is None:
        raise EvidenceValidationError(
            "Evidence references an unknown source_id: {}.".format(evidence.source_id)
        )

    start_offset = source_document.text.find(evidence.exact_quote)
    if start_offset < 0:
        raise EvidenceValidationError(
            "Evidence quote was not found in source_id: {}.".format(evidence.source_id)
        )

    return evidence.model_copy(
        update={
            "start_offset": start_offset,
            "end_offset": start_offset + len(evidence.exact_quote),
        }
    )


def validate_extraction_evidence(
    source_documents: Sequence[SourceDocument],
    extraction: V2ExtractionResponse,
) -> V2ExtractionResponse:
    """Return extraction output with every evidence reference resolved."""
    _index_source_documents(source_documents)

    financial_facts: List[FinancialFact] = [
        fact.model_copy(
            update={"evidence": resolve_evidence(source_documents, fact.evidence)}
        )
        for fact in extraction.financial_facts
    ]
    guidance: List[GuidanceFact] = [
        fact.model_copy(
            update={"evidence": resolve_evidence(source_documents, fact.evidence)}
        )
        for fact in extraction.guidance
    ]
    qualitative_observations: List[QualitativeObservation] = [
        observation.model_copy(
            update={"evidence": resolve_evidence(source_documents, observation.evidence)}
        )
        for observation in extraction.qualitative_observations
    ]

    return extraction.model_copy(
        update={
            "financial_facts": financial_facts,
            "guidance": guidance,
            "qualitative_observations": qualitative_observations,
        }
    )


def _index_source_documents(
    source_documents: Sequence[SourceDocument],
) -> Dict[str, SourceDocument]:
    """Index sources and reject ambiguous duplicate source identifiers."""
    documents_by_id: Dict[str, SourceDocument] = {}

    for source_document in source_documents:
        if source_document.source_id in documents_by_id:
            raise EvidenceValidationError(
                "Duplicate source_id is not allowed: {}.".format(
                    source_document.source_id
                )
            )
        documents_by_id[source_document.source_id] = source_document

    return documents_by_id
