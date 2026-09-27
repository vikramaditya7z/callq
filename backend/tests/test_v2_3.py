"""Focused deterministic tests for V2.3 grounded interpretation."""

from __future__ import annotations

import ast
from pathlib import Path
import unittest
from unittest.mock import patch

from backend.models.v2_analysis import (
    Calculation,
    EvidenceGap,
    EvidenceRef,
    FinancialFact,
    InterpretationItem,
    QualitativeObservation,
    V2InterpretationResponse,
)
from backend.services.v2_interpretation_service import (
    InterpretationValidationError,
    generate_v2_interpretation,
    validate_interpretation_references,
)


class V23GroundedInterpretationTests(unittest.TestCase):
    """Validate V2.3 references without live Gemini calls."""

    def setUp(self) -> None:
        self.revenue_fact = FinancialFact(
            fact_id="revenue_current",
            metric_key="revenue",
            reported_value="$1.20 billion",
            unit="USD",
            period="Q3 2025",
            period_type="quarterly",
            evidence=EvidenceRef(
                source_id="current_q",
                exact_quote="Revenue was $1.20 billion.",
                start_offset=0,
                end_offset=26,
            ),
        )
        self.observation = QualitativeObservation(
            observation_id="enterprise_demand",
            category="demand",
            statement="Enterprise demand remained strong.",
            evidence=EvidenceRef(
                source_id="current_q",
                exact_quote="Enterprise demand remained strong.",
                start_offset=27,
                end_offset=62,
            ),
        )
        self.calculation = Calculation(
            calculation_id="calc_revenue_growth",
            calculation_type="percentage_change",
            input_fact_ids=["revenue_current", "revenue_previous"],
            formula="((current - previous) / previous) * 100",
            result=18.52,
            unit="percent",
            status="valid",
        )

    def _item(
        self,
        claim: str = "Revenue growth improved.",
        why_it_matters: str = "Higher growth can support operating momentum.",
        fact_ids=None,
        calculation_ids=None,
        evidence_refs=None,
    ) -> InterpretationItem:
        return InterpretationItem(
            claim=claim,
            why_it_matters=why_it_matters,
            supporting_fact_ids=["revenue_current"] if fact_ids is None else fact_ids,
            calculation_ids=["calc_revenue_growth"] if calculation_ids is None else calculation_ids,
            evidence_refs=(
                [
                    EvidenceRef(
                        source_id="current_q",
                        exact_quote="Revenue was $1.20 billion.",
                    )
                ]
                if evidence_refs is None
                else evidence_refs
            ),
        )

    def _validate(self, response: V2InterpretationResponse) -> V2InterpretationResponse:
        return validate_interpretation_references(
            response,
            [self.revenue_fact],
            [],
            [self.observation],
            [self.calculation],
        )

    def test_valid_bull_bear_and_watch_outputs(self) -> None:
        response = V2InterpretationResponse(
            bull_items=[self._item()],
            bear_items=[
                self._item(
                    claim="Execution remains dependent on sustained demand.",
                    why_it_matters="Demand strength can change between reporting periods.",
                    fact_ids=["enterprise_demand"],
                    calculation_ids=[],
                    evidence_refs=[
                        EvidenceRef(
                            source_id="current_q",
                            exact_quote="Enterprise demand remained strong.",
                        )
                    ],
                )
            ],
            watch_items=[self._item()],
            evidence_gaps=[
                EvidenceGap(
                    gap_id="missing_prior_period",
                    description="No comparable prior-period revenue fact was supplied.",
                    related_fact_ids=["revenue_current"],
                    related_calculation_ids=[],
                )
            ],
        )

        validated = self._validate(response)

        self.assertEqual(validated.bull_items[0].evidence_refs[0].start_offset, 0)
        self.assertEqual(validated.bear_items[0].supporting_fact_ids, ["enterprise_demand"])

    def test_unsupported_claim_without_grounding_is_rejected(self) -> None:
        response = V2InterpretationResponse(
            bull_items=[self._item(fact_ids=[], calculation_ids=[])],
        )

        with self.assertRaises(InterpretationValidationError):
            self._validate(response)

    def test_missing_references_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._item(evidence_refs=[])

    def test_numeric_claim_without_calculation_reference_is_rejected(self) -> None:
        response = V2InterpretationResponse(
            bull_items=[
                self._item(
                    claim="Revenue grew 18.52%.",
                    calculation_ids=[],
                )
            ],
        )

        with self.assertRaises(InterpretationValidationError):
            self._validate(response)

    def test_unknown_fact_reference_is_rejected(self) -> None:
        response = V2InterpretationResponse(
            bull_items=[self._item(fact_ids=["missing_fact"])],
        )

        with self.assertRaises(InterpretationValidationError):
            self._validate(response)

    def test_unknown_calculation_reference_is_rejected(self) -> None:
        response = V2InterpretationResponse(
            bull_items=[self._item(calculation_ids=["missing_calculation"])],
        )

        with self.assertRaises(InterpretationValidationError):
            self._validate(response)

    def test_invalid_evidence_reference_is_rejected(self) -> None:
        response = V2InterpretationResponse(
            bull_items=[
                self._item(
                    evidence_refs=[
                        EvidenceRef(
                            source_id="current_q",
                            exact_quote="Unsupported quote.",
                        )
                    ]
                )
            ],
        )

        with self.assertRaises(InterpretationValidationError):
            self._validate(response)

    def test_service_validates_and_resolves_evidence_without_live_gemini(self) -> None:
        gemini_output = {
            "bull_items": [
                {
                    "claim": "Revenue growth improved.",
                    "why_it_matters": "Higher growth can support operating momentum.",
                    "supporting_fact_ids": ["revenue_current"],
                    "calculation_ids": ["calc_revenue_growth"],
                    "evidence_refs": [
                        {
                            "source_id": "current_q",
                            "exact_quote": "Revenue was $1.20 billion.",
                        }
                    ],
                }
            ],
            "bear_items": [],
            "watch_items": [],
            "evidence_gaps": [],
        }

        with patch(
            "backend.services.v2_interpretation_service.generate_structured_response",
            return_value=gemini_output,
        ):
            response = generate_v2_interpretation(
                [self.revenue_fact],
                [],
                [self.observation],
                [self.calculation],
            )

        self.assertEqual(response.bull_items[0].evidence_refs[0].end_offset, 26)


class Python39CompatibilityTests(unittest.TestCase):
    """Ensure V2.3 source uses syntax accepted by Python 3.9."""

    def test_v23_source_parses_with_python_39_grammar(self) -> None:
        repository_root = Path(__file__).resolve().parents[2]
        v23_files = [
            repository_root / "backend/models/v2_analysis.py",
            repository_root / "backend/prompts/v2_interpretation_prompt.py",
            repository_root / "backend/services/v2_interpretation_gemini_schema.py",
            repository_root / "backend/services/v2_interpretation_service.py",
        ]

        for source_file in v23_files:
            with self.subTest(source_file=source_file):
                ast.parse(
                    source_file.read_text(encoding="utf-8"),
                    filename=str(source_file),
                    feature_version=(3, 9),
                )


if __name__ == "__main__":
    unittest.main()
