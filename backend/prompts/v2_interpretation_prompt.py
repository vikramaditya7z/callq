"""Prompt construction for V2.3 grounded financial interpretation."""

from __future__ import annotations

import json
from typing import Sequence

from backend.models.v2_analysis import (
    Calculation,
    FinancialFact,
    GuidanceFact,
    QualitativeObservation,
)


V2_INTERPRETATION_PROMPT = """
You produce grounded financial interpretation from verified source facts and
Python-generated calculations supplied below.

Use only the supplied facts, evidence excerpts, calculation results, and
calculation status information. Do not use outside knowledge or unstated
assumptions.

Create Bull, Bear, and Watch items only when they are supported. It is valid
to return empty lists. Explain limitations in evidence_gaps when inputs are
missing, unavailable, or incomparable.

Rules:
- Do not calculate, recompute, round, or alter any financial value.
- Do not invent facts, historical comparisons, or unsupported claims.
- Do not override Python calculation results or statuses.
- Do not give investment recommendations, Buy/Hold/Sell labels, price targets,
  valuation opinions, or portfolio advice.
- Every interpretation item must cite at least one supplied fact_id or
  calculation_id and at least one supplied evidence reference.
- Any numeric wording in claim or why_it_matters must cite a supplied valid
  calculation_id. Otherwise express the point without numbers.
- Copy evidence source_id and exact_quote only from the supplied evidence.
- Do not output evidence offsets; Python resolves them from verified evidence.

Return only JSON matching the supplied schema.
""".strip()


def build_v2_interpretation_prompt(
    financial_facts: Sequence[FinancialFact],
    guidance: Sequence[GuidanceFact],
    qualitative_observations: Sequence[QualitativeObservation],
    calculations: Sequence[Calculation],
) -> str:
    """Build a bounded prompt containing only verified V2 inputs."""
    verified_inputs = {
        "financial_facts": [fact.model_dump(mode="json") for fact in financial_facts],
        "guidance": [fact.model_dump(mode="json") for fact in guidance],
        "qualitative_observations": [
            observation.model_dump(mode="json")
            for observation in qualitative_observations
        ],
        "calculations": [calculation.model_dump(mode="json") for calculation in calculations],
    }
    return "{}\n\nVerified inputs:\n{}".format(
        V2_INTERPRETATION_PROMPT,
        json.dumps(verified_inputs, ensure_ascii=False),
    )
