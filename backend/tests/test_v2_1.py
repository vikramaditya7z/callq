"""Focused deterministic tests for the V2.1 contracts and evidence layer."""

from __future__ import annotations

import ast
from pathlib import Path
import unittest
from unittest.mock import patch

from backend.models.v2_analysis import (
    EvidenceRef,
    FinancialFact,
    GuidanceFact,
    QualitativeObservation,
    SourceDocument,
    V2ExtractionResponse,
)
from backend.services.evidence_service import (
    EvidenceValidationError,
    resolve_evidence,
    validate_extraction_evidence,
)
from backend.services.v2_extraction_service import extract_v2_facts


SOURCE_TEXT = (
    "Revenue was $100 million. "
    "Management expects revenue of $110 million next quarter. "
    "Enterprise demand remained strong."
)


class V21EvidenceTests(unittest.TestCase):
    """Evidence validation tests without live Gemini calls."""

    def setUp(self) -> None:
        self.source = SourceDocument(
            source_id="current_q",
            document_type="earnings_call_transcript",
            text=SOURCE_TEXT,
        )

    def test_valid_financial_fact_with_valid_evidence(self) -> None:
        extraction = V2ExtractionResponse(
            financial_facts=[
                FinancialFact(
                    fact_id="revenue_current_q",
                    metric_key="revenue",
                    reported_value="$100 million",
                    unit="USD",
                    period=None,
                    period_type=None,
                    evidence=EvidenceRef(
                        source_id="current_q",
                        exact_quote="Revenue was $100 million.",
                    ),
                )
            ]
        )

        validated = validate_extraction_evidence([self.source], extraction)
        evidence = validated.financial_facts[0].evidence

        self.assertEqual(evidence.start_offset, 0)
        self.assertEqual(evidence.end_offset, len(evidence.exact_quote))

    def test_valid_guidance_with_valid_evidence(self) -> None:
        extraction = V2ExtractionResponse(
            guidance=[
                GuidanceFact(
                    fact_id="revenue_guidance",
                    metric_key="revenue",
                    guidance_value="$110 million",
                    unit="USD",
                    period="next quarter",
                    evidence=EvidenceRef(
                        source_id="current_q",
                        exact_quote="Management expects revenue of $110 million next quarter.",
                    ),
                )
            ]
        )

        validated = validate_extraction_evidence([self.source], extraction)
        self.assertIsNotNone(validated.guidance[0].evidence.start_offset)

    def test_valid_qualitative_observation_with_valid_evidence(self) -> None:
        extraction = V2ExtractionResponse(
            qualitative_observations=[
                QualitativeObservation(
                    observation_id="enterprise_demand",
                    category="demand",
                    statement="Enterprise demand remained strong.",
                    evidence=EvidenceRef(
                        source_id="current_q",
                        exact_quote="Enterprise demand remained strong.",
                    ),
                )
            ]
        )

        validated = validate_extraction_evidence([self.source], extraction)
        self.assertIsNotNone(
            validated.qualitative_observations[0].evidence.start_offset
        )

    def test_invalid_quote_is_rejected(self) -> None:
        evidence = EvidenceRef(
            source_id="current_q",
            exact_quote="Revenue was $200 million.",
        )

        with self.assertRaises(EvidenceValidationError):
            resolve_evidence([self.source], evidence)

    def test_unknown_source_id_is_rejected(self) -> None:
        evidence = EvidenceRef(
            source_id="missing_source",
            exact_quote="Revenue was $100 million.",
        )

        with self.assertRaises(EvidenceValidationError):
            resolve_evidence([self.source], evidence)

    def test_repeated_quote_uses_first_occurrence_and_ignores_offsets(self) -> None:
        source = SourceDocument(
            source_id="repeated",
            document_type="earnings_call_transcript",
            text="Demand improved. Demand improved.",
        )
        evidence = EvidenceRef(
            source_id="repeated",
            exact_quote="Demand improved.",
            start_offset=99,
            end_offset=115,
        )

        resolved = resolve_evidence([source], evidence)

        self.assertEqual(resolved.start_offset, 0)
        self.assertEqual(resolved.end_offset, len("Demand improved."))

    def test_pydantic_serialization_and_deserialization(self) -> None:
        extraction = V2ExtractionResponse(
            financial_facts=[
                FinancialFact(
                    fact_id="revenue_current_q",
                    metric_key="revenue",
                    reported_value="$100 million",
                    unit="USD",
                    period=None,
                    period_type=None,
                    evidence=EvidenceRef(
                        source_id="current_q",
                        exact_quote="Revenue was $100 million.",
                    ),
                )
            ]
        )

        round_tripped = V2ExtractionResponse.model_validate_json(
            extraction.model_dump_json()
        )

        self.assertEqual(round_tripped, extraction)

    def test_extraction_service_resolves_evidence(self) -> None:
        gemini_output = {
            "financial_facts": [
                {
                    "fact_id": "revenue_current_q",
                    "metric_key": "revenue",
                    "reported_value": "$100 million",
                    "unit": "USD",
                    "period": None,
                    "period_type": None,
                    "evidence": {
                        "source_id": "current_q",
                        "exact_quote": "Revenue was $100 million.",
                    },
                }
            ],
            "guidance": [],
            "qualitative_observations": [],
        }

        with patch(
            "backend.services.v2_extraction_service.generate_structured_response",
            return_value=gemini_output,
        ):
            extraction = extract_v2_facts([self.source])

        self.assertEqual(extraction.financial_facts[0].evidence.start_offset, 0)


class Python39CompatibilityTests(unittest.TestCase):
    """Ensure V2.1 source uses syntax accepted by Python 3.9."""

    def test_v21_source_parses_with_python_39_grammar(self) -> None:
        repository_root = Path(__file__).resolve().parents[2]
        v21_files = [
            repository_root / "backend/models/v2_analysis.py",
            repository_root / "backend/services/evidence_service.py",
            repository_root / "backend/services/v2_gemini_schemas.py",
            repository_root / "backend/prompts/v2_extraction_prompt.py",
            repository_root / "backend/services/v2_extraction_service.py",
        ]

        for source_file in v21_files:
            with self.subTest(source_file=source_file):
                ast.parse(
                    source_file.read_text(encoding="utf-8"),
                    filename=str(source_file),
                    feature_version=(3, 9),
                )


if __name__ == "__main__":
    unittest.main()
